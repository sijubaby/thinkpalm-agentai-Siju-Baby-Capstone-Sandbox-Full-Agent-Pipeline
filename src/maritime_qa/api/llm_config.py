"""LLM provider configuration (Groq preferred, OpenAI fallback)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from maritime_qa.paths import ENV_FILE, PROJECT_ROOT

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class LlmConfig:
    provider: str
    api_key: str
    base_url: str | None
    model: str

    @property
    def label(self) -> str:
        return f"{self.provider} ({self.model})"


def load_env_file() -> None:
    """Load .env from project root into os.environ (does not override existing vars)."""
    env_path = ENV_FILE
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def resolve_llm_config(preferred: str | None = None) -> LlmConfig | None:
    """
    Resolve LLM settings. Priority:
    1. explicit `preferred` arg (groq | openai)
    2. LLM_PROVIDER env
    3. GROQ_API_KEY if set
    4. OPENAI_API_KEY if set
    """
    load_env_file()
    provider = (preferred or os.getenv("LLM_PROVIDER", "")).strip().lower()

    if provider == "groq" or (not provider and os.getenv("GROQ_API_KEY")):
        key = os.getenv("GROQ_API_KEY", "").strip()
        if key:
            return LlmConfig(
                provider="groq",
                api_key=key,
                base_url=os.getenv("GROQ_BASE_URL", GROQ_BASE_URL).strip() or GROQ_BASE_URL,
                model=os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL).strip() or GROQ_DEFAULT_MODEL,
            )

    if provider == "openai" or os.getenv("OPENAI_API_KEY"):
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if key:
            return LlmConfig(
                provider="openai",
                api_key=key,
                base_url=os.getenv("OPENAI_BASE_URL", "").strip() or None,
                model=os.getenv("OPENAI_MODEL", OPENAI_DEFAULT_MODEL).strip() or OPENAI_DEFAULT_MODEL,
            )

    return None


def is_llm_available(preferred: str | None = None) -> bool:
    return resolve_llm_config(preferred) is not None


def llm_status() -> dict:
    cfg = resolve_llm_config()
    return {
        "llm_configured": cfg is not None,
        "llm_provider": cfg.provider if cfg else None,
        "llm_model": cfg.model if cfg else None,
    }
