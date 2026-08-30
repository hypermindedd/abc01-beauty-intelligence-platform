from __future__ import annotations
from typing import Any
from .domain_profiles import resolve_profile, capture_plan
from .direction_catalog import HAIR_COMPONENTS,COLOR_COMPONENTS,MAKEUP_COMPONENTS,NAIL_COMPONENTS,BEARD_COMPONENTS

CHANGE_ORDER={"Subtle":0,"Noticeable":1,"Statement":2}
MAINT_ORDER={"Low":0,"Low–Moderate":1,"Moderate":2,"High":3}
BEARD_LEVEL={"NONE":0,"STUBBLE":1,"SPARSE":2,"PARTIAL":3,"MEDIUM":4,"FULL":5,"UNKNOWN":0}


def empty_domain_analysis(profile: dict[str,Any]) -> dict[str,Any]:
    return {
        "image_quality":"MISSING",
        "view_sufficiency":{"accepted_views":[],"missing_material_views":list(profile.get("minimum_views",[])),"sufficient_for_analysis":False,"sufficient_for_recommendation":False,"reason":"تصویر کافی دریافت نشده است."},
        "evidence":{"OBSERVED":[],"USER_REPORTED":[],"INFERRED":[],"UNKNOWN":["Visible client state"],"REQUIRES_PROFESSIONAL_CHECK":[]},
        "domains":{},
        "source_reality_locks":["Do not fabricate current-state attributes before CLIENT_IMAGE evidence exists."],
        "analysis_brief":{"shared_client_summary":["برای تحلیل دقیق‌تر، حداقل تصاویر لازم این Service باید دریافت شود."],"specialist_summary":[],"strategy_before_recommendation":[]},
        "limitations":["CLIENT_IMAGE evidence incomplete."],
        "service_profile":profile,
    }


def normalize_analysis(raw: dict[str,Any], profile: dict[str,Any], supplied_views: list[str], explicit_context: dict[str,Any]) -> dict[str,Any]:
    raw=raw or {}
    raw.setdefault("image_quality","LIMITED")
    raw.setdefault("view_sufficiency",{})
    vs=raw["view_sufficiency"]
    accepted=list(dict.fromkeys(vs.get("accepted_views") or supplied_views))
    vs["accepted_views"]=accepted
    required=list(profile.get("minimum_views",[]))
    missing_required=[v for v in required if v not in accepted]
    provider_missing=list(vs.get("missing_material_views") or [])
    vs["missing_material_views"]=list(dict.fromkeys(missing_required+provider_missing))
    vs["sufficient_for_analysis"]=bool(accepted)
    # Engine-level professional gate: ranked recommendation requires the service-specific
    # minimum evidence view set. Conditional views remain adaptive and are requested only
    # when a material gap remains.
    vs["sufficient_for_recommendation"]=bool(accepted) and not missing_required and bool(vs.get("sufficient_for_recommendation",True))
    if missing_required:
        vs["reason"]="Minimum professional capture set incomplete: "+", ".join(missing_required)
    else:
        vs.setdefault("reason","")
    raw.setdefault("evidence",{})
    for k in ["OBSERVED","USER_REPORTED","INFERRED","UNKNOWN","REQUIRES_PROFESSIONAL_CHECK"]:
        raw["evidence"].setdefault(k,[])
    if explicit_context.get("goal"):
        fact=f"Goal: {explicit_context['goal']}"
        if fact not in raw["evidence"]["USER_REPORTED"]: raw["evidence"]["USER_REPORTED"].append(fact)
    raw.setdefault("domains",{})
    raw.setdefault("source_reality_locks",[])
    raw.setdefault("analysis_brief",{})
    raw["analysis_brief"].setdefault("shared_client_summary",[])
    raw["analysis_brief"].setdefault("specialist_summary",[])
    raw["analysis_brief"].setdefault("strategy_before_recommendation",[])
    raw.setdefault("limitations",[])
    raw["service_profile"]=profile
    raw["capture_plan"]=capture_plan(profile["profile_key"])
    raw["analysis_ready_before_recommendation"]=bool(vs.get("sufficient_for_recommendation") and raw["analysis_brief"]["shared_client_summary"])
    # Compatibility projection for existing salon-edition UIs. Core truth remains in domains/evidence/analysis_brief.
    hair=(raw.get("domains") or {}).get("hair") or {}
    beard=(raw.get("domains") or {}).get("beard") or {}
    raw["visible"]={
        "hair_length":hair.get("length","UNKNOWN"),"hair_texture":hair.get("texture","UNKNOWN"),"hair_density":hair.get("density","UNKNOWN"),
        "beard_coverage":beard.get("coverage","UNKNOWN"),"beard_length":beard.get("length","UNKNOWN"),"moustache_presence":beard.get("moustache","UNKNOWN")
    }
    raw["shared_summary"]=list(raw["analysis_brief"]["shared_client_summary"])
    raw["specialist_notes"]=list(raw["analysis_brief"]["specialist_summary"])
    return raw


