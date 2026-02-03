const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

import type { ProblemListItem, ProblemDetail } from "../types/problem";

type HealthResponse = { status: string };

export type CreateRoomResponse = {
  room_id: string;
};

export type JoinRoomRequest = {
  name: string;
};

export type JoinRoomResponse = {
  room_id: string;
  player_id: string; 
  ws_url: string;
};

export type RoomState = {
  room_id: string;
  status: string;
  players: Array<{
    player_id: string;
    name: string;
    connected: boolean;
  }>;
}

export type RaceRequest = {
  problem_id: string;
  user_time_ms: number;
};

export type RaceResponse = {
  result: "win" | "loss" | "draw";
  problem_id: string;
  baseline_ms: number;
  delta_ms: number;
};

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? ` - ${text}` : ""}`);
  }

  return res.json();
}

const BASE = import.meta.env.VITE_API_BASE;

export const api = {

  async createRoom(): Promise<CreateRoomResponse> {
    return http<CreateRoomResponse>("/rooms", { method: "POST" });
  },

  async joinRoom(roomId: string, body: JoinRoomRequest): Promise<JoinRoomResponse> {
    return http<JoinRoomResponse>(`/rooms/${roomId}/join`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async getRoomState(roomId: string): Promise<RoomState> {
    return http<RoomState>(`/rooms/${roomId}`);
  },
  
  async getProblems(): Promise<ProblemListItem[]> {
    const res = await fetch(`${BASE}/problems`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async race(body: RaceRequest): Promise<RaceResponse> {
    const res = await fetch(`${import.meta.env.VITE_API_BASE}/race`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getProblem(id: string): Promise<ProblemDetail> {
    const res = await fetch(`${BASE}/problems/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async execute(body: { problem_id: string; code: string; language: "python" }) {
    const res = await fetch(`${BASE}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async health(): Promise<HealthResponse> {
    const res = await fetch(`${import.meta.env.VITE_API_BASE}/health`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};