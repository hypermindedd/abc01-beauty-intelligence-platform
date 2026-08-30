from __future__ import annotations
import asyncio, time, shutil, subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from .config import settings, STATIC_DIR, MEDIA_DIR
from .models import NewSessionRequest, ContextUpdate, MessageRequest, SelectLookRequest, PreviewRequest, ValidationRequest
from . import store
from .engines import chat_reply
from .orchestrator import run_analysis, run_recommendation, run_preview
from .style_catalog import catalog_payload
from .domain_profiles import registry_payload as domain_registry_payload, capture_plan
from .direction_catalog import catalog_payload as direction_catalog_payload

APP_VERSION="0.4.0"
app=FastAPI(title="ABC CORE RUNTIME — CROSS DOMAIN",version=APP_VERSION)
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")

@app.get("/")
def home():
    return FileResponse(STATIC_DIR/"index.html")

@app.get("/api/health")
def health():
    return {
        "ok":True,"app":"ABC CORE RUNTIME — CROSS DOMAIN","version":APP_VERSION,
        "provider_configured":bool(settings.openai_api_key),
        "live_text":bool(settings.openai_api_key and settings.live_text),
        "live_visual":bool(settings.openai_api_key and settings.live_visual),
        "models":{
            "consultation":settings.text_model,
            "vision_context":settings.text_model,
            "visual_preview":settings.image_model,
            "visual_qa":settings.text_model,
        },
        "image_quality":settings.image_quality,
        "visual_max_attempts":settings.visual_max_attempts,
        "mode":"LIVE" if settings.openai_api_key else "SHOWCASE_FALLBACK",
        "integrity_policy":"Provider output is quarantined until Visual Integrity QA passes.",
        "truth_note":"Provider configuration does not imply professional validation or Production Readiness."
    }

@app.get("/api/style-catalog")
def style_catalog():
    return catalog_payload()

@app.get("/api/core/service-profiles")
def core_service_profiles():
    return domain_registry_payload()

@app.get("/api/core/direction-catalog")
def core_direction_catalog():
    return direction_catalog_payload()

@app.get("/api/core/capture-plan/{service_key}")
def core_capture_plan(service_key:str):
    return capture_plan(service_key)

@app.post("/api/sessions")
def create_session(req: NewSessionRequest):
    return store.new_session(req.salon_name,req.specialist_name,req.client_label)

@app.get("/api/sessions/{sid}")
def get_session(sid:str):
    try:return store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")

@app.post("/api/sessions/{sid}/context")
def update_context(sid:str, req:ContextUpdate):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    s["context"]=req.model_dump(); s["workflow_state"]="CLIENT_GUIDED_INPUT"
    store.audit(s,"context_updated",context=req.model_dump())
    return s

@app.post("/api/sessions/{sid}/message")
def message(sid:str, req:MessageRequest):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    s["messages"].append({"role":"user","text":req.text,"ts":time.time()})
    reply=chat_reply(s,req.text)
    s["messages"].append({"role":"assistant","text":reply,"ts":time.time()})
    store.audit(s,"consultation_turn")
    return {"reply":reply,"messages":s["messages"]}


def _normalize_standard_image(temp: Path, normalized: Path) -> tuple[int,int]:
    with Image.open(temp) as im:
        im.load(); im=ImageOps.exif_transpose(im)
        if im.mode not in ("RGB","L"):
            if "A" in im.getbands():
                bg=Image.new("RGB",im.size,(18,26,34)); rgba=im.convert("RGBA"); bg.paste(rgba,mask=rgba.getchannel("A")); im=bg
            else: im=im.convert("RGB")
        elif im.mode=="L": im=im.convert("RGB")
        w,h=im.size
        if w<64 or h<64: raise ValueError("image dimensions are too small")
        # Protect live demo from unnecessarily huge uploads while retaining detail.
        max_side=3200
        if max(w,h)>max_side:
            ratio=max_side/max(w,h); im=im.resize((int(w*ratio),int(h*ratio)),Image.Resampling.LANCZOS); w,h=im.size
        im.save(normalized,"JPEG",quality=95,optimize=True)
        return w,h


