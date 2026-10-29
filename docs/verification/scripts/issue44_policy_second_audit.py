"""Independent #44 policy audit: arithmetic and counterexample sensitivity.

Virtual-time experiments only. Does not approve N or enable a product policy.
"""
from decimal import Decimal,ROUND_CEILING
import hashlib
import heapq
import itertools
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"backend"))
from app.core.admission import AdmissionController,AdmissionPolicy,AdmissionRejected,Rate


class Clock:
    milliseconds=0
    def __call__(self):return self.milliseconds/1000


def control(n,multiplier,clock,total_burst=None):
    return AdmissionController(AdmissionPolicy(
        Rate(total_burst if total_burst is not None else 4*n,13*n),
        {a:Rate(n,n if a=="metadata" else 4*n) for a in ("metadata","analyze","attempt","render")},
        None,multiplier*n,{a:n for a in ("metadata","analyze","attempt","render")},1),clock=clock)


def sensitivity(n,multiplier,hold):
    clock=Clock();c=control(n,multiplier,clock)
    events=[];seq=itertools.count()
    def add(t,kind,content):heapq.heappush(events,(t,kind,next(seq),content))
    for user in range(n):
        add(0,1,("metadata",user,False))
        for k in range(10):
            t=(k+1)*320
            add(t,1,("analyze",user,False))
            add(t,1,("attempt",user,True))
    accepted=0;denied=[];peak=0
    while events:
        t,kind,_,content=heapq.heappop(events);clock.milliseconds=t
        if kind==0:
            content.release();continue
        action,user,preview=content
        try:lease=c.acquire(action,f"192.0.2.{user+1}")
        except AdmissionRejected as error:
            denied.append({"at_ms":t,"action":action,"code":error.code})
        else:
            accepted+=1;peak=max(peak,c.snapshot()["active"])
            add(t+hold,0,lease)
            # Render only after an admitted attempt completes; a denied
            # attempt cannot create a fictional successful preview.
            if preview:add(t+hold,1,("render",user,False))
    assert c.snapshot()["active"]==0
    return {"n":n,"active_multiplier":multiplier,"per_request_hold_ms":hold,
        "admitted":accepted,"denied":len(denied),"first_denials":denied[:4],
        "scheduled_requests":accepted+len(denied),
        "skipped_previews_if_attempt_denied":sum(x["action"]=="attempt" for x in denied),
        "peak_active":peak,"remaining_slots":c.snapshot()["active"],
        "kind":"integer-ms virtual timeline; not HTTP/user capacity"}


def isolated_global(n):
    clock=Clock();tight=control(n,3,clock,total_burst=n)
    wide=control(n,3,Clock(),total_burst=4*n)
    for c in (tight,wide):
        for user in range(n):
            c.acquire("analyze",f"192.0.2.{user+1}").release()
    try:tight.acquire("attempt","203.0.113.1")
    except AdmissionRejected as error:assert error.code=="rate_limit"
    else:raise AssertionError("common bucket did not reject")
    wide.acquire("attempt","203.0.113.1").release()
    return {"n":n,"tight_total_burst":n,"wide_total_burst":4*n,
        "same_action_allowance":"attempt still unused in both",
        "tight_attempt":"rate_limit","wide_attempt":"admitted"}


def main():
    p=ROOT/"docs/verification/evidence/2026-10-29-issue44-policy-with-admission.json"
    d=json.loads(p.read_text(encoding="utf-8"))
    averages=[];rows=[]
    for profile in d["profiles"]:
        samples=profile["samples"]
        assert len(samples)==204 and all(x["status"]==200 for x in samples)
        values=sorted(Decimal(str(x["elapsed_ms"])) for x in samples)
        p95=values[int((Decimal(".95")*len(values)).to_integral_value(rounding=ROUND_CEILING))-1]
        assert abs(p95-Decimal(str(profile["observed_latency_ms"]["p95_sample"])))<Decimal("1e-9")
        median=values[(len(values)+1)//2-1]
        assert abs(median-Decimal(str(profile["observed_latency_ms"]["median"])))<Decimal("1e-9")
        assert abs(values[-1]-Decimal(str(profile["observed_latency_ms"]["max"])))<Decimal("1e-9")
        assert profile["after"]["memory"]["peak_working_set"]>=profile["after"]["memory"]["working_set"]
        cpu=Decimal(str(profile["server_cpu_seconds"]))*1000/Decimal(len(samples))
        averages.append(cpu)
        rows.append({"clients":profile["requested_clients"],"requests":len(samples),
                     "cpu_ms_per_request_decimal":str(cpu),"p95_from_raw":str(p95)})
    cpu=max(averages)
    original=json.loads((ROOT/"docs/verification/evidence/2026-10-29-issue44-policy-replay.json").read_text(encoding="utf-8"))
    for row in original["comparisons"]:
        expected=Decimal(13*row["n_example_only"])*cpu/1000
        assert abs(expected-Decimal(str(row["planning_cpu_fraction_of_one_core"])))<Decimal("1e-12")
        n=row["n_example_only"]
        assert row["total_rate_per_second"]==3*row["action_rate_per_second"]+row["metadata_rate_per_second"]==13*n
        assert row["total_burst"]==4*row["action_burst"]==4*n
    findings=[sensitivity(n,m,s) for n in (1,4,8,16) for m in (2,3)
              for s in (133,160,161,200,320,321)]
    for n in (1,4,8,16):
        select=lambda m,s:next(x for x in findings if x["n"]==n and x["active_multiplier"]==m and x["per_request_hold_ms"]==s)
        assert select(2,161)["denied"]>0
        assert all(select(3,s)["denied"]==0 for s in (133,160,161,200,320))
        assert select(3,321)["denied"]>0
    result={"state":"independent draft audit; no capacity guarantee",
        "measurement_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
        "arithmetic_profiles":rows,"max_profile_mean_cpu_ms_decimal":str(cpu),
        "sensitivity_scenarios":findings,"isolated_global_controls":[isolated_global(n) for n in (1,4,8,16)],
        "findings":["2N can reject below 320ms goal when a previous preview overlaps next analysis/attempt",
                    "3N model admits <=320ms per request under this integer-time, one-tab interaction model",
                    "at 321ms the per-action cap still rejects; no overload guarantee",
                    "13N/4N totals equal sum of action quotas; original overflow did not isolate total"],
        "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out=ROOT/"docs/verification/evidence/2026-10-29-issue44-policy-second-audit.json"
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"arithmetic":"PASS","scenarios":len(findings),
        "global_controls":4,"N1_2N_161ms":next(x for x in findings if x["n"]==1 and x["active_multiplier"]==2 and x["per_request_hold_ms"]==161),
        "N1_3N_320ms":next(x for x in findings if x["n"]==1 and x["active_multiplier"]==3 and x["per_request_hold_ms"]==320)},ensure_ascii=False))


if __name__=="__main__":main()