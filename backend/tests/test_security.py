"""US-022 security checks — run with:  cd backend && venv/bin/python tests/test_security.py

No pytest needed. Uses a throw-away SQLite DB and never calls the real AI service.
Every fix has a positive proof (legit use still works) and a negative proof (the attack is blocked).
"""
import datetime as dt
import hashlib
import io
import os
import sys
import tempfile
import urllib.request

_tmpdir = tempfile.mkdtemp(prefix="us022_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["SECRET_KEY"] = "us022-test-signing-key-0123456789-abcdefghijklmnop"
for _v in ("ADMIN_PHONE", "ADMIN_PASSWORD", "LLM_API_URL", "LLM_API_KEY", "LLM_PROVIDER", "LLM_MODEL_NAME",
           "LEGACY_SECRET_KEY", "ALLOW_EPHEMERAL_SECRET", "CORS_ORIGINS"):
    os.environ.pop(_v, None)
BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BACKEND)

import jwt  # noqa: E402
from PIL import Image  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import auth, llm_config  # noqa: E402
from app.database import models as dbm  # noqa: E402
from app.models import vlm  # noqa: E402
from app.models.pesticide_matcher import is_banned_substance, match_medicines  # noqa: E402
from app.rate_limit import SlidingWindowLimiter  # noqa: E402
from app.routers import prediction as pred_router  # noqa: E402
from app.main import app  # noqa: E402

PASSED = 0
FAILED = []


def check(name, cond, detail=""):
    global PASSED
    if cond:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL  {name}  {detail}")


def section(title):
    print(f"\n== {title}")


