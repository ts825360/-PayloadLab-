"""Replay proposed #44 formulas against current admission primitives.

Virtual-time policy exercise only; not HTTP/load/user telemetry or approval.
Learner count remains a team-lead decision. All N rows are comparisons.
"""
import argparse
import hashlib
import heapq
import itertools
import json
import math
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"backend"))
from app.core.admission import AdmissionController,AdmissionPolicy,AdmissionRejected,Rate


class Clock:
    now=0.0
    def __call__(self):return self.now


def make_controller(n,clock,debounce_ms):
    cadence=math.ceil(1000/debounce_ms)
    # Peer disabled: school NAT must not be interpreted as one authenticated user.
    # max_peers=1 is an unused positive constructor placeholder; zero peers tracked.
    return AdmissionController(AdmissionPolicy(
        total_rate=Rate(4*n,(3*cadence+1)*n),
        action_rates={a:Rate(n, cadence*n if a!="metadata" else n)
                      for a in ("analyze","attempt","render","metadata")},
        peer_rate=None,max_active=2*n,
        action_active={a:n for a in ("analyze","attempt","render","metadata")},
        max_peers=1),clock=clock)


def replay(n,steps,render_keys,debounce_ms,hold_ms,shared_peer,all_preview=False):
    clock=Clock();c=make_controller(n,clock,debounce_ms)
    queue=[];seq=itertools.count()
    def add(t,kind,value):heapq.heappush(queue,(t,kind,next(seq),value))
    for user in range(n):
        peer="192.0.2.1" if shared_peer else f"192.0.2.{user+1}"
        add(0,1,("metadata",peer))
        for index,key in enumerate(steps):
            start=(index+1)*debounce_ms/1000
            add(start,1,("analyze",peer));add(start,1,("attempt",peer))
            if all_preview or key in render_keys:
                add(start+hold_ms/1000,1,("render",peer))
    accepted=0;rejected=[];peak=0
    while queue:
        t,kind,_,value=heapq.heappop(queue);clock.now=t
        if kind==0:
            value.release();continue
        action,peer=value
        try:lease=c.acquire(action,peer)
        except AdmissionRejected as error:
            rejected.append({"at":t,"action":action,"code":error.code})
        else:
            accepted+=1;peak=max(peak,c.snapshot()["active"])
            add(t+hold_ms/1000,0,lease)
    assert c.snapshot()["active"]==0 and c.snapshot()["tracked_peers"]==0
    assert rejected==[],rejected[:5]
    return {"n":n,"shared_peer":shared_peer,"all_steps_preview_model":all_preview,
        "accepted":accepted,"rejected":len(rejected),"peak_active":peak,
        "hold_ms":hold_ms,"clock":"virtual; not observed human timing",
        "capacity_validation":False}


def check_overflow(n,debounce_ms):
    c=make_controller(n,Clock(),debounce_ms)
    for action in ("metadata","analyze","attempt","render"):
        for i in range(n):
            lease=c.acquire(action,f"192.0.2.{i+1}");lease.release()
    try:c.acquire("attempt","203.0.113.10")
    except AdmissionRejected as error:assert error.code=="rate_limit"
    else:raise AssertionError("changed peer bypassed total burst")
    busy=make_controller(n,Clock(),debounce_ms)
    leases=[busy.acquire(a,"192.0.2.1") for a in ("analyze","attempt") for _ in range(n)]
    try:
        try:busy.acquire("render","203.0.113.10")
        except AdmissionRejected as error:assert error.code=="concurrency_limit"
        else:raise AssertionError("active cap not enforced")
    finally:
        for lease in leases:lease.release()
    busy.acquire("render","192.0.2.1").release()
    return {"n":n,"total_burst_admitted":4*n,"next_peer_changed":"rate_limit",
        "held_active":2*n,"next_active":"concurrency_limit","recovered":True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurement",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    measurement=json.loads(args.measurement.read_text(encoding="utf-8"))
    source=(ROOT/"frontend/src/useInputAnalysis.js").read_text(encoding="utf-8")
    match=re.search(r"},\s*(\d+)\);\s*return",source)
    assert match,"debounce source changed; inspect before deriving policy"
    debounce=int(match[1])
    cadence=math.ceil(1000/debounce)
    hold=math.ceil(max(p["observed_latency_ms"]["max"] for p in measurement["profiles"]))
    cpu_ms=max(1000*p["server_cpu_seconds"]/p["request_count"] for p in measurement["profiles"])
    max_clients=max(p["requested_clients"] for p in measurement["profiles"])
    assert 2*hold<debounce,"measured two-response model no longer fits one interaction cycle"
    steps=list(dict.fromkeys(c["id"].rsplit("/",1)[0] for c in measurement["cases"] if c["group"]=="actual-guide"))
    render_keys={c["id"].rsplit("/",1)[0] for c in measurement["cases"] if c["group"]=="render-plain"}
    assert len(steps)==27 and len(render_keys)==5
    rows=[];replays=[];overflows=[]
    for n in (1,4,8,16):
        total_rate=(3*cadence+1)*n
        cpu_fraction=total_rate*cpu_ms/1000
        rows.append({"n_example_only":n,"total_rate_per_second":total_rate,
            "total_burst":4*n,"action_rate_per_second":cadence*n,
            "action_burst":n,"metadata_rate_per_second":n,"active_total":2*n,
            "active_each_action":n,"queue_length":0,
            "planning_cpu_fraction_of_one_core":cpu_fraction,
            "within_observed_concurrency":2*n<=max_clients,
            "within_proposed_half_core_headroom":cpu_fraction<=.5,
            "approval":"not selected; not a capacity guarantee"})
        replays.append(replay(n,steps,render_keys,debounce,hold,True))
        replays.append(replay(n,steps,render_keys,debounce,hold,False))
        replays.append(replay(n,steps,render_keys,debounce,hold,True,True))
        overflows.append(check_overflow(n,debounce))
    result={"state":"DRAFT; N chosen by team lead; no main activation",
        "facts":{"debounce_ms":debounce,"guide_steps":len(steps),
            "preview_steps":len(render_keys),"measured_max_ms":hold,
            "max_profile_average_server_cpu_ms":cpu_ms,"profile_clients_max":max_clients},
        "policy_choices":{"cadence_per_learner_rounded_up":cadence,
            "metadata_reconnect_goal_per_learner_per_second":1,
            "global_rate_formula":"N*(3*ceil(1000/debounce_ms)+1)",
            "global_burst_formula":"4*N","max_active_formula":"2*N",
            "each_action_active_formula":"N","queue_length":0,
            "cpu_headroom_review_line":.5,"peer_rate":None,
            "response_target_ms":debounce,"hard_body_and_total_timeout":"not selected/not implemented"},
        "comparisons":rows,"replays":replays,"overflow_checks":overflows,
        "source_sha256":{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [
            "backend/app/core/admission.py","frontend/src/useInputAnalysis.js",
            str(Path(__file__).resolve().relative_to(ROOT))]},
        "measurement_sha256":hashlib.sha256(args.measurement.read_bytes()).hexdigest()}
    output=args.output.resolve()
    assert output.is_relative_to(ROOT.resolve())
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"replays":len(replays),"replayed_admissions":sum(x["accepted"] for x in replays),
        "overflows":len(overflows),"cpu_ms_used":cpu_ms,"comparisons":rows},ensure_ascii=False))


if __name__=="__main__":main()