from __future__ import annotations
import base64, json, mimetypes, re, urllib.request
from pathlib import Path
from typing import Any
from ..config import settings

class ProviderUnavailable(RuntimeError):
    pass

def _client():
    if not settings.openai_api_key:
        raise ProviderUnavailable("OPENAI_API_KEY is not configured.")
    try:
        from openai import OpenAI
    except Exception as e:
        raise ProviderUnavailable("The OpenAI Python SDK is not installed.") from e
    return OpenAI(api_key=settings.openai_api_key)

def _data_url(path: Path) -> str:
    mime=mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

def _json_from_text(text: str) -> dict[str,Any]:
    text=(text or "").strip()
    if text.startswith("```"):
        text=re.sub(r"^```(?:json)?\s*|\s*```$","",text,flags=re.S)
    try:
        return json.loads(text)
    except Exception:
        m=re.search(r"\{.*\}",text,flags=re.S)
        if m:
            return json.loads(m.group(0))
        raise


def vision_context_multi(view_paths: dict[str,Path], explicit_context: dict[str,Any], service_profile: dict[str,Any]) -> dict[str,Any]:
    """Cross-domain AG-03 multimodal analysis. Multiple views contribute only
    visible evidence; they do not reveal hidden history or professional facts."""
    c=_client()
    prompt=f"""
You are AG-03 Beauty Analysis for ABC, a salon-controlled, specialist-operated Beauty Decision & Visualization System.
This is NOT a men's-barber-only task. The active service profile controls which domains matter.

ACTIVE SERVICE PROFILE
{json.dumps(service_profile, ensure_ascii=False)}

EXPLICIT CLIENT / SPECIALIST CONTEXT
{json.dumps(explicit_context, ensure_ascii=False)}

CLIENT IMAGE RULES
- CLIENT_IMAGE views are authoritative only for visible/current-state evidence.
- Repeated/multiple views improve visibility; they do NOT reveal hidden chemical history, medical state, biology, future growth, product compatibility or execution feasibility.
- Do not identify the person.
- Do not infer ethnicity, religion, culture, personality, sexual orientation, gender identity, health, hormones, medical diagnoses or hidden history.
- Face-shape shorthand and proportions are coarse salon styling observations only, never beauty-value judgments.
- Preserve UNKNOWN when evidence is insufficient.
- Use REQUIRES_PROFESSIONAL_CHECK when a material execution fact cannot be resolved from images/chat.
- Analyze only domains relevant to the active service.

SERVICE-SPECIFIC REALITY RULES
- HAIR: distinguish visible length, texture/pattern, apparent density, volume, silhouette, hairline/growth direction. Do not diagnose hair loss or damage cause.
- COLOR: visible color/lightness/warm-cool direction is lighting-dependent; do not infer formula, exact lift, chemical history or achievable level.
- MAKEUP: describe only makeup-relevant visible geometry/contrast and explicit event/style context. Never diagnose skin.
- NAILS: describe visible nail length/shape/nail-bed/hand proportions. Never diagnose nail disease or material suitability from appearance.
- BEARD: coverage/distribution/moustache/outline are visible evidence only. Do not assume future growth or fabricate density.
- COMBINED LOOK: each component keeps its own evidence, uncertainty and professional-check state.

Return JSON only with this schema. Omit irrelevant domain observations rather than fabricating them:
{{
  "image_quality":"GOOD|USABLE|LIMITED",
  "view_sufficiency":{{
    "accepted_views":["VIEW_ID"],
    "missing_material_views":["VIEW_ID"],
    "sufficient_for_analysis":true,
    "sufficient_for_recommendation":true,
    "reason":"short Persian explanation"
  }},
  "evidence":{{
    "OBSERVED":["concise facts"],
    "USER_REPORTED":["concise facts from explicit context"],
    "INFERRED":["only cautious decision-relevant hypotheses"],
    "UNKNOWN":["material unknowns"],
    "REQUIRES_PROFESSIONAL_CHECK":["execution-sensitive facts"]
  }},
  "domains":{{
    "face":{{"outline":"...","proportions":"...","visible_asymmetry":"..."}},
    "hair":{{"length":"BALD|VERY_SHORT|SHORT|MEDIUM|LONG|VERY_LONG|UNKNOWN","texture":"STRAIGHT|WAVY|CURLY|COILY|UNKNOWN","density":"LOW|MEDIUM|HIGH|UNKNOWN","volume":"LOW|MEDIUM|HIGH|UNKNOWN","silhouette":"...","hairline_growth":"..."}},
    "color":{{"visible_depth":"...","warm_cool_direction":"...","gray_direction":"...","unevenness":"..."}},
    "makeup":{{"visible_contrast":"...","eye_structure":"...","brow_structure":"...","lip_structure":"...","current_makeup_state":"..."}},
    "nails":{{"current_length":"SHORT|MEDIUM|LONG|UNKNOWN","current_shape":"...","nail_bed":"...","hand_proportions":"...","current_design":"..."}},
    "beard":{{"coverage":"NONE|STUBBLE|SPARSE|PARTIAL|MEDIUM|FULL|UNKNOWN","length":"NONE|STUBBLE|SHORT|MEDIUM|LONG|UNKNOWN","distribution":"...","moustache":"NONE|LIGHT|VISIBLE|FULL|UNKNOWN","outline":"..."}},
    "coordination":{{"event_fit_inputs":"...","cross_component_notes":"..."}}
  }},
  "source_reality_locks":["imperative preservation constraints grounded in current visible state"],
  "analysis_brief":{{
    "shared_client_summary":["3-5 concise Persian points suitable for a shared salon screen"],
    "specialist_summary":["up to 8 concise Persian technical/decision notes"],
    "strategy_before_recommendation":["2-5 Persian strategy directions; do not name specific styles unless truly useful"]
  }},
  "limitations":["material limitations only"]
}}
"""
    content=[{"type":"input_text","text":prompt}]
    # Deterministic order: profile-required/known view IDs first by supplied dict insertion.
    for view_id,path in view_paths.items():
        content.append({"type":"input_text","text":f"CLIENT_IMAGE VIEW: {view_id}"})
        content.append({"type":"input_image","image_url":_data_url(path)})
    r=c.responses.create(
        model=settings.text_model,
        reasoning={"effort":settings.text_reasoning},
        input=[{"role":"user","content":content}],
        max_output_tokens=1900,
    )
    return _json_from_text(getattr(r,"output_text",""))


