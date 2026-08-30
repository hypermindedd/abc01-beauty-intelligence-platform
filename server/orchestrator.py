from __future__ import annotations
import asyncio,time,traceback
from pathlib import Path
from . import store
from .config import MEDIA_DIR,settings
from .engines import consultation_engine,context_engine,safety_engine,recommendation_engine,run_image_edit,run_visual_qa
from .providers.openai_provider import ProviderUnavailable


def _engine_start(s,key):
    e=s["engines"][key];e["state"]="RUNNING";e["started_at"]=time.time();e["finished_at"]=None;e["summary"]="";e["detail"]={};store.audit(s,"engine_started",engine=key)

def _engine_end(s,key,state="PASS",summary="",detail=None):
    e=s["engines"][key];e["state"]=state;e["finished_at"]=time.time();e["duration_ms"]=int((e["finished_at"]-(e["started_at"] or e["finished_at"]))*1000);e["summary"]=summary;e["detail"]=detail or {};store.audit(s,"engine_finished",engine=key,state=state,duration_ms=e["duration_ms"])

def _view_paths(sid:str,s:dict):
    out={}
    views=(s.get("media") or {}).get("client_views") or {}
    for vid,ref in views.items():
        p=MEDIA_DIR/sid/ref["filename"]
        if p.exists(): out[vid]=p
    if not out and (s.get("media") or {}).get("source"):
        ref=s["media"]["source"];p=MEDIA_DIR/sid/ref["filename"]
        if p.exists():out["FRONT"]=p
    return out

async def run_analysis(sid:str):
    s=store.get(sid);s["task"]["analysis"]="RUNNING";s["task"]["error"]=None;s["turn_state"]="PROCESSING";store.put(s)
    try:
        _engine_start(s,"consultation");store.put(s)
        c=consultation_engine(s);_engine_end(s,"consultation","PASS","Intent, service profile and capture plan routed.",c);store.put(s)

        _engine_start(s,"context");store.put(s)
        views=_view_paths(sid,s);ctx=await asyncio.to_thread(context_engine,s,views);s["analysis"]=ctx
        ready=bool(ctx.get("analysis_ready_before_recommendation"));ctx_state="PASS" if ready else "CHECK"
        _engine_end(s,"context",ctx_state,"Analysis brief compiled before recommendation.",ctx);store.put(s)

        _engine_start(s,"safety_pre");store.put(s)
        safety=safety_engine(s);s["safety"]=safety;st="BLOCKED" if safety["state"]=="STOP" else ("CHECK" if safety["state"]=="CHECK_FIRST" else "PASS")
        _engine_end(s,"safety_pre",st,f"{safety['tier']} / {safety['state']}",safety);store.put(s)

        # Hard product rule: analysis must be rendered/reviewed before AG-04 may emit recommendations.
        s["looks"]=[]
        s["analysis_brief_acknowledged"]=False
        rec=s["engines"]["recommendation"]
        if safety["state"]=="STOP":
            rec["state"]="BLOCKED";rec["summary"]="Recommendation blocked by Safety."
        elif not ready:
            rec["state"]="CHECK";rec["summary"]="Analysis/evidence not sufficient for recommendation.";rec["detail"]={"missing_material_views":(ctx.get("view_sufficiency") or {}).get("missing_material_views",[])}
        else:
            rec["state"]="PENDING";rec["summary"]="Waiting for Specialist/Shared Analysis Review.";rec["detail"]={"gate":"ANALYSIS_REVIEW_REQUIRED"}
        s["workflow_state"]="ANALYSIS_REVIEW";s["turn_state"]="EMITTING_ANALYSIS_BRIEF";s["task"]["analysis"]="PASS";store.put(s)
    except Exception as e:
        s["task"]["analysis"]="FAILED";s["task"]["error"]=f"{type(e).__name__}: {e}";s["turn_state"]="EMITTING_FAILURE_RECOVERY";store.audit(s,"analysis_failed",error=s["task"]["error"],trace=traceback.format_exc()[-3000:]);store.put(s)

async def run_recommendation(sid:str):
    s=store.get(sid)
    if not s.get("analysis_brief_acknowledged"):
        raise RuntimeError("Analysis Brief must be reviewed before recommendation.")
    if s.get("safety",{}).get("state")=="STOP":
        return
    _engine_start(s,"recommendation");store.put(s)
    try:
        s["looks"]=recommendation_engine(s);core=[x for x in s["looks"] if not x["is_explore"]]
        state="PASS" if core else "CHECK"
        summary=f"{len(core)} evidence-compatible Core direction(s) ready after Analysis Review." if core else "No valid Core direction; additional input required."
        _engine_end(s,"recommendation",state,summary,{"core_count":len(core),"analysis_review_acknowledged":True})
        s["workflow_state"]="SHARED_REVIEW";s["turn_state"]="EMITTING_OPTIONS";store.put(s)
    except Exception as e:
        _engine_end(s,"recommendation","FAILED","Recommendation generation failed.",{"error":f"{type(e).__name__}: {e}"});store.put(s);raise

