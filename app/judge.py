import json
import os
import subprocess
import tempfile
import textwrap
from typing import List, Dict

def run_python_subprocess(user_code: str, tests: List[dict], timeout_s: int = 3):
    """
    Runs ALL tests in one python process inside the backend container.
    Returns a dict matching ExecuteResponse.
    """
    harness = f"""
import json, time, traceback

{user_code}

tests = json.loads({json.dumps(json.dumps(tests))})
out_tests = []
total_start = time.perf_counter()

for i, t in enumerate(tests):
    start = time.perf_counter()
    try:
        actual = solution(*t["args"])
        passed = actual == t["expected"]
        err = None
    except Exception as e:
        actual = None
        passed = False
        err = traceback.format_exc()
        
    runtime_ms = int((time.perf_counter() - start) * 1000)
    out_tests.append({{
        "index": i,
        "passed": passed,
        "actual_json": json.dumps(actual),
        "expected_json": json.dumps(t["expected"]),
        "runtime_ms": runtime_ms,
        "error": err
    }})
total_runtime_ms = int((time.perf_counter() - total_start) * 1000)

print(json.dumps({{
    "tests": out_tests,
    "total_runtime_ms": total_runtime_ms
}}))
"""
    with tempfile.TemporaryDirectory() as d:
        fp = os.path.join(d, "run.py")
        with open (fp, "w", encoding="utf-8") as f:
            f.write(harness)
        try:
            p = subprocess.run(
                ["python3", fp],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return {"error" : f"timed out after {timeout_s}s"}
        
        if p.returncode != 0:
            print("this code is running before the error hits")
            # error the code the user has written
            msg = (p.stderr or p.stdout).strip()[:2000]  # cap length
            return {"error": msg or f"subprocess exited with code {p.returncode}", "stderr": p.stderr}
        try:
            # another check for faulty user code
            return json.loads(p.stdout)
        except Exception:
            return {"error": "failed to parse runner output", "stdout": p.stdout, "stderr": p.stderr}
