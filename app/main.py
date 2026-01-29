import json
import os
import random
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from app.models_execute import ExecuteRequest, ExecuteResponse
from app.judge import run_python_subprocess
from app.store import RoomStore

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

room_store = RoomStore(get_problem_payload=get_problem_payload)

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
    
# --- Adding new endpoints for rooms and websockets ---
@app.post("/rooms", response_model=CreateRoomResponse)
async def create_room():
    room_id = await room_store.create_room()
    return CreateRoomResponse(room_id=room_id)

@app.post("/rooms/{room_id}/join", response_model=JoinRoomResponse)
async def join_room(room_id: str, req: JoinRoomRequest):
    player_id, ws_url = await room_store.join_room(room_id, req.name)
    return JoinRoomResponse(room_id=room_id, player_id=player_id, ws_url=f"/ws/{room_id}?player_id={player_id}")

@app.get("/rooms/{room_id}")
async def get_room_state(room_id: str):
    return await room_store.get_state(room_id)

@app.websocket("/ws/{room_id}")
async def ws_room(ws: WebSocket, room_id: str, player_id: str):
    await ws.accept()
    try:
        await room_store.connect_ws(room_id, player_id, ws)
        while True:
            raw = await ws.receive_text()  # Keep the connection open
            message = json.loads(raw)
            resp = await room_store.handle_client_message(room_id, player_id, message)
            if resp is not None:
                await ws.send_json(resp)
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

