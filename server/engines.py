from __future__ import annotations
from pathlib import Path
from typing import Any
from PIL import Image
from .config import settings
from .domain_profiles import resolve_profile, capture_plan
from .cross_domain_engine import empty_domain_analysis, normalize_analysis, service_strategy, compose_recommendations, source_reality, preview_contract
from .providers.openai_provider import ProviderUnavailable, vision_context_multi, consultation_reply, visual_qa, image_edit


def local_consultation_reply(text:str, context:dict[str,Any], profile:dict[str,Any]) -> str:
    if not text.strip():
        return "برای شروع، هدف ظاهری، میزان تغییر و اگر Event مشخصی دارید بگویید."
    if not context.get("goal"):
        return "هدفتان را کوتاه بگویید تا Context تصمیم کامل شود."
    return f"Context اولیه برای {profile.get('label','Service')} ثبت شد. ابتدا Evidence و وضعیت فعلی تحلیل می‌شود؛ بعد Recommendation ساخته می‌شود."


def consultation_engine(session:dict[str,Any]) -> dict[str,Any]:
    profile=resolve_profile(session["context"].get("service"))
    return {
        "resolved_profile":profile,
        "goal":session["context"].get("goal",""),
        "participant_context_complete":bool(session["context"].get("style") and session["context"].get("change_level")),
        "capture_plan":capture_plan(profile["profile_key"]),
        "rule":"ANALYSIS_BRIEF_BEFORE_RECOMMENDATION"
    }


def _image_meta(view_paths:dict[str,Path]) -> dict[str,Any]:
    out={}
    for view_id,path in view_paths.items():
        try:
            with Image.open(path) as im:
                out[view_id]={"size":list(im.size),"usable":min(im.size)>=256}
        except Exception:
            out[view_id]={"size":None,"usable":False}
    return out


def context_engine(session:dict[str,Any], view_paths:dict[str,Path]) -> dict[str,Any]:
    profile=resolve_profile(session["context"].get("service"))
    if not view_paths:
        return empty_domain_analysis(profile)
    meta=_image_meta(view_paths)
    local={
        "image_quality":"USABLE" if any(v["usable"] for v in meta.values()) else "LIMITED",
        "view_sufficiency":{
            "accepted_views":[k for k,v in meta.items() if v["usable"]],
            "missing_material_views":[],
            "sufficient_for_analysis":any(v["usable"] for v in meta.values()),
            "sufficient_for_recommendation":any(v["usable"] for v in meta.values()),
            "reason":"Fallback محلی فقط کیفیت/وجود View را تأیید می‌کند؛ Attributeها UNKNOWN می‌مانند."
        },
        "evidence":{"OBSERVED":[],"USER_REPORTED":[],"INFERRED":[],"UNKNOWN":["Detailed visible attributes unavailable in local fallback"],"REQUIRES_PROFESSIONAL_CHECK":[]},
        "domains":{},
        "source_reality_locks":["Preserve identity and unrelated regions.","Do not fabricate current-state attributes not supported by CLIENT_IMAGE evidence."],
        "analysis_brief":{
            "shared_client_summary":["تصاویر دریافت شدند؛ جزئیات تخصصی در fallback محلی به‌صورت UNKNOWN حفظ می‌شوند."],
            "specialist_summary":["Recommendation محافظه‌کار خواهد بود تا Live Analysis در دسترس باشد."],
            "strategy_before_recommendation":service_strategy({"service_profile":profile,"analysis_brief":{}},session["context"])
        },
        "limitations":[],"provider_mode":"LOCAL_METADATA","image_meta":meta
    }
    if settings.openai_api_key and settings.live_text:
        try:
            raw=vision_context_multi(view_paths,session["context"],profile)
            raw["provider_mode"]="LIVE_VISION_MULTI"
            raw["image_meta"]=meta
            return normalize_analysis(raw,profile,list(view_paths.keys()),session["context"])
        except Exception as e:
            local["limitations"].append(f"Live AG-03 unavailable; conservative fallback used: {type(e).__name__}")
    return normalize_analysis(local,profile,list(view_paths.keys()),session["context"])