def _normalize_heic_mac(temp: Path, normalized: Path) -> tuple[int,int]:
    sips=shutil.which("sips")
    if not sips:
        raise RuntimeError("HEIC is supported natively on macOS only in this demo; convert to JPG/PNG on this host.")
    proc=subprocess.run([sips,"-s","format","jpeg",str(temp),"--out",str(normalized)],capture_output=True,text=True,timeout=45)
    if proc.returncode!=0 or not normalized.exists():
        raise RuntimeError((proc.stderr or proc.stdout or "sips conversion failed")[:350])
    with Image.open(normalized) as im:
        im.load(); im=ImageOps.exif_transpose(im).convert("RGB")
        w,h=im.size
        max_side=3200
        if max(w,h)>max_side:
            ratio=max_side/max(w,h); im=im.resize((int(w*ratio),int(h*ratio)),Image.Resampling.LANCZOS); w,h=im.size
        tmp_jpg=normalized.with_name("source_norm.jpg")
        im.save(tmp_jpg,"JPEG",quality=95,optimize=True)
    tmp_jpg.replace(normalized)
    return w,h

@app.post("/api/sessions/{sid}/upload")
async def upload(sid:str, file:UploadFile=File(...)):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    raw=await file.read(); content_type=(file.content_type or "").lower().strip(); original_name=(file.filename or "client-image").strip(); ext=Path(original_name).suffix.lower()
    if not raw: raise HTTPException(400,"Uploaded image is empty.")
    if len(raw)>settings.max_upload_mb*1024*1024: raise HTTPException(413,f"Image is larger than {settings.max_upload_mb} MB.")
    if ext not in {".jpg",".jpeg",".png",".webp",".heic",".heif"} and not content_type.startswith("image/"):
        raise HTTPException(400,f"Unsupported image type: {content_type or ext or 'unknown'}")

    mdir=store.media_dir(sid); temp=mdir/f"_upload{ext if ext else '.bin'}"; normalized=mdir/"source.jpg"; temp.write_bytes(raw)
    try:
        if ext in {".heic",".heif"}: w,h=_normalize_heic_mac(temp,normalized); normalizer="macOS sips + Pillow"
        else: w,h=_normalize_standard_image(temp,normalized); normalizer="Pillow"
    except Exception as e:
        normalized.unlink(missing_ok=True)
        raise HTTPException(400,f"Uploaded file could not be decoded as an image. ({type(e).__name__}: {str(e)[:260]})")
    finally:
        temp.unlink(missing_ok=True)

    ref={
        "filename":normalized.name,"content_type":"image/jpeg","size":[w,h],"uploaded_at":time.time(),
        "original_name":original_name,"original_content_type":content_type,"original_extension":ext,
        "normalized":True,"normalizer":normalizer,"view_id":"FRONT"
    }
    s["media"]["source"]=ref
    s["media"].setdefault("client_views",{})["FRONT"]=ref
    s["media"]["preview"]=None
    store.audit(s,"client_image_uploaded",filename=normalized.name,size=[w,h],original_extension=ext,normalizer=normalizer)
    return {"ok":True,"url":f"/media/{sid}/{normalized.name}","size":[w,h],"normalized":True,"normalizer":normalizer}

@app.post("/api/sessions/{sid}/upload-view/{view_id}")
async def upload_view(sid:str,view_id:str,file:UploadFile=File(...)):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    view_id=view_id.strip().upper()
    allowed={"FRONT","LEFT_45","RIGHT_45","LEFT_PROFILE","RIGHT_PROFILE","BACK","TOP_CROWN","ROOT_DETAIL","MID_LENGTH_DETAIL","ENDS_DETAIL","EYE_DETAIL","LIP_DETAIL","LEFT_HAND_TOP","RIGHT_HAND_TOP","LEFT_HAND_SIDE","RIGHT_HAND_SIDE","NAIL_DETAIL","ATTACHMENT_AREA_DETAIL"}
    if view_id not in allowed:raise HTTPException(400,"Unsupported view_id")
    raw=await file.read();content_type=(file.content_type or "").lower().strip();original_name=(file.filename or "client-image").strip();ext=Path(original_name).suffix.lower()
    if not raw:raise HTTPException(400,"Uploaded image is empty.")
    if len(raw)>settings.max_upload_mb*1024*1024:raise HTTPException(413,f"Image is larger than {settings.max_upload_mb} MB.")
    if ext not in {".jpg",".jpeg",".png",".webp",".heic",".heif"} and not content_type.startswith("image/"):raise HTTPException(400,"Unsupported image type")
    mdir=store.media_dir(sid);temp=mdir/f"_upload_{view_id}{ext if ext else '.bin'}";normalized=mdir/f"source_{view_id}.jpg";temp.write_bytes(raw)
    try:
        if ext in {".heic",".heif"}:w,h=_normalize_heic_mac(temp,normalized);normalizer="macOS sips + Pillow"
        else:w,h=_normalize_standard_image(temp,normalized);normalizer="Pillow"
    except Exception as e:
        normalized.unlink(missing_ok=True);raise HTTPException(400,f"Uploaded file could not be decoded as an image. ({type(e).__name__}: {str(e)[:260]})")
    finally:temp.unlink(missing_ok=True)
    ref={"filename":normalized.name,"content_type":"image/jpeg","size":[w,h],"uploaded_at":time.time(),"original_name":original_name,"original_content_type":content_type,"original_extension":ext,"normalized":True,"normalizer":normalizer,"view_id":view_id}
    s["media"].setdefault("client_views",{})[view_id]=ref
    if view_id=="FRONT" or not s["media"].get("source"):s["media"]["source"]=ref
    s["media"]["preview"]=None
    store.audit(s,"client_view_uploaded",view_id=view_id,filename=normalized.name,size=[w,h])
    return {"ok":True,"view_id":view_id,"url":f"/media/{sid}/{normalized.name}","size":[w,h],"normalizer":normalizer}

