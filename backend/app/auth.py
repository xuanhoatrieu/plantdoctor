import base64
import datetime as dt
import hashlib
import hmac
import logging
import os
import secrets
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from .database.models import get_db, User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------- signing secret
# Publicly known values that must never be used to sign tokens (they appeared in old code/compose files).
_KNOWN_INSECURE_SECRETS = {
    "",
    "plantdoctor-secret-key-change-in-production",
    "dev-secret-key",
    "changeme",
    "secret",
}
_MIN_SECRET_LENGTH = 32


def _load_secret_key() -> str:
    """Resolve the JWT signing secret. Fails closed: refuses to start with a missing or public secret.

    For throw-away test/dev sandboxes only, ALLOW_EPHEMERAL_SECRET=1 generates a random per-process key
    (every restart logs everyone out, and it does not work with several workers/instances).
    """
    key = (os.getenv("SECRET_KEY") or "").strip()
    if key and key not in _KNOWN_INSECURE_SECRETS:
        if len(key) < _MIN_SECRET_LENGTH:
            logger.warning(
                "SECRET_KEY is shorter than %d characters. Generate a stronger one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\"",
                _MIN_SECRET_LENGTH,
            )
        return key

    if os.getenv("ALLOW_EPHEMERAL_SECRET") == "1":
        logger.critical(
            "SECRET_KEY is missing or insecure -> using an EPHEMERAL random key (ALLOW_EPHEMERAL_SECRET=1). "
            "Tokens are invalidated on every restart and are not shared between instances. NEVER use in production."
        )
        return secrets.token_urlsafe(48)

    raise RuntimeError(
        "SECRET_KEY chưa được đặt hoặc đang dùng giá trị mặc định công khai. "
        "Hãy đặt biến môi trường SECRET_KEY (tạo bằng: python -c \"import secrets; print(secrets.token_urlsafe(48))\"). "
        "SECRET_KEY is missing or uses a publicly known default value; refusing to start."
    )


SECRET_KEY = _load_secret_key()
JWT_ALGORITHM = "HS256"  # Hardcoded: never derived from the (unverified) token header
TOKEN_LIFETIME = dt.timedelta(days=30)

# ---------------------------------------------------------------- password hashing
# scrypt (memory-hard) from the standard library: no extra dependency in the Docker image.
# Parameters follow an OWASP-listed equivalent: N=2^14, r=8, p=5 (~16 MiB per hash).
_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 5
_SCRYPT_DKLEN = 32
_SCRYPT_SALT_BYTES = 16
_SCRYPT_PREFIX = "scrypt"
_SCRYPT_MAXMEM = 64 * 1024 * 1024


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int, dklen: int) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=dklen, maxmem=_SCRYPT_MAXMEM)


def hash_password(password: str) -> str:
    """Return 'scrypt$N$r$p$salt$hash' with a unique random salt per password."""
    salt = secrets.token_bytes(_SCRYPT_SALT_BYTES)
    digest = _scrypt(password, salt, _SCRYPT_N, _SCRYPT_R, _SCRYPT_P, _SCRYPT_DKLEN)
    return f"{_SCRYPT_PREFIX}${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_b64(salt)}${_b64(digest)}"


def _legacy_salts() -> list:
    """Salts the old sha256(password + SECRET_KEY) scheme may have used on this deployment."""
    candidates = [
        os.getenv("SECRET_KEY") or "",  # raw value (may be empty if compose passed an unset variable)
        os.getenv("LEGACY_SECRET_KEY") or "",  # set this if SECRET_KEY was rotated
        "plantdoctor-secret-key-change-in-production",  # the old in-code default
        "dev-secret-key",  # the old docker-compose.yml default
        "",
    ]
    seen, out = set(), []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _verify_legacy_sha256(password: str, hashed: str) -> bool:
    ok = False
    for salt in _legacy_salts():
        candidate = hashlib.sha256((password + salt).encode()).hexdigest()
        # Check every candidate (no early exit) to keep timing independent of which salt matched
        ok = hmac.compare_digest(candidate, hashed) or ok
    return ok


def is_legacy_hash(hashed: Optional[str]) -> bool:
    return bool(hashed) and not hashed.startswith(_SCRYPT_PREFIX + "$")


def verify_password(password: str, hashed: Optional[str]) -> bool:
    if not hashed or password is None:
        return False
    if hashed.startswith(_SCRYPT_PREFIX + "$"):
        try:
            _, n, r, p, salt_b64, digest_b64 = hashed.split("$")
            expected = _unb64(digest_b64)
            actual = _scrypt(password, _unb64(salt_b64), int(n), int(r), int(p), len(expected))
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            logger.warning("Malformed scrypt password hash encountered")
            return False
    # Legacy unsalted-per-user sha256 hex digest (64 chars)
    if len(hashed) == 64:
        return _verify_legacy_sha256(password, hashed)
    return False


def needs_rehash(hashed: Optional[str]) -> bool:
    """True for legacy hashes or scrypt hashes created with weaker parameters than the current ones."""
    if is_legacy_hash(hashed):
        return True
    try:
        _, n, r, p, _, _ = hashed.split("$")
        return (int(n), int(r), int(p)) != (_SCRYPT_N, _SCRYPT_R, _SCRYPT_P)
    except (ValueError, TypeError, AttributeError):
        return True


# ---------------------------------------------------------------- tokens
def create_token(user_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": dt.datetime.now(dt.timezone.utc) + TOKEN_LIFETIME,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "user_id"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    data = decode_token(token)
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if user and not user.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị tạm khóa")
    return user


def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user, but an expired/invalid token just means 'guest' instead of a 401.

    Used by endpoints that guests may call (predict, feedback): they must never fail only because
    a token stored on a phone has expired.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        data = decode_token(authorization[7:])
    except HTTPException:
        return None
    user = db.query(User).filter(User.id == data.get("user_id")).first()
    if user is None or not user.is_active:
        return None
    return user


async def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    return user


async def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