def service_strategy(analysis: dict[str,Any], context: dict[str,Any]) -> list[str]:
    profile=analysis.get("service_profile") or resolve_profile(context.get("service"))
    existing=(analysis.get("analysis_brief") or {}).get("strategy_before_recommendation") or []
    if existing:
        return existing[:5]
    key=profile["profile_key"]
    if key=="hair_general": return ["فرم فعلی مو حفظ شود و تغییر روی silhouette/texture موردنیاز متمرکز بماند.","Direction باید با Maintenance انتخابی مشتری سازگار بماند."]
    if key=="hair_color": return ["ابتدا Color Direction بصری انتخاب شود؛ feasibility شیمیایی جداگانه نزد متخصص باقی می‌ماند.","در Preview رنگ، طول/فرم/کات مو ثابت می‌ماند."]
    if key=="makeup": return ["تمرکز روی requested makeup domains باشد؛ آناتومی صورت و skin identity تغییر نکند.","Event/lighting context در شدت و contrast پیشنهاد اثر بگذارد."]
    if key=="nails": return ["Direction بر اساس طول/فرم فعلی، هدف و Maintenance ساخته شود.","هندسه دست و انگشتان ثابت بماند؛ Extension فقط در مسیر controlled معتبر وارد شود."]
    if key=="mens_hair_beard": return ["Hair و Beard جداگانه از Source Reality تحلیل و سپس هماهنگ شوند.","هیچ Beard density یا Hair length خارج از شواهد فعلی اختراع نشود."]
    if key=="bridal_complete": return ["Complete Look یک coordination object است؛ هر component باید owner/safety/feasibility خودش را حفظ کند.","Event coherence بدون پوشاندن unknownها یا professional checks ساخته شود."]
    return ["Recommendation فقط از evidence-compatible directionها ساخته شود."]


def _pick_components(pool:list[dict[str,Any]], context:dict[str,Any], count:int=3) -> list[dict[str,Any]]:
    desired=CHANGE_ORDER.get(context.get("change_level","Noticeable"),1)
    maint=MAINT_ORDER.get(context.get("maintenance","Moderate"),2)
    style=(context.get("style") or "").lower(); occasion=(context.get("occasion") or "").lower()
    def key(x):
        tags=set(t.lower() for t in x.get("tags",[]))
        return (
            MAINT_ORDER.get(x.get("maintenance","Moderate"),2)<=maint,
            CHANGE_ORDER.get(x.get("change","Noticeable"),1)==desired,
            style in tags or any(style in t for t in tags) if style else False,
            occasion in tags or any(occasion in t for t in tags) if occasion else False,
        )
    return sorted(pool,key=key,reverse=True)[:count]


def _beard_component(analysis:dict[str,Any], role:str) -> dict[str,Any] | None:
    beard=(analysis.get("domains") or {}).get("beard") or {}
    coverage=beard.get("coverage","UNKNOWN")
    level=BEARD_LEVEL.get(coverage,0)
    eligible=[b for b in BEARD_COMPONENTS if BEARD_LEVEL.get(b["min_coverage"],0)<=level]
    if not eligible: return None
    if role=="BOLDER": return eligible[-1]
    if role=="ALTERNATIVE": return eligible[0]
    return eligible[min(1,len(eligible)-1)]