class env:
    """Temporarily set/unset environment variables."""

    def __init__(self, **values):
        self.values = values
        self.saved = {}

    def __enter__(self):
        for k, v in self.values.items():
            self.saved[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def raises(fn, exc=Exception):
    try:
        fn()
    except exc:
        return True
    return False


dbm.init_db()
client = TestClient(app)

# =====================================================================================
section("S2 — SECRET_KEY fail-closed")
with env(SECRET_KEY=None, ALLOW_EPHEMERAL_SECRET=None):
    check("missing SECRET_KEY -> refuse to start", raises(auth._load_secret_key, RuntimeError))
with env(SECRET_KEY="", ALLOW_EPHEMERAL_SECRET=None):
    check("empty SECRET_KEY (compose unset var) -> refuse", raises(auth._load_secret_key, RuntimeError))
with env(SECRET_KEY="plantdoctor-secret-key-change-in-production", ALLOW_EPHEMERAL_SECRET=None):
    check("old public default -> refuse", raises(auth._load_secret_key, RuntimeError))
with env(SECRET_KEY="dev-secret-key", ALLOW_EPHEMERAL_SECRET=None):
    check("old compose default -> refuse", raises(auth._load_secret_key, RuntimeError))
with env(SECRET_KEY=None, ALLOW_EPHEMERAL_SECRET="1"):
    k1, k2 = auth._load_secret_key(), auth._load_secret_key()
    check("ephemeral mode -> random strong key", len(k1) >= 32 and k1 != k2)
with env(SECRET_KEY="a-real-secret-value-that-is-long-enough-123456"):
    check("valid SECRET_KEY accepted", auth._load_secret_key() == "a-real-secret-value-that-is-long-enough-123456")

# =====================================================================================
section("S4 — password hashing (scrypt + legacy upgrade)")
h1, h2 = auth.hash_password("Mat-khau-1"), auth.hash_password("Mat-khau-1")
check("new hash uses scrypt with current params", h1.startswith("scrypt$16384$8$5$"), h1[:30])
check("unique salt per hash", h1 != h2)
check("correct password verifies", auth.verify_password("Mat-khau-1", h1))
check("wrong password rejected", not auth.verify_password("mat-khau-1", h1))
check("new hash does not need rehash", not auth.needs_rehash(h1))
legacy_default = hashlib.sha256(("Old-pass" + "plantdoctor-secret-key-change-in-production").encode()).hexdigest()
legacy_empty = hashlib.sha256("Old-pass".encode()).hexdigest()
legacy_current = hashlib.sha256(("Old-pass" + os.environ["SECRET_KEY"]).encode()).hexdigest()
legacy_unknown = hashlib.sha256(("Old-pass" + "some-other-salt").encode()).hexdigest()
check("legacy hash (old default salt) verifies", auth.verify_password("Old-pass", legacy_default))
check("legacy hash (empty salt) verifies", auth.verify_password("Old-pass", legacy_empty))
check("legacy hash (current SECRET_KEY salt) verifies", auth.verify_password("Old-pass", legacy_current))
check("legacy hash + wrong password rejected", not auth.verify_password("old-pass", legacy_default))
check("legacy hash with unknown salt rejected", not auth.verify_password("Old-pass", legacy_unknown))
with env(LEGACY_SECRET_KEY="some-other-salt"):
    check("LEGACY_SECRET_KEY enables rotated-salt hashes", auth.verify_password("Old-pass", legacy_unknown))
check("legacy hash flagged for rehash", auth.needs_rehash(legacy_default))
check("malformed scrypt hash -> False (no crash)", not auth.verify_password("x", "scrypt$abc$def"))
check("empty hash -> False", not auth.verify_password("x", ""))

# =====================================================================================
section("S2 — JWT validation")
db = dbm.SessionLocal()
normal = dbm.User(phone="0900000101", password_hash=auth.hash_password("Normal-pass-1"), role="user")
admin = dbm.User(phone="0900000102", password_hash=auth.hash_password("Admin-pass-123"), role="admin")
db.add_all([normal, admin])
db.commit()
db.refresh(normal)
db.refresh(admin)
NORMAL_ID, ADMIN_ID = normal.id, admin.id


def me(token):
    return client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code


exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
check("valid token accepted", me(auth.create_token(NORMAL_ID, "user")) == 200)
forged_default = jwt.encode({"user_id": ADMIN_ID, "role": "admin", "exp": exp},
                            "plantdoctor-secret-key-change-in-production", algorithm="HS256")
check("token forged with old default key -> 401", me(forged_default) == 401)
try:
    forged_empty = jwt.encode({"user_id": ADMIN_ID, "role": "admin", "exp": exp}, "", algorithm="HS256")
    check("token forged with empty key -> 401", me(forged_empty) == 401)
except Exception:
    check("token forged with empty key cannot even be created", True)
none_tok = jwt.encode({"user_id": ADMIN_ID, "role": "admin", "exp": exp}, None, algorithm="none")
check("alg=none token -> 401", me(none_tok) == 401)
no_exp = jwt.encode({"user_id": ADMIN_ID, "role": "admin"}, auth.SECRET_KEY, algorithm="HS256")
check("token without exp -> 401", me(no_exp) == 401)
expired = jwt.encode({"user_id": ADMIN_ID, "role": "admin", "exp": dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)},
                     auth.SECRET_KEY, algorithm="HS256")
check("expired token -> 401", me(expired) == 401)
hs512 = jwt.encode({"user_id": ADMIN_ID, "role": "admin", "exp": exp}, auth.SECRET_KEY, algorithm="HS512")
check("other algorithm (HS512) -> 401", me(hs512) == 401)

# =====================================================================================
section("S4 — login upgrades legacy hashes transparently")
legacy_hash = hashlib.sha256(("Legacy-pw-9" + "plantdoctor-secret-key-change-in-production").encode()).hexdigest()
legacy_user = dbm.User(phone="0900000103", password_hash=legacy_hash, role="user")
db.add(legacy_user)
db.commit()
r = client.post("/api/v1/auth/login", json={"phone": "0900000103", "password": "Legacy-pw-9"})
check("legacy user can still log in", r.status_code == 200, r.text[:120])
db.expire_all()
upgraded = db.query(dbm.User).filter(dbm.User.phone == "0900000103").first().password_hash
check("hash upgraded to scrypt after login", upgraded.startswith("scrypt$"), upgraded[:20])
check("login again with upgraded hash", client.post("/api/v1/auth/login", json={"phone": "0900000103", "password": "Legacy-pw-9"}).status_code == 200)
check("wrong password still 401", client.post("/api/v1/auth/login", json={"phone": "0900000103", "password": "legacy-pw-9"}).status_code == 401)

