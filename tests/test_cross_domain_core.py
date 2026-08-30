#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT_IMPORT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT_IMPORT))
from server.domain_profiles import resolve_profile,capture_plan,SERVICE_PROFILES
from server.cross_domain_engine import normalize_analysis,compose_recommendations,preview_contract


def analysis_for(service,domains=None,shared=True):
    p=resolve_profile(service)
    return normalize_analysis({
        "image_quality":"USABLE",
        "view_sufficiency":{"accepted_views":p["minimum_views"] or ["FRONT"],"missing_material_views":[],"sufficient_for_analysis":True,"sufficient_for_recommendation":True,"reason":"test"},
        "evidence":{"OBSERVED":["visible evidence"],"USER_REPORTED":[],"INFERRED":[],"UNKNOWN":[],"REQUIRES_PROFESSIONAL_CHECK":[]},
        "domains":domains or {},
        "source_reality_locks":["preserve source truth"],
        "analysis_brief":{"shared_client_summary":["analysis complete"] if shared else [],"specialist_summary":["specialist detail"],"strategy_before_recommendation":["strategy before recommendation"]},
        "limitations":[]
    },p,p["minimum_views"] or ["FRONT"],{"service":service,"goal":"refined","style":"Refined","change_level":"Noticeable","maintenance":"Moderate","occasion":"Event"})

# Core covers every currently canonical product family; it does not create skincare/facial IDs.
assert set(SERVICE_PROFILES)>={"hair_general","hair_color","makeup","nails","mens_hair_beard","bridal_complete","hair_extensions","smoothing"}
assert resolve_profile("SVC-01-003")["profile_key"]=="hair_general"
assert resolve_profile("SVC-02-006")["profile_key"]=="hair_color"
assert resolve_profile("SVC-03-004")["profile_key"]=="makeup"
assert resolve_profile("SVC-04-005")["profile_key"]=="nails"
assert resolve_profile("SVC-05-008")["profile_key"]=="mens_hair_beard"
assert resolve_profile("SVC-01-006")["control_id"]=="CTRL-001"
assert resolve_profile("CTRL-002")["profile_key"]=="makeup"
assert resolve_profile("CTRL-003")["profile_key"]=="nails"
assert resolve_profile("CTRL-004")["profile_key"]=="mens_hair_beard"
assert resolve_profile("CTRL-005")["profile_key"]=="hair_color"
assert resolve_profile("CTRL-008")["profile_key"]=="makeup"
assert resolve_profile("CTRL-010")["profile_key"]=="nails"
assert resolve_profile("facial_skincare")["profile_key"]=="unsupported"

# Capture plans are service-specific, not men's-only.
assert "LEFT_HAND_TOP" in capture_plan("nails")["minimum_views"]
assert "BACK" in capture_plan("hair_color")["minimum_views"]
assert "LEFT_45" in capture_plan("makeup")["minimum_views"]

ctx=lambda service:{"service":service,"goal":"professional event","style":"Refined","change_level":"Noticeable","maintenance":"Moderate","occasion":"Event"}
safety={"state":"ALLOW"}

# No recommendation is emitted before an analysis brief exists.
a=analysis_for("hair_general",shared=False)
assert compose_recommendations(a,ctx("hair_general"),safety)==[]

# Hair recommendations are custom compositions, not forced named styles.
a=analysis_for("hair_general",{"hair":{"length":"MEDIUM","texture":"WAVY","density":"MEDIUM"}})
looks=compose_recommendations(a,ctx("hair_general"),safety)
assert 1<=len([x for x in looks if not x["is_explore"]])<=3
assert all(x["custom_composition"] for x in looks)
assert all(x["components"] for x in looks)

# Men's beard source reality prevents a full beard component for sparse coverage.
a=analysis_for("mens_hair_beard",{"hair":{"length":"SHORT","texture":"WAVY"},"beard":{"coverage":"SPARSE"}})
looks=compose_recommendations(a,ctx("mens_hair_beard"),safety)
for l in looks:
    for c in l["components"]:
        if c.get("domain")=="beard":
            assert c["min_coverage"] in {"STUBBLE","SPARSE"}

# Domain-specific preview hard locks.
assert "COLOR_ONLY_PRESERVE_CUT_LENGTH_SHAPE" in preview_contract(analysis_for("hair_color"),{"components":[]},"color")["locks"]
assert "PRESERVE_FACE_ANATOMY" in preview_contract(analysis_for("makeup"),{"components":[]},"makeup")["locks"]
assert "PRESERVE_HAND_FINGER_GEOMETRY" in preview_contract(analysis_for("nails"),{"components":[]},"nails")["locks"]
assert "NO_BEARD_COVERAGE_INCREASE" in preview_contract(analysis_for("mens_hair_beard"),{"components":[]},"hair_beard")["locks"]

# Combined look is coordination over independently governed components.
a=analysis_for("bridal_complete",{"hair":{},"makeup":{},"nails":{}})
looks=compose_recommendations(a,ctx("bridal_complete"),safety)
assert looks and all(len(x["canonical_service_ids"])>=4 for x in looks)
assert all(any(c["domain"]=="hair" for c in x["components"]) for x in looks[:3])


# Professional multi-view gate: partial view set can be analyzed but cannot emit ranked recommendations.
p=resolve_profile("hair_color")
partial=normalize_analysis({
    "image_quality":"USABLE",
    "view_sufficiency":{"accepted_views":["FRONT"],"sufficient_for_analysis":True,"sufficient_for_recommendation":True},
    "evidence":{"OBSERVED":[],"USER_REPORTED":[],"INFERRED":[],"UNKNOWN":[],"REQUIRES_PROFESSIONAL_CHECK":[]},
    "domains":{},"source_reality_locks":[],
    "analysis_brief":{"shared_client_summary":["partial"],"specialist_summary":[],"strategy_before_recommendation":[]},
    "limitations":[]
},p,["FRONT"],ctx("hair_color"))
assert partial["view_sufficiency"]["sufficient_for_analysis"] is True
assert partial["analysis_ready_before_recommendation"] is False
assert "BACK" in partial["view_sufficiency"]["missing_material_views"]

print("PASS: cross-domain core profiles, controlled routing, professional multi-view gate, analysis-before-recommendation, custom composition, preview locks")
