import json
import os
import random
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from app.models_execute import ExecuteRequest, ExecuteResponse
from app.judge import run_python_subprocess
from app.store import RoomStore, get_problem as store_get_problem

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "https://sre-lc-gamified-tool.vercel.app",
        "https://sre-lc-gamified-tool.fly.dev"
    ],
    allow_origin_regex=r"https://sre-lc-gamified-tool*\.vercel\.app",
    allow_credentials=False,
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

room_store = RoomStore(get_problem_payload=get_problem_payload)

async def get_room_or_404(room_id: str) -> dict:
    try:
        return await room_store.get_state(room_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")

def load_problems():
    path = os.getenv("PROBLEMS_PATH", "problems.json")
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Problems file not found at {path}")
    
class CreateRoomResponse(BaseModel):
    room_id: str

class JoinRoomRequest(BaseModel):
    name: str

class JoinRoomResponse(BaseModel):
    room_id: str
    player_id: str
    ws_url: str


class SelectProblemRequest(BaseModel):
    player_id: str
    problem_id: str


# --- Adding new endpoints for rooms and websockets ---
@app.post("/rooms", response_model=CreateRoomResponse)
async def create_room():
    room_id = await room_store.create_room()
    return CreateRoomResponse(room_id=room_id)

@app.post("/rooms/{room_id}/join", response_model=JoinRoomResponse)
async def join_room(room_id: str, req: JoinRoomRequest):
    try:
        player_id = await room_store.join_room(room_id, req.name)
    except ValueError as e:
        # Convert ValueError to proper HTTP error
        if "Room not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "Room is full" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    
    ws_url = f"/ws/{room_id}?player_id={player_id}"
    return JoinRoomResponse(room_id=room_id, player_id=player_id, ws_url=ws_url)

@app.get("/rooms/{room_id}")
async def get_room_state(room_id: str):
    return await get_room_or_404(room_id)


@app.post("/rooms/{room_id}/problem")
async def select_problem(room_id: str, req: SelectProblemRequest):
    """Set the room's current problem. Validates problem exists; returns updated room state."""
    if store_get_problem(req.problem_id) is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    try:
        await room_store.select_problem(room_id, req.player_id, req.problem_id)
    except ValueError as e:
        msg = str(e)
        code = 403 if "creator" in msg else 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg)
    return await get_room_or_404(room_id)


@app.websocket("/ws/{room_id}")
async def ws_room(ws: WebSocket, room_id: str, player_id: str):
    await ws.accept()
    try:
        await room_store.connect_ws(room_id, player_id, ws)
        while True:
            await ws.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        await room_store.disconnect_ws(room_id, player_id)




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
    # load_problems() reads PROBLEMS_PATH so tests can override the fixture
    p = next((p for p in load_problems() if p["id"] == req.problem_id), None)
    if p is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    baseline = p["baseline_ms"]
    delta = req.user_time_ms - baseline
    result = "win" if delta < 0 else "draw" if delta == 0 else "loss"
    return {"result": result, "problem_id": req.problem_id, "baseline_ms": baseline, "delta_ms": delta}

@app.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest):
    if req.language != "python":
        raise HTTPException(status_code=400, detail="Only python supported")

    if "def solution" not in req.code:
        raise HTTPException(status_code=400, detail="Code must define def solution(...):")

    problem = store_get_problem(req.problem_id)
    if problem is None:
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

