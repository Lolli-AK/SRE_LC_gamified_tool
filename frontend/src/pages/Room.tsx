import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { RoomState } from "../lib/api";
import ProblemDetail from "./ProblemDetail";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export default function Room() {
    const { roomId } = useParams<{ roomId: string }>();
    const [roomState, setRoomState] = useState<RoomState | null>(null);
    const [playerName, setPlayerName] = useState<string>("");
    const [joined, setJoined] = useState<boolean>(false);
    const wsRef = useRef<WebSocket | null>(null);

    // get player name from local storage or prompt
    useEffect(() => {
        if (!roomId) return;

        const key = `playerName_${roomId}`;
        const saved = localStorage.getItem(key);
    
        const name = saved ?? (prompt("Enter your name") || "Anonymous");
        setPlayerName(name);
        localStorage.setItem(key, name);
    }, [roomId]);

    const hasJoinedRef = useRef(false);

    // join room and create websocket
    useEffect(() => {
        if (!roomId || !playerName || hasJoinedRef.current) return;

        (async () => {
            try {
                const joinRes = await api.joinRoom(roomId, { name: playerName });
                hasJoinedRef.current = true;
                setJoined(true);

                const wsBase = API_BASE
                    .replace("http://", "ws://")
                    .replace("https://", "wss://");
                const wsUrl = `${wsBase}/ws/${roomId}?player_id=${joinRes.player_id}`;

                const ws = new WebSocket(wsUrl);
                wsRef.current = ws;

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    // Backend sends {"type": "state", "room_id", "status", "players"}
                    if (data.type === "state") {
                        setRoomState(data);
                    }
                };

                ws.onclose = () => {
                    console.log("WebSocket disconnected");
                    hasJoinedRef.current = false;
                    setJoined(false);
                };
            } catch (error) {
                console.error("Failed to join room:", error);
            }
        })();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    }, [roomId, playerName]);

    console.log("Room state:", roomState);

    return (
        <div style={{ padding: 16 }}>
        <h1>Room: {roomId}</h1>
        <div>Player: {playerName}</div>
        {roomState?.current_problem_id && (
            
        <ProblemDetail problemId={roomState.current_problem_id} />
        )}
      </div>
    );
}