# =====================================================================================
section("S1 — admin bootstrap never resets passwords")
before = db.query(dbm.User).filter(dbm.User.id == ADMIN_ID).first().password_hash
dbm.init_db()
dbm.init_db()
db.expire_all()
after = db.query(dbm.User).filter(dbm.User.id == ADMIN_ID).first().password_hash
check("restart does not change admin password", before == after)
check("no hardcoded admin account is created", db.query(dbm.User).filter(dbm.User.phone == "0944550007").first() is None)
check("old default password does not work for the admin", client.post(
    "/api/v1/auth/login", json={"phone": "0900000102", "password": "Hoa@123"}).status_code == 401)

# A normal user who registers with the old hardcoded admin phone must NOT be promoted on restart
r = client.post("/api/v1/auth/register", json={"phone": "0944550007", "password": "Someone-123"})
check("anyone may register that phone as a normal user", r.status_code == 200, r.text[:100])
dbm.init_db()
db.expire_all()
squatter = db.query(dbm.User).filter(dbm.User.phone == "0944550007").first()
check("restart does NOT promote it to admin", squatter.role == "user", squatter.role)
check("restart does NOT reset its password", auth.verify_password("Someone-123", squatter.password_hash))

with env(ADMIN_PHONE="0900000201", ADMIN_PASSWORD="short"):
    dbm.init_db()
db.expire_all()
check("ADMIN_PASSWORD < 8 chars -> no admin created", db.query(dbm.User).filter(dbm.User.phone == "0900000201").first() is None)
with env(ADMIN_PHONE="0900000202", ADMIN_PASSWORD="Strong-admin-pass"):
    dbm.init_db()
db.expire_all()
created = db.query(dbm.User).filter(dbm.User.phone == "0900000202").first()
check("ADMIN_PHONE + ADMIN_PASSWORD -> admin created", created is not None and created.role == "admin")
check("created admin password verifies", created is not None and auth.verify_password("Strong-admin-pass", created.password_hash))
with env(ADMIN_PHONE="0900000202", ADMIN_PASSWORD="Different-pass-999"):
    dbm.init_db()
db.expire_all()
created = db.query(dbm.User).filter(dbm.User.phone == "0900000202").first()
check("changing ADMIN_PASSWORD later does NOT overwrite", auth.verify_password("Strong-admin-pass", created.password_hash))
with env(ADMIN_PHONE="0900000101", ADMIN_PASSWORD=None):
    dbm.init_db()
db.expire_all()
check("explicit ADMIN_PHONE promotes that existing account", db.query(dbm.User).get(NORMAL_ID).role == "admin")
db.query(dbm.User).get(NORMAL_ID).role = "user"
db.commit()

