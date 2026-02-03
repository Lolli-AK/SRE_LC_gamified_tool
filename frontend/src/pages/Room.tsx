import { useEffect, useState, useRef, use } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { RoomState } from "../lib/api";

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

    // join room and create websocket
    useEffect(() => {
        if (!roomId || !playerName || joined) return;

        let ws: WebSocket | null = null;

        ( async () => {
            try {
                const joinRes = await api.joinRoom(roomId, { name: playerName });
                setJoined(true);

                ws = new WebSocket(joinRes.ws_url);
                wsRef.current = ws;

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.type === "room_state") {
                        setRoomState(data.payload);
                    }
                };

                ws.onclose = () => {
                    console.log("WebSocket disconnected");
                    setJoined(false);
                };
            } catch (error) {
                console.error("Failed to join room:", error);
            }
        } )();
        return () => {
            if (wsRef.current) wsRef.current.close();
            wsRef.current = null;
            setJoined(false);
        };
    
    }, [roomId, playerName, joined]);

    return (
        <div style={{ padding: 16 }}>
        <h1>Room: {roomId}</h1>
        <div>Player: {playerName}</div>
  
        <pre style={{ marginTop: 12 }}>
          {roomState ? JSON.stringify(roomState, null, 2) : "Waiting for room state..."}
        </pre>
      </div>
    );
}