async def run_preview(sid:str,look_id:str,scope:str,extra:str):
    s=store.get(sid);s["task"]["preview"]="RUNNING";s["task"]["error"]=None;store.put(s)
    try:
        views=_view_paths(sid,s)
        if not views:raise RuntimeError("Client image is required before Live Preview.")
        # FRONT is preferred as provider edit source; otherwise first accepted view.
        src=views.get("FRONT") or next(iter(views.values()))
        look=next((x for x in s["looks"] if x["id"]==look_id),None)
        if not look:raise RuntimeError("Selected direction was not found.")
        if s["safety"]["state"]=="STOP":raise RuntimeError("Preview blocked by Safety.")
        if not look.get("preview_eligible",False):raise RuntimeError("Selected direction is not Preview-eligible.")

        _engine_start(s,"visual_preview");store.put(s);accepted=None;last_qa=None;retry_correction=""
        for attempt in range(1,settings.visual_max_attempts+1):
            qname=f"quarantine_{look_id}_{int(time.time()*1000)}_a{attempt}.png";qpath=MEDIA_DIR/sid/qname
            provider=await asyncio.to_thread(run_image_edit,s,src,look,scope,extra,qpath,retry_correction)
            _engine_start(s,"visual_qa");store.put(s)
            qa=await asyncio.to_thread(run_visual_qa,s,views,qpath,look,scope);last_qa=qa
            rec={"attempt":attempt,"look_id":look_id,"scope":scope,"created_at":time.time(),"provider":provider,"qa":qa,"published":False};s["media"].setdefault("preview_attempts",[]).append(rec)
            if qa.get("compiled_result")=="PASS":
                final_name=f"preview_{look_id}_{int(time.time())}.png";final_path=MEDIA_DIR/sid/final_name;qpath.replace(final_path)
                preview={"filename":final_name,"look_id":look_id,"created_at":time.time(),"provider":provider,"scope":scope,"qa":qa,"attempt":attempt,"integrity_state":"PASS"};rec["published"]=True;s["media"]["preview"]=preview;s["media"]["preview_history"].append(preview);s["selected_look_id"]=look_id;accepted=preview;_engine_end(s,"visual_qa","PASS",f"Cross-domain Visual Integrity PASS on attempt {attempt}.",qa);store.put(s);break
            reasons=qa.get("compiled_reasons") or ["Visual integrity rejected."];_engine_end(s,"visual_qa","REJECTED",f"Attempt {attempt} rejected.",qa);store.put(s);qpath.unlink(missing_ok=True);retry_correction="Correct prior failures only: "+"; ".join(reasons)+". Preserve source truth and do not compensate with beautification."
            if attempt<settings.visual_max_attempts:_engine_start(s,"visual_preview");store.put(s)
        if accepted:
            _engine_end(s,"visual_preview","PASS",f"Provider output accepted after {accepted['attempt']} attempt(s).",accepted["provider"]);s["task"]["preview"]="PASS";s["turn_state"]="EMITTING_PREVIEW"
        else:
            s["media"]["preview"]=None;_engine_end(s,"visual_preview","REJECTED",f"No preview passed integrity after {settings.visual_max_attempts} attempt(s).",last_qa or {});s["task"]["preview"]="REJECTED_BY_QA";s["task"]["error"]="Preview rejected by source-reality/identity gate.";s["turn_state"]="EMITTING_FAILURE_RECOVERY"
        store.put(s)
    except ProviderUnavailable as e:
        s["task"]["preview"]="BLOCKED";s["task"]["error"]=str(e)
        if s["engines"]["visual_preview"]["state"]=="RUNNING":_engine_end(s,"visual_preview","BLOCKED","Live provider unavailable.",{"error":str(e)})
        store.put(s)
    except Exception as e:
        s["task"]["preview"]="FAILED";s["task"]["error"]=f"{type(e).__name__}: {e}"
        if s["engines"]["visual_preview"]["state"]=="RUNNING":_engine_end(s,"visual_preview","FAILED","Preview generation failed.",{"error":s["task"]["error"]})
        store.audit(s,"preview_failed",error=s["task"]["error"],trace=traceback.format_exc()[-3000:]);store.put(s)
