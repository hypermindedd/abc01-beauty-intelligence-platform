from __future__ import annotations
from typing import Any

# Cross-domain service profile registry. These profiles do not create new canonical
# service IDs. They map product/runtime intents to the frozen ABC ontology.

SERVICE_PROFILES: dict[str, dict[str, Any]] = {
    "hair_general": {
        "family":"SVC-01", "label":"Hair Cut / Style", "canonical_ids":["SVC-01-001","SVC-01-002","SVC-01-003","SVC-01-004","SVC-01-005"],
        "knowledge_owners":["ABC-KB-003"], "baseline_safety":"S0",
        "analysis_domains":["face","hair"],
        "visualization_types":["LENGTH_CHANGE","TEXTURE_STYLE_CHANGE"],
        "minimum_views":["FRONT","LEFT_45","RIGHT_45"],
        "conditional_views":["LEFT_PROFILE","RIGHT_PROFILE","BACK","TOP_CROWN"],
        "preview_scope":"hair",
    },
    "hair_color": {
        "family":"SVC-02", "label":"Hair Color", "canonical_ids":[f"SVC-02-00{i}" for i in range(1,10)],
        "knowledge_owners":["ABC-KB-004"], "baseline_safety":"S1",
        "analysis_domains":["hair","color"],
        "visualization_types":["COLOR_CHANGE"],
        "minimum_views":["FRONT","LEFT_45","RIGHT_45","BACK"],
        "conditional_views":["ROOT_DETAIL","MID_LENGTH_DETAIL","ENDS_DETAIL"],
        "preview_scope":"color",
    },
    "makeup": {
        "family":"SVC-03", "label":"Makeup", "canonical_ids":["SVC-03-001","SVC-03-002","SVC-03-003","SVC-03-004","SVC-03-005","SVC-03-006","SVC-03-007"],
        "knowledge_owners":["ABC-KB-005"], "baseline_safety":"S0",
        "analysis_domains":["face","makeup","skin_visual"],
        "visualization_types":["FACE_SURFACE_APPLICATION"],
        "minimum_views":["FRONT","LEFT_45","RIGHT_45"],
        "conditional_views":["EYE_DETAIL","LIP_DETAIL"],
        "preview_scope":"makeup",
    },
    "nails": {
        "family":"SVC-04", "label":"Nails", "canonical_ids":["SVC-04-001","SVC-04-002","SVC-04-003","SVC-04-004","SVC-04-005","SVC-04-006","SVC-04-007"],
        "knowledge_owners":["ABC-KB-006"], "baseline_safety":"S0",
        "analysis_domains":["hands","nails"],
        "visualization_types":["NAIL_SURFACE_APPLICATION","ADDITION_OVERLAY"],
        "minimum_views":["LEFT_HAND_TOP","RIGHT_HAND_TOP"],
        "conditional_views":["LEFT_HAND_SIDE","RIGHT_HAND_SIDE","NAIL_DETAIL"],
        "preview_scope":"nails",
    },
    "mens_hair_beard": {
        "family":"SVC-05", "label":"Men's Hair & Beard", "canonical_ids":[f"SVC-05-00{i}" for i in range(1,10)],
        "knowledge_owners":["ABC-KB-007","ABC-KB-008"], "baseline_safety":"S0",
        "analysis_domains":["face","hair","beard"],
        "visualization_types":["LENGTH_CHANGE","TEXTURE_STYLE_CHANGE","ADDITION_OVERLAY"],
        "minimum_views":["FRONT","LEFT_45","RIGHT_45"],
        "conditional_views":["LEFT_PROFILE","RIGHT_PROFILE","BACK","TOP_CROWN"],
        "preview_scope":"hair_beard",
    },
    "bridal_complete": {
        "family":"COMPOSITE", "label":"Bridal / Complete Look", "canonical_ids":["SVC-01-006","SVC-03-005","SVC-04-007","CTRL-009"],
        "knowledge_owners":["ABC-KB-003","ABC-KB-005","ABC-KB-006","ABC-KB-009"], "baseline_safety":"S1",
        "analysis_domains":["face","hair","makeup","skin_visual","hands","nails","coordination"],
        "visualization_types":["FULL_LOOK_COMPOSITE"],
        "minimum_views":["FRONT","LEFT_45","RIGHT_45","BACK","LEFT_HAND_TOP","RIGHT_HAND_TOP"],
        "conditional_views":["LEFT_PROFILE","RIGHT_PROFILE","TOP_CROWN","EYE_DETAIL","LIP_DETAIL","NAIL_DETAIL"],
        "preview_scope":"complete",
    },
    "hair_extensions": {
        "family":"SVC-01", "label":"Hair Extensions", "canonical_ids":["SVC-01-007","CTRL-006"],
        "knowledge_owners":["ABC-KB-013"], "baseline_safety":"S2",
        "analysis_domains":["hair"],
        "visualization_types":["ADDITION_OVERLAY","LENGTH_CHANGE"],
        "minimum_views":["FRONT","LEFT_45","RIGHT_45","BACK"],
        "conditional_views":["TOP_CROWN","ATTACHMENT_AREA_DETAIL"],
        "preview_scope":"hair",
    },
    "smoothing": {
        "family":"CTRL-007", "label":"Chemical Smoothing / Keratin", "canonical_ids":["CTRL-007"],
        "knowledge_owners":["ABC-KB-014"], "baseline_safety":"S2",
        "analysis_domains":["hair"],
        "visualization_types":["TEXTURE_STYLE_CHANGE"],
        "minimum_views":["FRONT","LEFT_45","RIGHT_45","BACK"],
        "conditional_views":["MID_LENGTH_DETAIL","ENDS_DETAIL"],
        "preview_scope":"hair",
    },
}