def consultation_reply(history: list[dict[str,str]], context: dict[str,Any], service_profile: dict[str,Any] | None=None) -> str:
    c=_client(); compact=history[-8:]
    prompt=f"""
You are AG-02 Consultation for ABC, a cross-domain beauty consultation product for salons.
Reply in natural Persian for a shared specialist+client screen. Product terms may remain English.
Ask at most ONE decision-useful question at a time. Do not interrogate or add generic filler.
Use the active service profile to prioritize only material inputs (goal, event/context, change magnitude, maintenance, exclusions, target/reference, relevant reported history).
Do not diagnose or infer personality from appearance. Do not claim booking, payment, professional clearance, persistent profile, or image-generation success.
Active service profile: {json.dumps(service_profile or {},ensure_ascii=False)}
Current context: {json.dumps(context,ensure_ascii=False)}
Conversation: {json.dumps(compact,ensure_ascii=False)}
Return only the assistant reply, max 55 Persian words.
"""
    r=c.responses.create(model=settings.text_model,reasoning={"effort":"none"},input=prompt,max_output_tokens=190)
    return (getattr(r,"output_text","") or "").strip()


def visual_qa(source_paths: dict[str,Path], result_path: Path, requested_change: str, source_reality: dict[str,Any], preview_contract: dict[str,Any]) -> dict[str,Any]:
    c=_client()
    prompt=f"""
You are AG-05 Visual Integrity QA for ABC. Compare the Decision Preview against the authoritative CLIENT_IMAGE views.
Do not identify the person. Do not make medical or sensitive-trait claims.

Requested change:
{requested_change}

Authoritative source reality:
{json.dumps(source_reality,ensure_ascii=False)}

Preview contract:
{json.dumps(preview_contract,ensure_ascii=False)}

Hard rules:
- Material identity/face/body/hand geometry drift is a failure.
- Unrequested changes outside authorized beauty regions are failures when material.
- Do not invent hair/beard/nail length, density, coverage, anatomy, or hidden feasibility beyond the explicit request and source evidence.
- Color-only must preserve cut/length/shape.
- Makeup must not reshape facial anatomy or unsolicited skin/face geometry.
- Nails must preserve hand/finger geometry and jewelry unless explicitly changed.
- Beard must not gain coverage/density unless an explicit bounded growth-simulation intent exists.
- Requested change must be visible; unchanged source is not a successful Preview.

Return JSON only:
{{
  "requested_change_visible":true,
  "identity_continuity":"GOOD|UNCERTAIN|POOR",
  "geometry_drift":"NONE|MINOR|MATERIAL",
  "unrelated_change":"LOW|MEDIUM|HIGH",
  "source_reality_violation":false,
  "authorized_region_fidelity":"GOOD|UNCERTAIN|POOR",
  "domain_checks":{{
    "hair_length":"PRESERVED|SHORTER|LONGER_SLIGHT|LONGER_MAJOR|NOT_APPLICABLE|UNCERTAIN",
    "beard_coverage":"PRESERVED|REDUCED|INCREASED_SLIGHT|INCREASED_MAJOR|NOT_APPLICABLE|UNCERTAIN",
    "hair_geometry_for_color_only":"PRESERVED|CHANGED|NOT_APPLICABLE|UNCERTAIN",
    "face_anatomy_for_makeup":"PRESERVED|CHANGED|NOT_APPLICABLE|UNCERTAIN",
    "hand_finger_geometry_for_nails":"PRESERVED|CHANGED|NOT_APPLICABLE|UNCERTAIN"
  }},
  "notes":["short observable notes"]
}}
Be conservative. QA support is not biometric verification or professional feasibility clearance.
"""
    content=[{"type":"input_text","text":prompt}]
    for view_id,path in source_paths.items():
        content.append({"type":"input_text","text":f"SOURCE VIEW {view_id}"})
        content.append({"type":"input_image","image_url":_data_url(path)})
    content.append({"type":"input_text","text":"PREVIEW OUTPUT"})
    content.append({"type":"input_image","image_url":_data_url(result_path)})
    r=c.responses.create(model=settings.text_model,reasoning={"effort":"low"},input=[{"role":"user","content":content}],max_output_tokens=900)
    return _json_from_text(getattr(r,"output_text",""))


def image_edit(source_path: Path, prompt: str, output_path: Path) -> dict[str,Any]:
    c=_client()
    with source_path.open("rb") as f:
        response=c.images.edit(model=settings.image_model,image=f,prompt=prompt,size="1024x1024",quality=settings.image_quality)
    item=response.data[0]; b64=getattr(item,"b64_json",None); url=getattr(item,"url",None)
    if b64:
        output_path.write_bytes(base64.b64decode(b64))
    elif url:
        urllib.request.urlretrieve(url,output_path)
    else:
        raise RuntimeError("Image provider returned no image payload.")
    return {"provider":"openai","model":settings.image_model,"quality":settings.image_quality,"output_file":output_path.name}
