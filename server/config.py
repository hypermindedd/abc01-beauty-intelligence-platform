from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
MEDIA_DIR = DATA_DIR / "media"
STATIC_DIR = ROOT / "static"

def _load_env_local() -> None:
    p = ROOT / ".env.local"
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

_load_env_local()

@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    text_model: str = os.getenv("ABC_TEXT_MODEL", "gpt-5.6-terra").strip()
    image_model: str = os.getenv("ABC_IMAGE_MODEL", "gpt-image-2").strip()
    text_reasoning: str = os.getenv("ABC_TEXT_REASONING", "low").strip()
    image_quality: str = os.getenv("ABC_IMAGE_QUALITY", "high").strip()
    live_text: bool = os.getenv("ABC_LIVE_TEXT", "1").strip() not in {"0","false","False"}
    live_visual: bool = os.getenv("ABC_LIVE_VISUAL", "1").strip() not in {"0","false","False"}
    max_upload_mb: int = int(os.getenv("ABC_MAX_UPLOAD_MB", "15"))
    session_persistence: bool = os.getenv("ABC_SESSION_PERSISTENCE", "1").strip() not in {"0","false","False"}
    visual_max_attempts: int = max(1, min(3, int(os.getenv("ABC_VISUAL_MAX_ATTEMPTS", "2"))))

settings = Settings()