def _common_look(lid:str,role:str,title:str,components:list[dict[str,Any]],why:str,tradeoff:str,profile:dict[str,Any],analysis:dict[str,Any],context:dict[str,Any]) -> dict[str,Any]:
    return {
        "id":lid,"role":role,"title":title,"custom_composition":True,
        "components":components,
        "why":why,"tradeoff":tradeoff,
        "service_profile":profile["profile_key"],"canonical_service_ids":profile.get("canonical_ids",[]),"knowledge_owners":profile.get("knowledge_owners",[]),
        "maintenance":context.get("maintenance","Moderate"),"change":context.get("change_level","Noticeable"),
        "source_reality_constraints":analysis.get("source_reality_locks",[]),
        "professional_checks":analysis.get("evidence",{}).get("REQUIRES_PROFESSIONAL_CHECK",[]),
        "preview_eligible":True,"is_explore":role.startswith("EXPLORE"),
        # Existing edition UI compatibility; these are presentation aliases, not canonical engine truth.
        "hair_style_name": next((c.get("name") for c in components if c.get("domain")=="hair"), title),
        "beard_style_name": next((c.get("name") for c in components if c.get("domain")=="beard"), "Unchanged / not applicable"),
        "source_beard_coverage": ((analysis.get("domains") or {}).get("beard") or {}).get("coverage","UNKNOWN"),
        "trend":"CUSTOM_COMPOSITION",
        "reality_constraints":analysis.get("source_reality_locks",[]),
    }


