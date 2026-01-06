import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, type ProblemListItem } from "../lib/api";

export default function Problems() {
  const [problems, setProblems] = useState<ProblemListItem[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listProblems().then(setProblems).catch((e) => setError(String(e)));
  }, []);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return problems;
    return problems.filter(
      (p) =>
        p.title.toLowerCase().includes(s) ||
        p.id.toLowerCase().includes(s) ||
        p.tags.join(" ").toLowerCase().includes(s)
    );
  }, [problems, q]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Problems</h1>

      <input
        className="w-full rounded-lg border bg-white p-3"
        placeholder="Search title, id, or tag…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />

      {error && <div className="text-red-600">{error}</div>}

      <div className="grid gap-3">
        {filtered.map((p) => (
          <Link
            key={p.id}
            to={`/problems/${p.id}`}
            className="rounded-xl border bg-white p-4 hover:shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div className="font-semibold">{p.title}</div>
              <div className="text-sm text-gray-600">{p.difficulty}</div>
            </div>
            <div className="mt-1 text-sm text-gray-700">
              Baseline: <b>{p.baseline_ms}ms</b>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {p.tags.map((t) => (
                <span key={t} className="rounded-full bg-gray-100 px-2 py-1 text-xs">
                  {t}
                </span>
              ))}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}