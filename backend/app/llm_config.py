"""Single source of truth for the LLM connection settings.

Resolution order for each field: Admin Settings (database) -> environment variable -> non-secret default.
Secrets (API key) and the private endpoint URL are NEVER hardcoded here.

Environment variables:
    LLM_PROVIDER    cliproxy | openai | google      (default: cliproxy)
    LLM_API_URL     chat-completions URL            (required for cliproxy unless set in Admin Settings)
    LLM_API_KEY     API key                         (required unless set in Admin Settings)
    LLM_MODEL_NAME  model name                      (default depends on provider)
"""
import ipaddress
import logging
import os
from typing import Optional
from urllib.parse import urlparse

from .database.models import Setting

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ("cliproxy", "openai", "google")
_DEFAULT_MODELS = {"cliproxy": "gemini-3.8-flash-high", "openai": "gpt-4o", "google": "gemini-1.5-flash"}
_DEFAULT_URLS = {"openai": "https://api.openai.com/v1/chat/completions"}
_warned_plain_http = set()


class LLMConfigError(RuntimeError):
    """Raised when the LLM connection is not configured. The message never contains the key."""


def _db_value(db, key: str) -> str:
    if db is None:
        return ""
    row = db.query(Setting).filter(Setting.key == key).first()
    return (row.value or "").strip() if row is not None else ""


def _first(*values: Optional[str]) -> str:
    for v in values:
        if v and str(v).strip():
            return str(v).strip()
    return ""


def _is_private_host(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback
    except ValueError:
        pass
    # "localhost" or a single-label name such as a Docker service ("cliproxy") stays on the internal network
    return host == "localhost" or (bool(host) and "." not in host)


def _warn_if_plain_http(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme == "http" and not _is_private_host(parsed.hostname or ""):
        if url not in _warned_plain_http:
            _warned_plain_http.add(url)
            # TODO(security): the LLM endpoint is reached over plain HTTP on a public address, so the API key
            # and user photos travel unencrypted. Put the proxy behind HTTPS or on the internal Docker network.
            logger.warning("LLM endpoint uses plain HTTP on a public address (%s://%s). Use HTTPS or an internal network.",
                           parsed.scheme, parsed.hostname)


def resolve_llm_config(db=None, overrides: Optional[dict] = None) -> dict:
    """Return {'provider', 'api_url', 'api_key', 'model_name'} or raise LLMConfigError.

    `overrides` (e.g. values typed in the Admin 'test connection' form) take precedence when non-empty.
    """
    o = overrides or {}
    stored_provider = _first(_db_value(db, "llm_provider"), os.getenv("LLM_PROVIDER"), "cliproxy").lower()
    provider = _first(o.get("llm_provider"), stored_provider).lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise LLMConfigError(f"Unsupported LLM provider: {provider}")

    # Stored URL/key/model belong to the stored provider: never send e.g. an OpenAI key to the cliproxy URL
    # when an admin is testing a different provider in the settings form.
    same = provider == stored_provider

    def stored(key: str, env: str) -> str:
        return _first(_db_value(db, key), os.getenv(env)) if same else ""

    api_url = _first(o.get("llm_api_url"), stored("llm_api_url", "LLM_API_URL"), _DEFAULT_URLS.get(provider))
    api_key = _first(o.get("llm_api_key"), stored("llm_api_key", "LLM_API_KEY"))
    model_name = _first(o.get("llm_model_name"), stored("llm_model_name", "LLM_MODEL_NAME"), _DEFAULT_MODELS[provider])

    if provider in ("cliproxy", "openai") and not api_url:
        raise LLMConfigError("LLM API URL is not configured (Admin > Settings or env LLM_API_URL)")
    if not api_key:
        raise LLMConfigError("LLM API key is not configured (Admin > Settings or env LLM_API_KEY)")
    if api_url:
        _warn_if_plain_http(api_url)

    return {"provider": provider, "api_url": api_url, "api_key": api_key, "model_name": model_name}


def env_seed_settings() -> dict:
    """LLM settings to seed into an EMPTY settings table on first start (only from the environment)."""
    seed = {
        "llm_provider": _first(os.getenv("LLM_PROVIDER"), "cliproxy"),
        "llm_model_name": _first(os.getenv("LLM_MODEL_NAME"), _DEFAULT_MODELS["cliproxy"]),
    }
    if os.getenv("LLM_API_URL"):
        seed["llm_api_url"] = os.getenv("LLM_API_URL").strip()
    if os.getenv("LLM_API_KEY"):
        seed["llm_api_key"] = os.getenv("LLM_API_KEY").strip()
    return seed
