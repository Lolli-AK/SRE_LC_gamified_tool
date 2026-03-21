import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { RoomState } from "../lib/api";
import type { ProblemListItem } from "../types/problem";
import ProblemDetail from "./ProblemDetail";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export default function Room() {
    const { roomId } = useParams<{ roomId: string }>();
    const [roomState, setRoomState] = useState<RoomState | null>(null);
    const [playerName, setPlayerName] = useState<string>("");
    const [joined, setJoined] = useState<boolean>(false);
    const [problems, setProblems] = useState<ProblemListItem[]>([]);
    const [selectingProblem, setSelectingProblem] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const playerIdRef = useRef<string | null>(null);

    // determine if this player is the room creator
    const isCreator = roomId ? localStorage.getItem(`isCreator_${roomId}`) === "true" : false;

    // get player name from local storage or prompt
    useEffect(() => {
        if (!roomId) return;

        const key = `playerName_${roomId}`;
        const saved = localStorage.getItem(key);
    
        const name = saved ?? (prompt("Enter your name") || "Anonymous");
        setPlayerName(name);
        localStorage.setItem(key, name);
    }, [roomId]);

    // load problem list for creator
    useEffect(() => {
        if (!isCreator) return;
        api.getProblems().then(setProblems).catch(console.error);
    }, [isCreator]);

    const hasJoinedRef = useRef(false);

    // join room and create websocket
    useEffect(() => {
        if (!roomId || !playerName || hasJoinedRef.current) return;

        (async () => {
            try {
                const joinRes = await api.joinRoom(roomId, { name: playerName });
                hasJoinedRef.current = true;
                playerIdRef.current = joinRes.player_id;
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

    async function handleSelectProblem(problemId: string) {
        if (!roomId || !playerIdRef.current) return;
        setSelectingProblem(true);
        try {
            await api.selectProblem(roomId, playerIdRef.current, problemId );
        } catch (error) {
            alert(`Failed to select problem: ${error}`);
        } finally {
            setSelectingProblem(false);
        }
    }

    // show picker if creator joined and no problem selected (oppponent waiting)
    const showPicker = isCreator && joined && !roomState?.current_problem_id && roomState?.status == "waiting";



    return (
        <div style={{ padding: 16 }}>
        <h1>Room: {roomId}</h1>
        <div>Player: {playerName}</div>

        {/* Waiting message for the joiner */}
        {roomState?.status === "waiting" && !isCreator && (
                <p className="text-gray-500 mt-2">Waiting for the room creator to pick a problem…</p>
        )}

        {/* Problem picker for the creator */}
        {showPicker && (
                <div className="mt-4 space-y-2">
                    <p className="font-semibold">Pick a problem to race on:</p>
                    {problems.map((p) => (
                        <button
                            key={p.id}
                            disabled={selectingProblem}
                            onClick={() => handleSelectProblem(p.id)}
                            className="w-full text-left border rounded p-3 hover:bg-gray-50 disabled:opacity-50 flex justify-between items-center"
                        >
                            <span className="font-medium">{p.title}</span>
                        </button>
                    ))}
                </div>
            )}
 
            {/* Creator has picked but opponent hasn't joined yet */}
            {isCreator && roomState?.current_problem_id && roomState?.status === "waiting" && (
                <p className="text-gray-500 mt-2">
                    Problem selected! Waiting for your teammate to join…
                </p>
            )}

        {/* Show problem details once a problem is selected */}
        {roomState?.current_problem_id && (
            
        <ProblemDetail problemId={roomState.current_problem_id} />
        )}
      </div>
    );
}