def compose_recommendations(analysis:dict[str,Any],context:dict[str,Any],safety:dict[str,Any]) -> list[dict[str,Any]]:
    profile=analysis.get("service_profile") or resolve_profile(context.get("service"))
    if profile["profile_key"]=="unsupported" or safety.get("state")=="STOP": return []
    if not analysis.get("analysis_ready_before_recommendation"):
        return []
    key=profile["profile_key"]
    roles=[("A","BEST FIT"),("B","ALTERNATIVE"),("C","BOLDER")]
    looks=[]

    if key in {"hair_general","mens_hair_beard","hair_extensions","smoothing"}:
        hair=_pick_components(HAIR_COMPONENTS,context,3)
        if not hair: return []
        for i,(lid,role) in enumerate(roles[:len(hair)]):
            hc=hair[i]; comps=[{"domain":"hair",**hc}]
            if key=="mens_hair_beard":
                bc=_beard_component(analysis,role)
                if bc: comps.append({"domain":"beard",**bc})
            title=("Custom Direction · "+" + ".join(c["name"] for c in comps))
            why=f"این Direction از وضعیت مشاهده‌شده و هدف {context.get('style')} ساخته شده و به یک مدل نام‌دار خاص محدود نیست."
            trade=f"Change: {context.get('change_level')} · Maintenance: {context.get('maintenance')}"
            looks.append(_common_look(lid,role,title,comps,why,trade,profile,analysis,context))

    elif key=="hair_color":
        comps=_pick_components(COLOR_COMPONENTS,context,3)
        for i,(lid,role) in enumerate(roles[:len(comps)]):
            cc=comps[i]
            looks.append(_common_look(lid,role,"Custom Color Direction · "+cc["name"],[{"domain":"color",**cc}],"Color Direction بر اساس ظاهر فعلی و هدف مشتری ساخته شده؛ فرمول/level/feasibility از Preview استنباط نمی‌شود.","Professional feasibility remains separate.",profile,analysis,context))

    elif key=="makeup":
        comps=_pick_components(MAKEUP_COMPONENTS,context,3)
        # Build composite makeup looks rather than single catalog names.
        for i,(lid,role) in enumerate(roles):
            selected=comps[:max(1,min(len(comps),i+1))]
            title="Custom Makeup Composition · "+" + ".join(x["name"] for x in selected)
            looks.append(_common_look(lid,role,title,[{"domain":"makeup",**x} for x in selected],"Composition از makeup domains مرتبط با هدف و Event ساخته شده و نباید آناتومی صورت را تغییر دهد.","Intensity/maintenance changes by role.",profile,analysis,context))

    elif key=="nails":
        comps=_pick_components(NAIL_COMPONENTS,context,3)
        for i,(lid,role) in enumerate(roles[:len(comps)]):
            nc=comps[i]
            looks.append(_common_look(lid,role,"Custom Nail Direction · "+nc["name"],[{"domain":"nails",**nc}],"Direction از طول/فرم فعلی قابل مشاهده، هدف و Maintenance ساخته شده است.","Extension/building remains controlled when required.",profile,analysis,context))

    elif key=="bridal_complete":
        # Composition over independently governed components.
        hair=_pick_components(HAIR_COMPONENTS,context,3)
        makeup=_pick_components(MAKEUP_COMPONENTS,context,3)
        nails=_pick_components(NAIL_COMPONENTS,context,3)
        for i,(lid,role) in enumerate(roles):
            comps=[]
            if i<len(hair): comps.append({"domain":"hair",**hair[i]})
            if i<len(makeup): comps.append({"domain":"makeup",**makeup[i]})
            if i<len(nails): comps.append({"domain":"nails",**nails[i]})
            looks.append(_common_look(lid,role,"Complete Look Composition · "+" / ".join(c["name"] for c in comps),comps,"این Complete Look فقط coordination است؛ هر component همچنان owner، Safety و Specialist Validation مستقل خود را دارد.","One unresolved component cannot be hidden by the package.",profile,analysis,context))

    # Add optional Explore directions only when there are valid component alternatives.
    base_pool={"hair_general":HAIR_COMPONENTS,"mens_hair_beard":HAIR_COMPONENTS,"hair_color":COLOR_COMPONENTS,"makeup":MAKEUP_COMPONENTS,"nails":NAIL_COMPONENTS}.get(key,[])
    extras=_pick_components(base_pool,context,6)[3:6] if base_pool else []
    for idx,x in enumerate(extras,start=0):
        lid=chr(ord("D")+idx)
        domain="hair" if key in {"hair_general","mens_hair_beard"} else ("color" if key=="hair_color" else ("makeup" if key=="makeup" else "nails"))
        looks.append(_common_look(lid,"EXPLORE","Explore Custom Direction · "+x["name"],[{"domain":domain,**x}],"Explore یک جهت معتبر اضافه است و Core roles را بازنویسی نمی‌کند.","Optional exploration; not filler.",profile,analysis,context))
    return looks


def source_reality(analysis:dict[str,Any]) -> dict[str,Any]:
    return {"domains":analysis.get("domains",{}),"locks":analysis.get("source_reality_locks",[]),"evidence":analysis.get("evidence",{})}


def preview_contract(analysis:dict[str,Any],look:dict[str,Any],scope:str) -> dict[str,Any]:
    profile=analysis.get("service_profile") or {}
    key=profile.get("profile_key")
    locks=["PRESERVE_IDENTITY","PRESERVE_UNRELATED_REGIONS","NO_UNSOLICITED_BEAUTIFICATION"]
    if key=="hair_color": locks += ["COLOR_ONLY_PRESERVE_CUT_LENGTH_SHAPE"]
    if key=="makeup": locks += ["PRESERVE_FACE_ANATOMY","EDIT_ONLY_REQUESTED_MAKEUP_DOMAINS"]
    if key=="nails": locks += ["PRESERVE_HAND_FINGER_GEOMETRY","PRESERVE_SKIN_JEWELRY_UNLESS_REQUESTED"]
    if key=="mens_hair_beard": locks += ["NO_BEARD_COVERAGE_INCREASE","NO_HAIR_LENGTH_FABRICATION"]
    if key=="hair_extensions": locks += ["EXTENSION_VISUALIZATION_NOT_FEASIBILITY_PROOF"]
    return {"service_profile":key,"scope":scope,"locks":locks,"components":look.get("components",[]),"source_reality":source_reality(analysis)}
