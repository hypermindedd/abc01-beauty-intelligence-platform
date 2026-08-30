#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT_IMPORT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT_IMPORT))
import json,os,subprocess,sys,tempfile,time,socket
from pathlib import Path
from urllib.request import Request,urlopen
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def free_port():
    s=socket.socket();s.bind(("127.0.0.1",0));p=s.getsockname()[1];s.close();return p
def req(url,method="GET",data=None):
    b=None;h={}
    if data is not None:b=json.dumps(data).encode();h["Content-Type"]="application/json"
    with urlopen(Request(url,method=method,data=b,headers=h),timeout=12) as r:
        raw=r.read();return json.loads(raw) if raw else {}
def wait(base,sid,key,vals,timeout=8):
    end=time.time()+timeout
    while time.time()<end:
        s=req(f"{base}/api/sessions/{sid}")
        if s["task"][key] in vals:return s
        time.sleep(.12)
    return req(f"{base}/api/sessions/{sid}")
def upload(base,sid,path,view=None):
    url=f"{base}/api/sessions/{sid}/upload" if not view else f"{base}/api/sessions/{sid}/upload-view/{view}"
    return json.loads(subprocess.check_output(["curl","-fsS","-X","POST",url,"-F",f"file=@{path}"],text=True))

port=free_port();base=f"http://127.0.0.1:{port}";env=os.environ.copy();env.pop("OPENAI_API_KEY",None)
p=subprocess.Popen([sys.executable,"-m","uvicorn","server.app:app","--host","127.0.0.1","--port",str(port)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
checks={}
try:
    for _ in range(80):
        try:h=req(base+"/api/health");break
        except Exception:time.sleep(.1)
    else:raise RuntimeError("server start failed")
    checks["health_v040"]=h["ok"] and h["version"]=="0.4.0"
    reg=req(base+"/api/core/service-profiles")
    checks["cross_domain_profiles"]=all(k in reg["profiles"] for k in ["hair_general","hair_color","makeup","nails","mens_hair_beard","bridal_complete"])
    checks["nail_capture_plan"]="LEFT_HAND_TOP" in req(base+"/api/core/capture-plan/nails")["minimum_views"]

    img=Path(tempfile.gettempdir())/"abc_core_smoke.jpg";Image.new("RGB",(900,900),(82,93,105)).save(img)
    for service in ["hair_general","hair_color","makeup","nails","mens_hair_beard","bridal_complete"]:
        s=req(base+"/api/sessions",method="POST",data={"salon_name":"Smoke","specialist_name":"Spec","client_label":"Client"});sid=s["session_id"]
        plan=req(base+f"/api/core/capture-plan/{service}")
        for view in plan["minimum_views"]:
            upload(base,sid,img,view)
        req(base+f"/api/sessions/{sid}/context",method="POST",data={"service":service,"goal":"refined event direction","occasion":"Event","style":"Refined","change_level":"Noticeable","maintenance":"Moderate","exclusions":[],"notes":""})
        req(base+f"/api/sessions/{sid}/analyze",method="POST",data={})
        s=wait(base,sid,"analysis",{"PASS","FAILED"})
        checks[f"{service}_analysis_pass"]=s["task"]["analysis"]=="PASS"
        checks[f"{service}_analysis_brief_before_recommendation"]=bool((s["analysis"].get("analysis_brief") or {}).get("shared_client_summary"))
        checks[f"{service}_no_recommendation_before_review"]=(s["workflow_state"]=="ANALYSIS_REVIEW" and not s["looks"] and s["engines"]["recommendation"]["state"] in {"PENDING","CHECK","BLOCKED"})
        if (s["analysis"].get("analysis_ready_before_recommendation") and s["safety"]["state"]!="STOP"):
            req(base+f"/api/sessions/{sid}/ack-analysis",method="POST",data={})
            end=time.time()+4
            while time.time()<end:
                s=req(base+f"/api/sessions/{sid}")
                if s["engines"]["recommendation"]["state"] in {"PASS","CHECK","FAILED"}:break
                time.sleep(.1)
        checks[f"{service}_recommendation_bounded"]=len([x for x in s["looks"] if not x["is_explore"]])<=3
        if service=="hair_color":checks["hair_color_s1_guided_caution"]=s["safety"]["tier"]=="S1" and s["safety"]["state"]=="ALLOW"
    # Preview without key must never fake success.
    s=req(base+"/api/sessions",method="POST",data={"salon_name":"Smoke","specialist_name":"Spec","client_label":"Client"});sid=s["session_id"]
    for view in req(base+"/api/core/capture-plan/mens_hair_beard")["minimum_views"]: upload(base,sid,img,view)
    req(base+f"/api/sessions/{sid}/context",method="POST",data={"service":"mens_hair_beard","goal":"modern","occasion":"Event","style":"Modern","change_level":"Noticeable","maintenance":"Moderate","exclusions":[],"notes":""});req(base+f"/api/sessions/{sid}/analyze",method="POST",data={});s=wait(base,sid,"analysis",{"PASS","FAILED"})
    if s["analysis"].get("analysis_ready_before_recommendation"):
        req(base+f"/api/sessions/{sid}/ack-analysis",method="POST",data={});time.sleep(.3);s=req(base+f"/api/sessions/{sid}")
    if s["looks"]:
        req(base+f"/api/sessions/{sid}/select",method="POST",data={"look_id":s["looks"][0]["id"]});req(base+f"/api/sessions/{sid}/preview",method="POST",data={"look_id":s["looks"][0]["id"],"scope":"hair_beard","extra_instruction":""});s=wait(base,sid,"preview",{"BLOCKED","FAILED","PASS","REJECTED_BY_QA"});checks["no_fake_preview_without_key"]=s["task"]["preview"]=="BLOCKED" and s["media"]["preview"] is None
    else: checks["no_fake_preview_without_key"]=False
finally:
    p.terminate();
    try:p.wait(timeout=4)
    except: p.kill()
result="PASS" if all(checks.values()) else "FAIL"
print(json.dumps({"result":result,"checks":checks},ensure_ascii=False,indent=2));sys.exit(0 if result=="PASS" else 1)
