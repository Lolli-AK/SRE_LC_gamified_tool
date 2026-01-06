import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

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
        if p["id"] == problem_id:
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)