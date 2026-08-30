from __future__ import annotations
import json, time, uuid, threading
from pathlib import Path
from typing import Any
from .config import SESSIONS_DIR, MEDIA_DIR, settings

_lock = threading.RLock()
_sessions: dict[str, dict[str, Any]] = {}

ENGINE_ORDER = [
    ("consultation","Consultation Engine"),
    ("context","Context Engine"),
    ("safety_pre","Safety Pre-Gate"),
    ("recommendation","Recommendation Engine"),
    ("visual_preview","Visual Preview Engine"),
    ("visual_qa","Safety & Visual QA"),
    ("validation","Specialist Validation"),
]

def _default_engines():
    return {k:{
        "id":k,"label":label,"state":"PENDING","started_at":None,"finished_at":None,
        "duration_ms":None,"summary":"","detail":{}
    } for k,label in ENGINE_ORDER}

def new_session(salon_name: str, specialist_name: str, client_label: str) -> dict[str,Any]:
    sid = uuid.uuid4().hex[:16]
    now = time.time()
    s = {
        "session_id": sid,
        "created_at": now,
        "updated_at": now,
        "salon_name": salon_name,
        "specialist_name": specialist_name,
        "client_label": client_label,
        "mode": "LIVE" if settings.openai_api_key else "SHOWCASE_FALLBACK",
        "workflow_state": "SPECIALIST_SETUP",
        "turn_state": "AWAITING_INPUT",
        "context": {
            "service":"hair_general","goal":"","occasion":"Everyday","style":"Refined",
            "change_level":"Noticeable","maintenance":"Moderate","exclusions":[],"notes":""
        },
        "messages": [
            {"role":"assistant","text":"سلام! برای شروع، Service و هدف ظاهری مشتری را مشخص کنید؛ ABC ابتدا Evidence را تحلیل می‌کند و بعد Recommendation می‌سازد."}
        ],
        "media": {"source":None,"client_views":{},"preview":None,"preview_history":[],"preview_attempts":[]},
        "analysis": {},
        "analysis_brief_acknowledged": False,
        "safety": {"tier":"S0","state":"ALLOW","reasons":[],"professional_checks":[]},
        "looks": [],
        "explore_enabled": False,
        "selected_look_id": None,
        "service_decision": "UNRESOLVED",
        "specialist_validation": {"status":"NOT_STARTED","notes":""},
        "engines": _default_engines(),
        "task": {"analysis":"IDLE","preview":"IDLE","error":None},
        "audit": [],
    }
    put(s)
    return s

def path_for(sid: str) -> Path:
    return SESSIONS_DIR / f"{sid}.json"

def get(sid: str) -> dict[str,Any]:
    with _lock:
        if sid in _sessions:
            return _sessions[sid]
        p = path_for(sid)
        if p.exists():
            s = json.loads(p.read_text(encoding="utf-8"))
            _sessions[sid] = s
            return s
    raise KeyError(sid)

def put(session: dict[str,Any]) -> None:
    session["updated_at"] = time.time()
    with _lock:
        _sessions[session["session_id"]] = session
        if settings.session_persistence:
            SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
            path_for(session["session_id"]).write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")

def audit(session: dict[str,Any], event: str, **detail) -> None:
    session.setdefault("audit", []).append({"ts":time.time(),"event":event,"detail":detail})
    if len(session["audit"]) > 250:
        session["audit"] = session["audit"][-250:]
    put(session)

def media_dir(sid: str) -> Path:
    p = MEDIA_DIR / sid
    p.mkdir(parents=True, exist_ok=True)
    return p
