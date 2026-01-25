import json
import os
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from app.models_execute import ExecuteRequest, ExecuteResponse
from app.judge import run_python_subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,  # keep false unless you use cookies/auth
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

def get_problem_payload(problem_id: str | None = None) -> dict:
    problems = load_problems()

    if problem_id is None:
        p = random.choice(problems)
    else:
        p = next((p for p in problems if p["id"] == problem_id), None)
        if p is None:
            raise HTTPException(status_code=404, detail="Problem not found")
    return p

def load_problems():
    path = os.getenv("PROBLEMS_PATH", "problems.json")
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Problems file not found at {path}")



@app.get("/problems")
def list_problems():
    return load_problems()

@app.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    problems = load_problems()
    for p in problems:
        if p.get("id") == problem_id:
            return p
    raise HTTPException(status_code=404, detail="Problem not found")

class RaceRequest(BaseModel):
    problem_id: str
    user_time_ms: int = Field(gt=0)


class RaceResponse(BaseModel):
    result: Literal["win", "loss", "draw"]
    problem_id: str
    baseline_ms: int
    delta_ms: int


@app.post("/race", response_model=RaceResponse)
def race(req: RaceRequest):
    problems = load_problems()
    for p in problems:
        if p["id"] == req.problem_id:
            baseline = p["baseline_ms"]
            delta = req.user_time_ms - baseline

            if delta < 0:
                result = "win"
            elif delta == 0:
                result = "draw"
            else:
                result = "loss"

            return {
                "result": result,
                "problem_id": req.problem_id,
                "baseline_ms": baseline,
                "delta_ms": delta,
            }

    raise HTTPException(status_code=404, detail="Problem not found")

@app.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest):
    if req.language != "python":
        raise HTTPException(status_code=400, detail="Only python supported")

    if "def solution" not in req.code:
        raise HTTPException(status_code=400, detail="Code must define def solution(...):")

    problem = get_problem(req.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    samples = problem.get("samples", [])
    if not samples:
        raise HTTPException(status_code=400, detail="No samples configured for this problem")

    tests = []
    for s in samples:
        try:
            args = json.loads(s["args_json"])
            expected = json.loads(s["expected_json"])
        except Exception:
            raise HTTPException(status_code=500, detail="Invalid sample JSON format")

        if not isinstance(args, list):
            raise HTTPException(status_code=500, detail="args_json must be a JSON list of positional args")

        tests.append({"args": args, "expected": expected})

    result = run_python_subprocess(user_code=req.code, tests=tests, timeout_s=3)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result

'''	•	POST /rooms
	•	POST /rooms/{room_id}/join
	•	GET /rooms/{room_id}
	•	WS /ws/{room_id}
'''

