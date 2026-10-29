"""#44 bounded policy sizing: real guide inputs, isolated loopback process.

This does not choose production policy, enable admission in main, or measure a
Docker CPU quota. It can profile with/without the opt-in admission adapter; batch values are not policy.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import ctypes
from ctypes import wintypes
import hashlib
import http.client
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import time
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[3]


def memory_snapshot():
    if os.name!="nt": return {"kind":"unavailable"}
    class Counters(ctypes.Structure):
        _fields_=[("cb",wintypes.DWORD),("faults",wintypes.DWORD),
            ("peak_working_set",ctypes.c_size_t),("working_set",ctypes.c_size_t),
            ("peak_paged",ctypes.c_size_t),("paged",ctypes.c_size_t),
            ("peak_nonpaged",ctypes.c_size_t),("nonpaged",ctypes.c_size_t),
            ("pagefile",ctypes.c_size_t),("peak_pagefile",ctypes.c_size_t)]
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    psapi=ctypes.WinDLL("psapi",use_last_error=True)
    fn=psapi.GetProcessMemoryInfo
    fn.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    fn.restype=wintypes.BOOL
    value=Counters();value.cb=ctypes.sizeof(value)
    if not fn(kernel.GetCurrentProcess(),ctypes.byref(value),value.cb):
        return {"kind":"unavailable","error":ctypes.get_last_error()}
    return {"kind":"Windows own-process working set","working_set":value.working_set,
            "peak_working_set":value.peak_working_set,"pagefile":value.pagefile}


def serve(admission_budget=0,admission_active=0):
    sys.path.insert(0,str(ROOT/"backend"))
    from fastapi import FastAPI
    from app.review_app import create_review_app,local_review_config
    from app.core.request_limits import InputLimits
    from app.core.sql_limits import SQLLimits
    from app.core.admission import AdmissionController,AdmissionPolicy,Rate
    from app.labs.practice_extensions import PERMISSION_COMMANDS
    from app.labs.sql_injection import QUERY_PREFIX,QUERY_SUFFIX
    import sqlite3
    import uvicorn
    proposal=json.loads((ROOT/"docs/verification/evidence/2026-10-28-issue42-sizing-summary.json").read_text(encoding="utf-8"))["proposal"]
    def authorizer(action,arg1,arg2,database,trigger):
        if action in (sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_RECURSIVE):
            return sqlite3.SQLITE_OK
        if action==sqlite3.SQLITE_FUNCTION and arg2 in {"length","printf","sum"}:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    statement=4*proposal["string_codepoints"]+len((QUERY_PREFIX+QUERY_SUFFIX+"EXPLAIN ").encode())
    statement=1<<(statement-1).bit_length()
    controller=None
    if admission_budget:
        controller=AdmissionController(AdmissionPolicy(
            Rate(admission_budget,1),
            {a:Rate(admission_budget,1) for a in ("analyze","attempt","render","metadata")},
            None,admission_active,
            {a:admission_active for a in ("analyze","attempt","render","metadata")},1))
    app=create_review_app(
        input_limits=InputLimits(proposal["string_codepoints"],proposal["body_bytes"],
            proposal["history_count"],proposal["history_total_codepoints"],
            (1<<53)-1,frozenset(PERMISSION_COMMANDS)),
        sql_limits=SQLLimits(proposal["sql_vm_shared_request"],proposal["sql_request_deadline_ms"],
            proposal["returned_rows"],proposal["single_sql_value_bytes"],
            proposal["sql_result_bytes"],proposal["sql_result_bytes"],statement),
        sql_authorizer=authorizer,response_bytes=proposal["api_response_bytes"],
        admission_controller=controller)
    state={"active":0,"peak_active":0,"completed":0}
    class Observe:
        def __init__(self,inner):self.inner=inner
        async def __call__(self,scope,receive,send):
            if scope["type"]!="http" or not scope["path"].startswith("/labs"):
                return await self.inner(scope,receive,send)
            state["active"]+=1;state["peak_active"]=max(state["peak_active"],state["active"])
            try:await self.inner(scope,receive,send)
            finally:
                state["active"]-=1;state["completed"]+=1
    outer=FastAPI()
    @outer.get("/_profile")
    def snapshot():
        return {"cpu_seconds":time.process_time(),"memory":memory_snapshot(),**state}
    @outer.get("/_stop")
    def stop():
        runner.should_exit=True
        return {"ok":True}
    outer.mount("/",Observe(app))
    sock=socket.socket();sock.bind(("127.0.0.1",0))
    port=sock.getsockname()[1]
    runner=uvicorn.Server(local_review_config(outer,port=port))
    print(json.dumps({"port":port}),flush=True)
    try:runner.run(sockets=[sock])
    finally:sock.close()


def exchange(port,case):
    raw=json.dumps(case["payload"],ensure_ascii=False).encode() if case["method"]=="POST" else None
    conn=http.client.HTTPConnection("127.0.0.1",port,timeout=5)
    begin=time.perf_counter()
    try:
        conn.request(case["method"],case["path"],raw,{"Content-Type":"application/json"})
        response=conn.getresponse();body=response.read()
        elapsed=(time.perf_counter()-begin)*1000
        value={}
        if "application/json" in (response.getheader("Content-Type") or ""):
            value=json.loads(body)
        trace=value.get("learning_trace",value) if isinstance(value,dict) else {}
        return {"case":case["id"],"group":case["group"],"method":case["method"],
            "path":case["path"],"status":response.status,"bytes":len(body),
            "elapsed_ms":elapsed,
            "execution_status":(trace.get("execution") or {}).get("status") if isinstance(trace,dict) else None,
            "analysis_status":trace.get("analysis_status") if isinstance(trace,dict) else None}
    finally:conn.close()


def build_cases():
    catalog=json.loads(subprocess.check_output(
        ["node",str(ROOT/"docs/verification/scripts/learning_flow_review.mjs"),"catalog"],
        cwd=ROOT).decode("utf-8"))
    cases=[]
    for lab in catalog:
        history=[]
        for step in lab["lesson"]["steps"]:
            text=step["suggestion"]
            payload={lab["field"]:int(text) if lab["numeric"] else text}
            if lab["category"]=="idor" and lab["difficulty"]=="medium":
                payload["claimed_user_id"]=2001
            if lab["category"]=="permissions":payload["history"]=list(history)
            for action in ("analyze","attempt"):
                cases.append({"id":lab["id"]+"/"+step["id"]+"/"+action,
                    "group":"actual-guide","method":"POST","path":f'/labs/{lab["id"]}/{action}',
                    "payload":payload})
            if lab["category"]=="reflected_xss":
                # Plain marker only: never execute browser script during sizing.
                cases.append({"id":lab["id"]+"/"+step["id"]+"/render-plain",
                    "group":"render-plain","method":"GET",
                    "path":f'/labs/{lab["id"]}/render?'+urlencode({"query":"hello"}),
                    "payload":None})
            if lab["category"]=="permissions":history.append(text)
    cases.append({"id":"catalog","group":"metadata","method":"GET","path":"/labs","payload":None})
    for label,text in [("ascii","a"*2000),("korean","박"*2000),("astral","😀"*2000)]:
        for action in ("analyze","attempt"):
            cases.append({"id":"boundary-"+label+"/"+action,"group":"boundary","method":"POST",
                "path":"/labs/sql-injection-easy/"+action,"payload":{"username":text}})
    heavy="' OR (WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<10000) SELECT sum(x) FROM n)>0--"
    for action in ("analyze","attempt"):
        cases.append({"id":"bounded-recursive/"+action,"group":"bounded-sql","method":"POST",
            "path":"/labs/sql-injection-easy/"+action,"payload":{"username":heavy}})
    return catalog,cases


def percentile(values,p):
    return sorted(values)[max(0,math.ceil(p*len(values))-1)]


def profile(concurrency,cases,admission=False):
    creation=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0
    command=[sys.executable,"-X","utf8",str(Path(__file__).resolve()),"--serve"]
    if admission:
        command += ["--admission-budget",str(len(cases)*3+3),"--admission-active",str(concurrency)]
    proc=subprocess.Popen(command,
        cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",
        creationflags=creation)
    port=None
    try:
        ready=proc.stdout.readline()
        if not ready:raise RuntimeError("isolated server did not announce readiness")
        port=json.loads(ready)["port"]
        probe={"id":"snapshot","group":"probe","method":"GET","path":"/_profile","payload":None}
        deadline=time.monotonic()+10
        while True:
            try:
                conn=http.client.HTTPConnection("127.0.0.1",port,timeout=1)
                conn.request("GET","/_profile");r=conn.getresponse()
                before=json.loads(r.read());conn.close();break
            except (OSError,http.client.HTTPException):
                if time.monotonic()>deadline:raise
                time.sleep(.02)
        # Warm the actual route separately; not a measured corpus sample.
        for _ in range(3):exchange(port,cases[0])
        def snapshot():
            conn=http.client.HTTPConnection("127.0.0.1",port,timeout=3)
            try:
                conn.request("GET","/_profile");r=conn.getresponse();return json.loads(r.read())
            finally:conn.close()
        before=snapshot()
        start=time.perf_counter()
        jobs=[{**case,"repeat":repeat} for repeat in range(3) for case in cases]
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            samples=list(pool.map(lambda case:exchange(port,case),jobs))
        duration=time.perf_counter()-start
        after=snapshot()
        assert all(s["status"]==200 for s in samples),"unexpected HTTP response"
        assert after["active"]==0
        return {"requested_clients":concurrency,"request_count":len(samples),
            "admission_enabled":admission,"admission_batch_budget":len(cases)*3+3 if admission else None,
            "elapsed_seconds":duration,"server_cpu_seconds":after["cpu_seconds"]-before["cpu_seconds"],
            "baseline":before,"after":after,"samples":samples,
            "observed_latency_ms":{"median":percentile([s["elapsed_ms"] for s in samples],.5),
                "p95_sample":percentile([s["elapsed_ms"] for s in samples],.95),
                "max":max(s["elapsed_ms"] for s in samples)}}
    finally:
        if port is not None:
            try:
                conn=http.client.HTTPConnection("127.0.0.1",port,timeout=1)
                conn.request("GET","/_stop");conn.getresponse().read();conn.close()
            except (OSError,http.client.HTTPException):pass
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate();proc.wait(timeout=3)
        if proc.stdout:proc.stdout.close()
        if proc.stderr:proc.stderr.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve",action="store_true")
    parser.add_argument("--with-admission",action="store_true")
    parser.add_argument("--admission-budget",type=int,default=0)
    parser.add_argument("--admission-active",type=int,default=0)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if args.serve:return serve(args.admission_budget,args.admission_active)
    if args.output is None:parser.error("--output required")
    output=args.output.resolve()
    if not output.is_relative_to(ROOT.resolve()):parser.error("output must stay in repo")
    catalog,cases=build_cases()
    result={"scope":"small bounded loopback corpus; no production policy/capacity guarantee",
        "head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "environment":{"python":sys.version,"platform":platform.platform(),
            "host_logical_cpus":os.cpu_count(),"docker_cpu_quota_applied":False,
            "packages":{k:importlib.metadata.version(k) for k in ["uvicorn","fastapi","starlette","anyio"]}},
        "admission_enabled":args.with_admission,
        "labs":len(catalog),"guide_steps":sum(len(l["lesson"]["steps"]) for l in catalog),
        "cases":cases,"profiles":[]}
    for concurrency in (1,2,4,8):
        data=profile(concurrency,cases,args.with_admission)
        result["profiles"].append(data)
        print(json.dumps({"clients":concurrency,"requests":data["request_count"],
            "server_cpu_seconds":data["server_cpu_seconds"],"latency_ms":data["observed_latency_ms"]}),flush=True)
    source_files=["frontend/src/lesson-catalog.js","frontend/src/useInputAnalysis.js",
        "backend/app/review_app.py","backend/app/core/admission.py",
        "backend/app/core/admission_guard.py","backend/app/core/sql_limits.py","docker-compose.yml",str(Path(__file__).relative_to(ROOT))]
    result["source_sha256"]={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_files}
    result["total_measured_requests"]=sum(p["request_count"] for p in result["profiles"])
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(output.relative_to(ROOT)),"total":result["total_measured_requests"]}),flush=True)


if __name__=="__main__":main()