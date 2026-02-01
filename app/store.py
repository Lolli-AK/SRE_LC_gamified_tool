from __future__ import annotations
import json, asyncio, time, uuid
from dataclasses import dataclass, field
from pathlib import Path
from fastapi import WebSocket
from typing import Any, Dict, List, Optional, Callable

def _new_id() -> str:
    return uuid.uuid4().hex

@dataclass
class Player:
    player_id: str
    name: str
    ws: Optional[WebSocket] = None
    joined_at: float = field(default_factory=time.time) # generate a time stamp for a new instance

@dataclass
class Room:
    room_id: str
    players: Dict[str, Player] = field(default_factory=dict)
    status: str = "waiting" # waiting|ready|running|done
    created_at: float = field(default_factory=time.time)


class RoomStore:
    '''
    In memory room manager (MVP)
    swap internals to Redis
    '''
    def __init__(self, get_problem_payload: Callable[[], dict]):
        self.__rooms: Dict[str, Room] = {}
        self.__lock = asyncio.Lock()
        self.get_problem_payload = get_problem_payload
    
    async def create_room(self) -> str:
        room_id = _new_id()
        async with self.__lock:
            self.__rooms[room_id] = Room(room_id=room_id)
            return room_id
    
    async def join_room(self, room_id:str, name: str) -> str:
        async with self.__lock:
            room = self.__rooms.get(room_id)
            if room is None:
                raise ValueError("Room not found")
            if len(room.players) >= 2:
                raise ValueError("Room is full")
            player_id = _new_id()
            room.players[player_id] = Player(player_id=player_id, name=name)
            await self.maybe_update_status(room)
            return player_id
    
    async def get_state(self, room_id: str) -> dict:
        async with self.__lock:
            room = self.__rooms.get(room_id)
            if room is None:
                raise KeyError("Room not found")
            return self.__state__payload(room)
    
    async def connect_ws(self, room_id: str, player_id: str, ws: WebSocket):
        async with self.__lock:
            room = self.__rooms.get(room_id)
            if room is None:
                raise KeyError("Room not found")
            player = room.players.get(player_id)
            if player is None:
                raise KeyError("Player not found")
            player.ws = ws

            # send state to player and announce
            await self._ws_send(ws, self._state_payload(room))
            await self._broadcast(room, {
                "type": "event",
                 "message": f"{player.name} connected",
            })
            await self._maybe_start(room)
    
    async def disconnect_ws(self, room_id: str, player_id: str) -> None:
        async with self.__lock:
            room = self.__rooms.get(room_id)
            if room is None:
                return
            player = room.players.get(player_id)
            if player is None:
                return
            player.ws = None
            if player_id in room.players:
                room.players[player_id].ws = None
                await self._broadcast(room, {"type": "opponent_left", "player_id": player_id})
                await self._maybe_update_status(room)
                await self._broadcast(room, self._state_payload(room))

    # ----Internals----
    def _state_payload(self, room: Room) -> dict:
        return {
            "type": "state",
            "room_id": room.room_id,
            "status": room.status,
            "players": [
                {
                "player_id": p.player_id, 
                "name": p.name, 
                "connected": p.ws is not None
                } 
                for p in room.players.values()
            ],
        }

    async def _ws_send(self, ws: WebSocket, payload: dict):
        await ws.send_json(payload)
    
    async def _broadcast(self, room: Room, payload: dict):
        gone = []
        for pid, p in room.players.items():
            if p.ws is None:
                continue
            try:
                await p.ws.send_json(payload)
            except Exception:
                gone.append(pid)
        for pid in gone:
            room.players[pid].ws = None
    
    async def maybe_update_status(self, room: Room):
        if len(room.players) < 2:
            room.status = "waiting"
        else:
            room.status = "ready"
    
    async def _maybe_start(self, room: Room):
        connected = [p for p in room.players.values() if p.ws is not None]
        if len(connected) == 2 and room.status in ("waiting", "ready"):
            room.status = "running"
            room.started_at = time.time()
            problem = self._get_problem_payload()
            await self._broadcast(room, {"type": "start", "problem": problem})
        await self._broadcast(room, self._state_payload(room))

# makes database migration - moving from one database to another - easier

DATA_PATH = Path(__file__).parent / "data" / "problems.json"

# Load once at import time (simple + fast for MVP).
# Later you can swap this for DynamoDB/Postgres without changing routes.
with DATA_PATH.open("r", encoding="utf-8") as f:
    _PROBLEMS: List[Dict[str, Any]] = json.load(f)

_INDEX: Dict[str, Dict[str, Any]] = {p["id"]: p for p in _PROBLEMS}


def list_problems() -> List[Dict[str, Any]]:
    return _PROBLEMS


def get_problem(problem_id: str) -> Optional[Dict[str, Any]]:
    return _INDEX.get(problem_id)