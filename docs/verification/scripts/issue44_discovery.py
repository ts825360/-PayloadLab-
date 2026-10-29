"""#44 stage-1 discovery only: bounded loopback requests and proxy observation.

Does not change the product app, install a limiter, or choose production values.
Run from the repository root; output is explicit and local.
"""
import argparse
import contextlib
import hashlib
import http.client
import importlib.metadata
import json
import platform
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
import uvicorn
from fastapi import FastAPI
from app.main import app as product_app

SOURCE_PATHS = [
    "backend/app/main.py", "backend/app/routes/labs.py",
    "frontend/src/useInputAnalysis.js", "frontend/src/App.jsx",
    "frontend/src/api.js", "frontend/vite.config.js", "docker-compose.yml",
    "backend/app/core/lab_paths.py",
]


async def observed_app(scope, receive, send):
    # Diagnostic endpoint exists only in this in-memory wrapper.
    if scope["type"] == "http" and scope["path"].endswith("/_issue44_peer"):
        body = json.dumps({"client": scope.get("client")}).encode()
        await send({"type": "http.response.start", "status": 200,
                    "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": body})
    else:
        await product_app(scope, receive, send)


@contextlib.contextmanager
def server(proxy_headers, trusted):
    dual = FastAPI()
    dual.mount("/api", observed_app)
    dual.mount("/", observed_app)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    address = sock.getsockname()
    runner = uvicorn.Server(uvicorn.Config(
        dual, log_level="error", access_log=False, lifespan="off", ws="none",
        proxy_headers=proxy_headers, forwarded_allow_ips=trusted,
    ))
    thread = threading.Thread(target=runner.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        end = time.monotonic() + 5
        while not runner.started:
            if not thread.is_alive() or time.monotonic() >= end:
                raise RuntimeError("loopback probe server did not start")
            time.sleep(.01)
        yield address
    finally:
        runner.should_exit = True
        thread.join(5)
        sock.close()
        if thread.is_alive():
            raise RuntimeError("probe server did not stop")


def request(address, method, path, payload=None, headers=None):
    conn = http.client.HTTPConnection(*address, timeout=5)
    raw = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    started = time.perf_counter()
    try:
        conn.request(method, path, raw, {"Content-Type": "application/json", **(headers or {})})
        response = conn.getresponse()
        body = response.read()
        return {"status": response.status, "bytes": len(body),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 4),
                "retry_after": response.getheader("Retry-After")}, body
    finally:
        conn.close()


def debounced_count(interval_ms, count, delay_ms):
    # Timer model only; not measured human traffic or actual React rendering.
    times = [n * interval_ms for n in range(count)]
    return sum(1 for n, t in enumerate(times)
               if n == len(times)-1 or times[n+1] - t > delay_ms)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT.resolve()):
        parser.error("output must stay inside this repository")

    cases = []
    for category, field, value, levels in [
        ("sql-injection", "username", "guest", ("easy", "medium")),
        ("reflected-xss", "query", "hello", ("easy", "medium")),
        ("idor", "requested_id", 1042, ("easy", "medium")),
        ("ssrf", "target_url", "https://example.com/news", ("easy", "medium")),
        ("command-injection", "hostname", "example.com", ("easy", "medium")),
        ("linux-basics", "command", "ls", ("easy", "medium")),
        ("permissions", "command", "whoami", ("easy",)),
    ]:
        for level in levels:
            payload = {field: value}
            if category == "idor" and level == "medium":
                payload["claimed_user_id"] = 1042
            if category == "permissions":
                payload["history"] = []
            for action in ("analyze", "attempt"):
                cases.append(("POST", f"/labs/{category}-{level}/{action}", payload))
    for level in ("easy", "medium"):
        cases.append(("GET", f"/labs/reflected-xss-{level}/render?" + urlencode({"query": "hello"}), None))
    cases += [("GET", "/health", None), ("GET", "/labs", None)]

    results, proxy_results, mounted = [], [], []
    profiles = [
        ("loopback-trusted", True, "127.0.0.1"),
        ("proxy-disabled", False, "127.0.0.1"),
        ("loopback-not-trusted", True, "192.0.2.10"),
    ]
    variants = [
        ("plain", {}, "127.0.0.1"),
        ("xff-a", {"X-Forwarded-For": "198.51.100.10"}, "198.51.100.10"),
        ("xff-b", {"X-Forwarded-For": "198.51.100.11"}, "198.51.100.11"),
        ("forwarded-only", {"Forwarded": "for=198.51.100.12"}, "127.0.0.1"),
    ]
    for profile, enabled, trusted in profiles:
        with server(enabled, trusted) as address:
            if profile == "loopback-trusted":
                for method, path, payload in cases:
                    samples = []
                    for _ in range(3):
                        result, body = request(address, method, path, payload)
                        assert result["status"] == 200, (path, result, body[:200])
                        samples.append(result)
                    results.append({"method": method, "path": path, "input": payload, "samples": samples})
                for _ in range(3):
                    result, _body = request(address, "POST",
                        "/api/labs/sql-injection-easy/analyze", {"username": "guest"})
                    assert result["status"] == 200
                    mounted.append(result)
            for prefix in ("", "/api"):
                for variant, headers, forwarded in variants:
                    result, body = request(address, "GET", prefix + "/_issue44_peer", headers=headers)
                    peer = json.loads(body)["client"][0]
                    expected = forwarded if profile == "loopback-trusted" else "127.0.0.1"
                    assert result["status"] == 200 and peer == expected, (profile, variant, peer)
                    proxy_results.append({"profile": profile, "path_prefix": prefix,
                                          "headers_case": variant, "expected_peer": expected,
                                          "actual_peer": peer, **result})
    actual_config = uvicorn.Config("app.main:app")
    result = {
        "scope": "small sequential loopback HTTP discovery; no app rate policy, no capacity/load claim",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "packages": {k: importlib.metadata.version(k) for k in ("uvicorn","fastapi","starlette","anyio")},
                        "uvicorn_defaults_this_environment": {
                            "proxy_headers": actual_config.proxy_headers,
                            "forwarded_allow_ips": actual_config.forwarded_allow_ips,
                            "workers": actual_config.workers,
                            "limit_concurrency": actual_config.limit_concurrency,
                        }},
        "source_sha256": {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCE_PATHS},
        "cases": results, "mounted_sql": mounted, "proxy_observations": proxy_results,
        "timer_model": {"input_changes": 25, "delay_ms": 320,
                        "spacing_100ms_requests": debounced_count(100,25,320),
                        "spacing_400ms_requests": debounced_count(400,25,320),
                        "kind": "synthetic timer arithmetic, not actual browser/human telemetry"},
        "total_http_requests": len(cases)*3 + len(mounted) + len(proxy_results),
        "remaining": ["multi-worker aggregate", "concurrency/queue/cancellation",
                      "real proxy/container/origin enforcement", "school NAT workload",
                      "approved rates and timeouts", "user-facing retry UI"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"output": str(output.relative_to(ROOT)),
                      "http_requests": result["total_http_requests"],
                      "route_cases": len(cases), "proxy_checks": len(proxy_results),
                      "timer_model": result["timer_model"],
                      "status": "all expected observations matched"}, ensure_ascii=False))


if __name__ == "__main__":
    main()