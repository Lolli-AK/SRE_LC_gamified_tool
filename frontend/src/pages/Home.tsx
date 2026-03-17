import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);
  const [status, setStatus] = useState("checking...");
  const [error, setError] = useState<string | null>(null);

  const handleCreateRace = async () => {
    setCreating(true);
    try{
      const resp = await api.createRoom();
      localStorage.setItem(`isCreator_${resp.room_id}`, "true");
      navigate(`/room/${resp.room_id}`);
    } catch (error) {
      alert(`Failed to create room: ${error}`);
      setCreating(false);
    }
  };

  useEffect(() => {
    api.health()
      .then((r) => setStatus(r.status))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Race Lobby</h1>

      <div className="rounded-xl border bg-white p-4">
        <button
          onClick={handleCreateRace}
          disabled={creating}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {creating ? "Creating..." : "Create a Race"}
        </button>
        <div className="text-sm text-gray-600">API status</div>
        {error ? (
          <div className="mt-1 text-red-600">{error}</div>
        ) : (
          <div className="mt-1 font-medium">{status}</div>
        )}
      </div>

      <div className="rounded-xl border bg-white p-4 text-gray-700">
        Pick a problem to solve.
        Click "Create a Race" to generate a room. Share the link with a friend to race together!
      </div>
    </div>
  );
}