def safety_engine(session:dict[str,Any]) -> dict[str,Any]:
    profile=resolve_profile(session["context"].get("service"))
    c=session["context"]
    combined=" ".join([c.get("goal",""),c.get("notes",""),*[m.get("text","") for m in session.get("messages",[])[-6:]]]).lower()
    acute=["سوزش شدید","تاول","ورم شدید","خونریزی","زخم باز","عفونت","severe burning","blister","open wound"]
    if any(x in combined for x in acute):
        return {"tier":"S3","state":"STOP","reasons":["گزارش نگرانی فعال خارج از Beauty Optimization عادی."],"professional_checks":["متخصص باید وضعیت را قبل از ادامه بررسی کند."],"service_profile":profile["profile_key"]}
    tier=profile.get("baseline_safety","S0")
    requested=profile.get("requested_canonical_id")
    controlled_exact={
        "SVC-01-006":"S1","CTRL-001":"S1",
        "SVC-01-007":"S2","CTRL-006":"S2",
        "SVC-02-009":"S2","CTRL-005":"S2",
        "SVC-03-005":"S1","CTRL-002":"S1",
        "SVC-03-006":"S1","CTRL-008":"S1",
        "SVC-04-002":"S1","CTRL-010":"S1",
        "SVC-04-007":"S1","CTRL-003":"S1",
        "SVC-05-009":"S1","CTRL-004":"S1",
        "CTRL-007":"S2","CTRL-009":"S1"
    }
    if requested in controlled_exact:tier=controlled_exact[requested]
    if profile["profile_key"]=="bridal_complete":tier="S1"
    checks=[]
    if profile["profile_key"] in {"hair_color","hair_extensions","smoothing"}:
        checks.append("Execution feasibility/history/material compatibility از تصویر به‌تنهایی قابل تأیید نیست.")
    if requested in controlled_exact or profile["profile_key"] in {"bridal_complete","hair_extensions","smoothing"}:
        checks.append("Controlled service requires Specialist Validation before execution-sensitive commitment.")
    # S1 is guided caution, not an automatic professional-check requirement. S2 is CHECK_FIRST.
    state="CHECK_FIRST" if tier=="S2" else "ALLOW"
    return {"tier":tier,"state":state,"reasons":(["Controlled/high-variability service boundary."] if checks else []),"professional_checks":checks,"service_profile":profile["profile_key"],"requested_canonical_id":requested}


def recommendation_engine(session:dict[str,Any]) -> list[dict[str,Any]]:
    return compose_recommendations(session.get("analysis") or {},session["context"],session["safety"])


def _preview_scope_text(profile_key:str,scope:str) -> str:
    if profile_key=="hair_color": return "Change visible hair color direction only; preserve haircut, length, shape, hairline, face and background."
    if profile_key=="makeup": return "Apply only selected makeup domains; preserve facial anatomy, skin identity, hair, clothing and background."
    if profile_key=="nails": return "Modify only requested nail shape/surface/design; preserve hand/finger geometry, skin, jewelry and background."
    if profile_key=="mens_hair_beard": return "Change selected hair styling and groom only facial hair coverage already present; do not invent beard coverage or hair length."
    if profile_key=="hair_extensions": return "Visualize only the requested extension direction; preserve identity and clearly treat it as visualization, not attachment feasibility proof."
    if profile_key=="smoothing": return "Visualize texture/silhouette direction only; preserve identity, length and color unless separately requested."
    if profile_key=="bridal_complete": return "Apply only selected component changes; each component remains bounded and unrelated regions stay unchanged."
    return "Change only the explicitly selected hair/style region; preserve all unrelated regions."


def visual_prompt(session:dict[str,Any],look:dict[str,Any],scope:str,extra:str,retry_correction:str="") -> str:
    analysis=session.get("analysis") or {}; profile=analysis.get("service_profile") or resolve_profile(session["context"].get("service")); contract=preview_contract(analysis,look,scope)
    return f"""
Create a high-integrity ABC DECISION PREVIEW by EDITING the uploaded CLIENT_IMAGE, not by reimagining the client.

ACTIVE SERVICE
{profile.get('label')} / {profile.get('profile_key')}
Canonical IDs: {profile.get('canonical_ids')}

SELECTED CUSTOM DIRECTION
Role: {look.get('role')}
Title: {look.get('title')}
Components: {look.get('components')}
Why: {look.get('why')}

AUTHORITATIVE SOURCE REALITY
{source_reality(analysis)}

PREVIEW CONTRACT
{contract}

EXPLICIT CLIENT CONTEXT
{session.get('context')}

EDIT SCOPE
{_preview_scope_text(profile.get('profile_key',''),scope)}
Additional instruction: {extra or 'none'}

HARD LOCKS
1. Preserve the same person's recognizable identity/current-state evidence as strongly as the runtime allows.
2. Preserve unrelated face/body/hand geometry, pose, expression, clothing, accessories, crop, background and lighting context.
3. No unsolicited beautification, face slimming, eye/nose/jaw reshaping, age shifting, body reshaping or skin glamour treatment.
4. Do not invent hair/beard/nail length, coverage, density, anatomy or hidden feasibility unless an explicit authorized simulation specifically requests that dimension.
5. Color-only preserves cut/length/shape. Makeup preserves facial anatomy. Nail Preview preserves hand/finger geometry. Beard Preview preserves source coverage unless explicit growth simulation exists.
6. If the exact named/reference direction conflicts with source reality, preserve truth and approximate only the evidence-compatible direction.
7. Preview is a decision aid, not proof of safety, feasibility, durability or final result.
8. No text/logo/watermark.

{('RETRY CORRECTION: '+retry_correction) if retry_correction else ''}
Return one edited image only.
""".strip()


