"""Small local mechanism test; no production policy or external targets."""
import json
import platform
import sqlite3
import subprocess
import time

calls = 0
conn = sqlite3.connect(":memory:")
started = time.monotonic()

def progress():
    global calls
    calls += 1
    return int(calls >= 10)

conn.set_progress_handler(progress, 100)
interrupted = False
try:
    conn.execute("WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<10000) SELECT sum(x) FROM n").fetchone()
except sqlite3.OperationalError as error:
    interrupted = str(error) == "interrupted"
finally:
    conn.set_progress_handler(None, 0)
    conn.close()
closed = False
try:
    conn.execute("SELECT 1")
except sqlite3.ProgrammingError:
    closed = True
recovery = sqlite3.connect(":memory:")
try:
    normal = recovery.execute("SELECT 1").fetchone() == (1,)
finally:
    recovery.close()
assert interrupted and closed and normal
print(json.dumps(dict(main_sha=subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip(), python=platform.python_version(), sqlite=sqlite3.sqlite_version, callbacks=calls, test_budget_instructions=1000, interrupted=interrupted, closed=closed, next_connection_ok=normal, elapsed_ms=round((time.monotonic()-started)*1000, 2), scope="mechanism only; production routes and policy not modified"), indent=2))