ALIASES = {
    # Existing men's demo aliases
    "groom_event":"mens_hair_beard",
    "hair_beard":"mens_hair_beard",
    "color_gray":"hair_color",
    # Generic product aliases
    "hair":"hair_general",
    "haircut":"hair_general",
    "style":"hair_general",
    "color":"hair_color",
    "makeup":"makeup",
    "nail":"nails",
    "nails":"nails",
    "bridal":"bridal_complete",
    "complete_look":"bridal_complete",
    "extensions":"hair_extensions",
    "keratin":"smoothing",
}

CONTROLLED_IDS = {
    "CTRL-001","CTRL-002","CTRL-003","CTRL-004","CTRL-005","CTRL-006","CTRL-007","CTRL-008","CTRL-009","CTRL-010"
}

# Exact controlled-service routing. These mappings preserve the frozen service owner
# and add coordination/controlled metadata without inventing new SVC/CTRL identifiers.
EXACT_ROUTES: dict[str, dict[str, Any]] = {
    "SVC-01-006":{"base":"hair_general","requested":"SVC-01-006","ctrl":"CTRL-001","owners":["ABC-KB-003","ABC-KB-009"],"controlled":True,"label":"Bridal / Formal Hair"},
    "CTRL-001":{"base":"hair_general","requested":"CTRL-001","svc":"SVC-01-006","owners":["ABC-KB-003","ABC-KB-009"],"controlled":True,"label":"Bridal Hair"},
    "SVC-01-007":{"base":"hair_extensions","requested":"SVC-01-007","ctrl":"CTRL-006","owners":["ABC-KB-013"],"controlled":True,"label":"Hair Extensions"},
    "CTRL-006":{"base":"hair_extensions","requested":"CTRL-006","svc":"SVC-01-007","owners":["ABC-KB-013"],"controlled":True,"label":"Hair Extensions"},
    "SVC-02-009":{"base":"hair_color","requested":"SVC-02-009","ctrl":"CTRL-005","owners":["ABC-KB-004"],"controlled":True,"label":"Color Correction"},
    "CTRL-005":{"base":"hair_color","requested":"CTRL-005","svc":"SVC-02-009","owners":["ABC-KB-004"],"controlled":True,"label":"Color Correction"},
    "SVC-03-005":{"base":"makeup","requested":"SVC-03-005","ctrl":"CTRL-002","owners":["ABC-KB-005","ABC-KB-009"],"controlled":True,"label":"Bridal Makeup"},
    "CTRL-002":{"base":"makeup","requested":"CTRL-002","svc":"SVC-03-005","owners":["ABC-KB-005","ABC-KB-009"],"controlled":True,"label":"Bridal Makeup"},
    "SVC-03-006":{"base":"makeup","requested":"SVC-03-006","ctrl":"CTRL-008","owners":["ABC-KB-005"],"controlled":True,"label":"Corrective / Coverage Makeup"},
    "CTRL-008":{"base":"makeup","requested":"CTRL-008","svc":"SVC-03-006","owners":["ABC-KB-005"],"controlled":True,"label":"Corrective / Coverage Makeup"},
    "SVC-04-002":{"base":"nails","requested":"SVC-04-002","ctrl":"CTRL-010","owners":["ABC-KB-006"],"controlled":True,"label":"Nail Length Extension / Building"},
    "CTRL-010":{"base":"nails","requested":"CTRL-010","svc":"SVC-04-002","owners":["ABC-KB-006"],"controlled":True,"label":"Nail Length Extension / Building"},
    "SVC-04-007":{"base":"nails","requested":"SVC-04-007","ctrl":"CTRL-003","owners":["ABC-KB-006","ABC-KB-009"],"controlled":True,"label":"Bridal Nails"},
    "CTRL-003":{"base":"nails","requested":"CTRL-003","svc":"SVC-04-007","owners":["ABC-KB-006","ABC-KB-009"],"controlled":True,"label":"Bridal Nails"},
    "SVC-05-009":{"base":"mens_hair_beard","requested":"SVC-05-009","ctrl":"CTRL-004","owners":["ABC-KB-007","ABC-KB-008","ABC-KB-009"],"controlled":True,"label":"Groom Styling"},
    "CTRL-004":{"base":"mens_hair_beard","requested":"CTRL-004","svc":"SVC-05-009","owners":["ABC-KB-007","ABC-KB-008","ABC-KB-009"],"controlled":True,"label":"Groom Styling"},
    "CTRL-007":{"base":"smoothing","requested":"CTRL-007","owners":["ABC-KB-014"],"controlled":True,"label":"Chemical Smoothing / Keratin"},
    "CTRL-009":{"base":"bridal_complete","requested":"CTRL-009","owners":["ABC-KB-003","ABC-KB-005","ABC-KB-006","ABC-KB-009"],"controlled":True,"label":"Complex Bridal Full-Look Package"},
}