@app.get("/media/{sid}/{filename}")
def media(sid:str,filename:str):
    base=(MEDIA_DIR/sid).resolve(); p=(base/filename).resolve()
    if base not in p.parents or not p.exists(): raise HTTPException(404,"media not found")
    return FileResponse(p)

@app.post("/api/sessions/{sid}/analyze")
async def analyze(sid:str):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    if s["task"]["analysis"]=="RUNNING": return {"accepted":False,"state":"RUNNING"}
    asyncio.create_task(run_analysis(sid)); return {"accepted":True,"state":"RUNNING"}

@app.post("/api/sessions/{sid}/ack-analysis")
async def acknowledge_analysis(sid:str):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    if s.get("task",{}).get("analysis")!="PASS":raise HTTPException(409,"Analysis must complete first.")
    if not (s.get("analysis") or {}).get("analysis_ready_before_recommendation"):raise HTTPException(409,"Analysis is not sufficient for recommendation.")
    s["analysis_brief_acknowledged"]=True
    store.audit(s,"analysis_brief_acknowledged")
    asyncio.create_task(run_recommendation(sid))
    return {"accepted":True,"state":"RECOMMENDATION_RUNNING"}

@app.post("/api/sessions/{sid}/explore")
def explore(sid:str):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    if not s["looks"]: raise HTTPException(409,"Run analysis first.")
    s["explore_enabled"]=True; store.audit(s,"explore_enabled")
    return {"looks":s["looks"],"active_count":len(s["looks"])}

@app.post("/api/sessions/{sid}/select")
def select(sid:str,req:SelectLookRequest):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    if not any(x["id"]==req.look_id for x in s["looks"]): raise HTTPException(400,"unknown look")
    s["selected_look_id"]=req.look_id; store.audit(s,"client_selected",look_id=req.look_id); return s

@app.post("/api/sessions/{sid}/preview")
async def preview(sid:str,req:PreviewRequest):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    if s["task"]["preview"]=="RUNNING": return {"accepted":False,"state":"RUNNING"}
    asyncio.create_task(run_preview(sid,req.look_id,req.scope,req.extra_instruction)); return {"accepted":True,"state":"RUNNING"}

@app.post("/api/sessions/{sid}/validate")
def validate(sid:str,req:ValidationRequest):
    try:s=store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    if not s.get("selected_look_id"): raise HTTPException(409,"Client selection is required before Specialist Validation.")
    e=s["engines"]["validation"]; e["state"]="RUNNING"; e["started_at"]=time.time()
    s["specialist_validation"]={"status":"PASSED" if req.decision=="PROCEED" else ("MODIFIED" if req.decision=="MODIFY" else "PARTIAL"),"notes":req.notes}
    mapping={"PROCEED":"PROCEED","MODIFY":"MODIFY","CHECK_FIRST":"CHECK_FIRST","DEFER":"DEFER","STOP":"STOP"}
    if s["safety"]["state"]=="STOP": s["service_decision"]="STOP"
    elif s["safety"]["state"]=="CHECK_FIRST" and req.decision=="PROCEED": s["service_decision"]="CHECK_FIRST"
    else: s["service_decision"]=mapping[req.decision]
    e["finished_at"]=time.time();e["duration_ms"]=int((e["finished_at"]-e["started_at"])*1000);e["state"]="PASS" if s["service_decision"]=="PROCEED" else "CHECK";e["summary"]=s["service_decision"]
    s["workflow_state"]="SERVICE_CONFIRMATION"; store.audit(s,"specialist_validated",requested=req.decision,compiled=s["service_decision"]); return s

@app.delete("/api/sessions/{sid}")
def delete_session(sid:str):
    try:store.get(sid)
    except KeyError:raise HTTPException(404,"session not found")
    store.path_for(sid).unlink(missing_ok=True); m=MEDIA_DIR/sid
    if m.exists(): shutil.rmtree(m)
    return {"ok":True}
