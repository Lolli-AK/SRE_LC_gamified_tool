import { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function Home() {
  const [status, setStatus] = useState("checking...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.health()
      .then((r) => setStatus(r.status))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Race Lobby</h1>

      <div className="rounded-xl border bg-white p-4">
        <div className="text-sm text-gray-600">API status</div>
        {error ? (
          <div className="mt-1 text-red-600">{error}</div>
        ) : (
          <div className="mt-1 font-medium">{status}</div>
        )}
      </div>

      <div className="rounded-xl border bg-white p-4 text-gray-700">
        Pick a problem and race the baseline.
      </div>
    </div>
  );
}