# =====================================================================================
section("S3 — no hardcoded LLM key/endpoint")
LEAKS = ("ai-teaching-assistant-prod", "152.67.112.145")
leaky = []
for root in (os.path.join(BACKEND, "app"), os.path.join(BACKEND, "..", "frontend", "src"), os.path.join(BACKEND, "..", "mobile", "src")):
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith((".py", ".js", ".jsx")):
                path = os.path.join(dirpath, fn)
                with open(path, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                if any(s in text for s in LEAKS):
                    leaky.append(os.path.relpath(path, BACKEND))
check("no LLM key / proxy IP in backend, web or mobile source", not leaky, leaky)
check("fresh DB without env -> no LLM key seeded", (db.query(dbm.Setting).filter(dbm.Setting.key == "llm_api_key").first() is None))
check("unconfigured LLM -> LLMConfigError (no silent fallback)", raises(lambda: llm_config.resolve_llm_config(db), llm_config.LLMConfigError))

with env(LLM_API_URL="http://cliproxy:8317/v1/chat/completions", LLM_API_KEY="env-key-123"):
    cfg = llm_config.resolve_llm_config(db)
check("env fallback works", cfg["api_key"] == "env-key-123" and cfg["api_url"].startswith("http://cliproxy"))
db.add_all([dbm.Setting(key="llm_api_url", value="http://10.0.0.5:8317/v1/chat/completions"),
            dbm.Setting(key="llm_api_key", value="db-key-456")])
db.commit()
with env(LLM_API_KEY="env-key-123"):
    cfg = llm_config.resolve_llm_config(db)
check("Admin Settings (DB) take precedence over env", cfg["api_key"] == "db-key-456")
check("stored cliproxy key is NOT sent when testing another provider",
      raises(lambda: llm_config.resolve_llm_config(db, {"llm_provider": "openai"}), llm_config.LLMConfigError))
cfg = llm_config.resolve_llm_config(db, {"llm_provider": "openai", "llm_api_key": "sk-typed"})
check("typed key for another provider is used with that provider's URL",
      cfg["api_key"] == "sk-typed" and cfg["api_url"].startswith("https://api.openai.com"))

admin_tok = auth.create_token(ADMIN_ID, "admin")
s = client.get("/api/v1/admin/settings", headers={"Authorization": f"Bearer {admin_tok}"}).json()
check("admin settings return the key masked", "db-key-456" not in str(s) and "•" in s.get("llm_api_key", ""), s.get("llm_api_key"))

# Gemini: the key must travel in a header, never in the URL (URLs end up in logs/error messages)
captured = {}


class _Resp:
    def read(self):
        return b'{"candidates":[{"content":{"parts":[{"text":"{\\"plant\\":\\"Cam\\",\\"disease\\":\\"Khoe manh\\",\\"confidence\\":90}"}]}}]}'


def fake_urlopen(req, timeout=None):
    captured["url"] = req.full_url
    captured["headers"] = {k.lower(): v for k, v in req.header_items()}
    return _Resp()


orig_urlopen = urllib.request.urlopen
urllib.request.urlopen = fake_urlopen
try:
    db.query(dbm.Setting).filter(dbm.Setting.key == "llm_provider").delete()
    db.add(dbm.Setting(key="llm_provider", value="google"))
    db.query(dbm.Setting).filter(dbm.Setting.key == "llm_api_key").first().value = "gemini-secret-key"
    db.commit()
    vlm._call_vlm_once(["aGVsbG8="], "vi", db=db)
finally:
    urllib.request.urlopen = orig_urlopen
check("Gemini key not in URL", "gemini-secret-key" not in captured.get("url", "") and "key=" not in captured.get("url", ""), captured.get("url"))
check("Gemini key sent as x-goog-api-key header", captured.get("headers", {}).get("x-goog-api-key") == "gemini-secret-key")

# =====================================================================================
section("S5 — CORS + security headers")


def cors(origin, method="GET"):
    if method == "OPTIONS":
        return client.options("/api/v1/health", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
    return client.get("/api/v1/health", headers={"Origin": origin})


r = cors("https://evil.example")
check("unknown origin gets no CORS header", "access-control-allow-origin" not in r.headers)
r = cors("https://benhcay.tuaf.edu.vn")
check("production origin allowed", r.headers.get("access-control-allow-origin") == "https://benhcay.tuaf.edu.vn")
check("credentials never allowed cross-origin", "access-control-allow-credentials" not in r.headers)
check("localhost dev origin allowed", cors("http://localhost:3000").headers.get("access-control-allow-origin") == "http://localhost:3000")
check("look-alike origin localhost.evil.com rejected", "access-control-allow-origin" not in cors("http://localhost.evil.com").headers)
check("look-alike origin benhcay.tuaf.edu.vn.evil.com rejected",
      "access-control-allow-origin" not in cors("https://benhcay.tuaf.edu.vn.evil.com").headers)
pre = cors("https://evil.example", "OPTIONS")
check("preflight from unknown origin rejected", "access-control-allow-origin" not in pre.headers)
pre_ok = cors("https://benhcay.tuaf.edu.vn", "OPTIONS")
check("preflight from production origin OK", pre_ok.status_code == 200 and pre_ok.headers.get("access-control-allow-origin"))
h = client.get("/api/v1/health").headers
check("X-Content-Type-Options: nosniff", h.get("x-content-type-options") == "nosniff")
check("X-Frame-Options: DENY", h.get("x-frame-options") == "DENY")
check("auth responses are not cached",
      client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_tok}"}).headers.get("cache-control") == "no-store")

# =====================================================================================
section("S6 — /predict rate limiting")
AI_CALLS = []


def fake_predict_vlm(images, lang="vi", db=None, plant_hint=None):
    AI_CALLS.append(1)
    return vlm._format_result({"plant": "Cam", "disease": "Loét cam", "confidence": 90, "medicines": []}, lang)


pred_router.predict_vlm = fake_predict_vlm
pred_router.guest_limiter = SlidingWindowLimiter(3, 600)
pred_router.user_limiter = SlidingWindowLimiter(2, 600)

buf = io.BytesIO()
Image.new("RGB", (400, 400), (60, 140, 60)).save(buf, "JPEG")
IMG = buf.getvalue()


def predict(ip="198.51.100.7", token=None):
    headers = {"X-Forwarded-For": ip}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post("/api/v1/predict", files={"file": ("a.jpg", IMG, "image/jpeg")}, data={"lang": "vi"}, headers=headers)


codes = [predict().status_code for _ in range(3)]
check("guest: first 3 requests allowed", codes == [200, 200, 200], codes)
blocked = predict()
check("guest: 4th request -> 429", blocked.status_code == 429, blocked.status_code)
check("429 carries Retry-After", blocked.headers.get("retry-after", "").isdigit())
check("429 message is user friendly (vi)", "thử lại" in blocked.json().get("detail", ""))
check("AI was not called for the blocked request", len(AI_CALLS) == 3, len(AI_CALLS))
check("another guest IP has its own bucket", predict(ip="203.0.113.9").status_code == 200)
check("spoofed left-most X-Forwarded-For does not bypass",
      predict(ip="1.2.3.4, 198.51.100.7").status_code == 429)
user_tok = auth.create_token(NORMAL_ID, "user")
codes = [predict(ip=f"192.0.2.{i}", token=user_tok).status_code for i in range(3)]
check("logged-in user limited per account even across IPs", codes == [200, 200, 429], codes)
check("expired/invalid token on /predict = guest, not 401",
      predict(ip="203.0.113.50", token="not-a-jwt").status_code == 200)
r = client.post("/api/v1/predict/clarify", json={"session_token": "unknown-session-0001", "selected_plant": "Cam", "lang": "vi"},
                headers={"X-Forwarded-For": "198.51.100.7"})
check("/predict/clarify shares the same bucket", r.status_code == 429, r.status_code)
r = client.post("/api/v1/predict/clarify", json={"session_token": "unknown-session-0002", "selected_plant": "Cam", "lang": "vi"},
                headers={"X-Forwarded-For": "203.0.113.77"})
check("/predict/clarify under the limit works normally (404 unknown session)", r.status_code == 404, r.status_code)

# Sliding window releases after the window passes
import app.rate_limit as rl  # noqa: E402
now = [1000.0]
orig_mono = rl.time.monotonic
rl.time.monotonic = lambda: now[0]
try:
    lim = SlidingWindowLimiter(2, 60)
    seq = [lim.hit("k"), lim.hit("k"), lim.hit("k")]
    now[0] += 61
    after_window = lim.hit("k")
finally:
    rl.time.monotonic = orig_mono
check("limiter: 3rd hit inside window blocked", seq[0] is None and seq[1] is None and isinstance(seq[2], int), seq)
check("limiter: allowed again after the window", after_window is None)

# =====================================================================================
section("S7 — banned substance matching")
for text in ("Lead arsenate", "Chì (lead)", "DDT 50%", "methyl-parathion", "Methyl Parathion", "Captan 50WP", "Endosulfan"):
    check(f"banned: {text}", is_banned_substance(text))
for text in ("Mancozeb", "Pleadomycin", "Copper hydroxide", "Azoxystrobin", "Leaderine", "Cleadrin 20EC"):
    check(f"not banned: {text}", not is_banned_substance(text))
mm = match_medicines(["Lead arsenate", "Mancozeb"])
check("match_medicines flags only the banned one", mm["banned_warning"] == ["Lead arsenate"], mm["banned_warning"])

db.close()
print(f"\nRESULT: {PASSED} passed, {len(FAILED)} failed")
if FAILED:
    print("FAILED:", FAILED)
    sys.exit(1)
