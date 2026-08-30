#!/usr/bin/env python3
import sys, asyncio
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from server import store, orchestrator
from server.domain_profiles import resolve_profile

s=store.new_session("T","S","C")
profile=resolve_profile("mens_hair_beard")
s["context"].update({"service":"mens_hair_beard","goal":"modern","style":"Modern","change_level":"Noticeable","maintenance":"Moderate","occasion":"Event"})
s["analysis"]={
    "service_profile":profile,
    "domains":{"hair":{"length":"SHORT","texture":"WAVY","density":"MEDIUM"},"beard":{"coverage":"SPARSE","length":"STUBBLE","moustache":"LIGHT"}},
    "evidence":{"OBSERVED":[],"USER_REPORTED":[],"INFERRED":[],"UNKNOWN":[],"REQUIRES_PROFESSIONAL_CHECK":[]},
    "source_reality_locks":["NO_BEARD_COVERAGE_INCREASE"],
    "analysis_ready_before_recommendation":True,
}
s["safety"]={"tier":"S0","state":"ALLOW","reasons":[],"professional_checks":[]}
s["looks"]=[{"id":"A","role":"BEST FIT","title":"Test","components":[],"why":"test","preview_eligible":True}]
s["selected_look_id"]="A"
mdir=store.media_dir(s["session_id"])
src=mdir/"source_FRONT.jpg"; Image.new("RGB",(512,512),(50,60,70)).save(src)
ref={"filename":src.name,"size":[512,512],"view_id":"FRONT"}
s["media"]["source"]=ref
s["media"]["client_views"]={"FRONT":ref}
store.put(s)

calls={"edit":0,"qa":0}
def fake_edit(session, source_path, look, scope, extra, output_path, retry_correction=""):
    calls["edit"]+=1
    Image.new("RGB",(512,512),(60+calls["edit"],70,80)).save(output_path)
    return {"provider":"mock","model":"mock"}
def fake_qa(session, source_views, result_path, look, scope):
    calls["qa"]+=1
    if calls["qa"]==1:
        return {"compiled_result":"REJECT","compiled_reasons":["beard coverage increased beyond source"],"identity_continuity":"GOOD","geometry_drift":"NONE","unrelated_change":"LOW","source_reality_violation":True}
    return {"compiled_result":"PASS","compiled_reasons":[],"identity_continuity":"GOOD","geometry_drift":"NONE","unrelated_change":"LOW","source_reality_violation":False}

orchestrator.run_image_edit=fake_edit
orchestrator.run_visual_qa=fake_qa
class S: visual_max_attempts=2
orchestrator.settings=S()
asyncio.run(orchestrator.run_preview(s["session_id"],"A","hair_beard",""))
r=store.get(s["session_id"])
assert r["task"]["preview"]=="PASS"
assert r["media"]["preview"] is not None
assert r["media"]["preview"]["attempt"]==2
assert len(r["media"]["preview_history"])==1
assert len(r["media"]["preview_attempts"])==2
assert r["media"]["preview_attempts"][0]["published"] is False
assert r["media"]["preview_attempts"][1]["published"] is True
assert not any(mdir.glob("quarantine_*.png"))
print("PASS: rejected provider output stayed quarantined/deleted; only QA-PASS output published")