def _exact_profile(key: str) -> dict[str, Any] | None:
    route=EXACT_ROUTES.get(key)
    if not route:
        return None
    base=route["base"]
    payload={"profile_key":base, **SERVICE_PROFILES[base]}
    payload["requested_canonical_id"]=route["requested"]
    payload["controlled"]=bool(route.get("controlled"))
    payload["knowledge_owners"]=list(route.get("owners") or payload.get("knowledge_owners",[]))
    payload["label"]=route.get("label",payload.get("label"))
    if route.get("ctrl"): payload["control_id"]=route["ctrl"]
    if route.get("svc"): payload["service_id"]=route["svc"]
    return payload


def resolve_profile(service_key: str | None) -> dict[str, Any]:
    key = (service_key or "").strip()
    key = ALIASES.get(key, key)
    if key in SERVICE_PROFILES:
        return {"profile_key":key, **SERVICE_PROFILES[key]}

    exact=_exact_profile(key)
    if exact:
        return exact

    # Canonical ID routing without inventing semantics. Exact controlled IDs are
    # resolved above before family-level routing.
    if key.startswith("SVC-01-"):
        return {"profile_key":"hair_general", **SERVICE_PROFILES["hair_general"], "requested_canonical_id":key}
    if key.startswith("SVC-02-"):
        return {"profile_key":"hair_color", **SERVICE_PROFILES["hair_color"], "requested_canonical_id":key}
    if key.startswith("SVC-03-"):
        return {"profile_key":"makeup", **SERVICE_PROFILES["makeup"], "requested_canonical_id":key}
    if key.startswith("SVC-04-"):
        return {"profile_key":"nails", **SERVICE_PROFILES["nails"], "requested_canonical_id":key}
    if key.startswith("SVC-05-"):
        return {"profile_key":"mens_hair_beard", **SERVICE_PROFILES["mens_hair_beard"], "requested_canonical_id":key}

    return {
        "profile_key":"unsupported",
        "label":"Unsupported / Unmapped Service",
        "canonical_ids":[],
        "knowledge_owners":[],
        "baseline_safety":"S0",
        "analysis_domains":[],
        "visualization_types":[],
        "minimum_views":[],
        "conditional_views":[],
        "preview_scope":"complete",
        "unsupported_service":key,
    }


def capture_plan(service_key: str | None) -> dict[str, Any]:
    p=resolve_profile(service_key)
    return {
        "service_profile":p["profile_key"],
        "requested_canonical_id":p.get("requested_canonical_id"),
        "minimum_views":list(p.get("minimum_views",[])),
        "conditional_views":list(p.get("conditional_views",[])),
        "rule":"Collect the service-specific minimum professional view set before ranked recommendation; request conditional views only when a material evidence gap remains.",
    }


def registry_payload() -> dict[str, Any]:
    return {
        "version":"0.4.0",
        "profiles":SERVICE_PROFILES,
        "aliases":ALIASES,
        "exact_controlled_routes":EXACT_ROUTES,
        "note":"Runtime routing layer over the frozen ABC ontology. No new SVC/CTRL IDs are created here.",
    }
