import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

DOCKER_IMAGE = os.getenv("JUDGE_PY_IMAGE", "python:3.11-slim")

RUNNER_CODE = r"""
import json, time, traceback

# user code injected below
USER_CODE

def _run_one(args):
    start = time.perf_counter()
    try:
        # args is a list/tuple of positional args
        out = solution(*args)
        ok = True
        err = None
    except Exception as e:
        out = None
        ok = False
        err = traceback.format_exc(limit=5)
    end = time.perf_counter()
    return ok, out, int((end - start) * 1000), err

def main():
    payload = json.load(open("payload.json", "r"))
    tests = payload["tests"]
    results = []
    total = 0

    for i, t in enumerate(tests):
        args = t["args"]
        expected = t["expected"]
        ok, out, ms, err = _run_one(args)
        total += ms

        passed = ok and out == expected
        results.append({
            "index": i,
            "passed": passed,
            "actual_json": json.dumps(out),
            "expected_json": json.dumps(expected),
            "runtime_ms": ms,
            "error": err if err and not passed else None
        })

    print(json.dumps({"tests": results, "total_runtime_ms": total}))
if __name__ == "__main__":
    main()
"""

def run_python_in_docker(user_code: str, tests: List[Dict[str, Any]], timeout_s: int = 3) -> Dict[str, Any]:
    """
    tests: [{ "args": [...], "expected": ... }]
    returns parsed JSON from runner stdout
    """
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)

        # Write payload
        (work / "payload.json").write_text(json.dumps({"tests": tests}), encoding="utf-8")

        # Inject user code
        runner = RUNNER_CODE.replace("USER_CODE", user_code)
        (work / "runner.py").write_text(runner, encoding="utf-8")

        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--read-only",
            "--pids-limit", "64",
            "--cpus", "1",
            "--memory", "256m",
            "-v", f"{work}:/work:rw",
            "-w", "/work",
            DOCKER_IMAGE,
            "python", "runner.py"
        ]

        start = time.perf_counter()
        try:
            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s
            )
        except subprocess.TimeoutExpired:
            return {"tests": [], "total_runtime_ms": int((time.perf_counter() - start) * 1000), "error": "timeout"}

        if p.returncode != 0:
            return {"tests": [], "total_runtime_ms": int((time.perf_counter() - start) * 1000), "error": p.stderr.strip()[:2000]}

        # stdout is JSON
        out = p.stdout.strip().splitlines()[-1]
        return json.loads(out)