def compile_visual_qa(session:dict[str,Any],qa:dict[str,Any],look:dict[str,Any],scope:str) -> dict[str,Any]:
    analysis=session.get("analysis") or {}; profile=(analysis.get("service_profile") or {}).get("profile_key")
    reasons=[]
    if qa.get("requested_change_visible") is not True: reasons.append("requested change not clearly visible")
    if qa.get("identity_continuity")!="GOOD": reasons.append("identity continuity is not GOOD")
    if qa.get("geometry_drift") in {"MINOR","MATERIAL"}: reasons.append(f"geometry drift: {qa.get('geometry_drift')}")
    if qa.get("unrelated_change") in {"MEDIUM","HIGH"}: reasons.append(f"unrelated change: {qa.get('unrelated_change')}")
    if qa.get("source_reality_violation") is True: reasons.append("source reality violation")
    dc=qa.get("domain_checks") or {}
    if profile=="hair_color" and dc.get("hair_geometry_for_color_only") not in {"PRESERVED","NOT_APPLICABLE"}: reasons.append("color-only altered hair geometry")
    if profile=="makeup" and dc.get("face_anatomy_for_makeup") not in {"PRESERVED","NOT_APPLICABLE"}: reasons.append("makeup altered face anatomy")
    if profile=="nails" and dc.get("hand_finger_geometry_for_nails") not in {"PRESERVED","NOT_APPLICABLE"}: reasons.append("nail preview altered hand/finger geometry")
    beard=((analysis.get("domains") or {}).get("beard") or {}).get("coverage","UNKNOWN")
    if beard in {"NONE","STUBBLE","SPARSE","UNKNOWN"} and dc.get("beard_coverage") in {"INCREASED_SLIGHT","INCREASED_MAJOR"}: reasons.append("beard coverage increased beyond source")
    return {**qa,"compiled_result":"PASS" if not reasons else "REJECT","compiled_reasons":reasons}


def run_image_edit(session:dict[str,Any],source_path:Path,look:dict[str,Any],scope:str,extra:str,output_path:Path,retry_correction:str="") -> dict[str,Any]:
    if not settings.openai_api_key or not settings.live_visual: raise ProviderUnavailable("Live visual provider is not configured.")
    return image_edit(source_path,visual_prompt(session,look,scope,extra,retry_correction),output_path)


def run_visual_qa(session:dict[str,Any],source_paths:dict[str,Path],result_path:Path,look:dict[str,Any],scope:str) -> dict[str,Any]:
    if settings.openai_api_key and settings.live_text:
        try:
            contract=preview_contract(session.get("analysis") or {},look,scope)
            raw=visual_qa(source_paths,result_path,look.get("title",""),source_reality(session.get("analysis") or {}),contract)
            return compile_visual_qa(session,raw,look,scope)
        except Exception as e:
            return {"requested_change_visible":None,"identity_continuity":"UNCERTAIN","geometry_drift":"UNCERTAIN","unrelated_change":"UNKNOWN","source_reality_violation":None,"domain_checks":{},"notes":[f"AI Visual QA unavailable: {type(e).__name__}"],"compiled_result":"REJECT","compiled_reasons":["Visual QA unavailable; do not publish preview"]}
    return {"requested_change_visible":None,"identity_continuity":"UNCERTAIN","geometry_drift":"UNCERTAIN","unrelated_change":"UNKNOWN","source_reality_violation":None,"domain_checks":{},"notes":["Live Visual QA is not configured."],"compiled_result":"REJECT","compiled_reasons":["Visual QA unavailable; do not publish preview"]}


def chat_reply(session:dict[str,Any],text:str) -> str:
    profile=resolve_profile(session["context"].get("service"))
    if settings.openai_api_key and settings.live_text:
        try:return consultation_reply(session["messages"],session["context"],profile)
        except Exception:pass
    return local_consultation_reply(text,session["context"],profile)
