// pages/Problems.tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { ProblemListItem } from "../types/problem";

export default function Problems() {
  const [problems, setProblems] = useState<ProblemListItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getProblems()
      .then(setProblems)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="text-red-600">{error}</div>;

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Problems</h1>

      <div className="space-y-2">
        {problems.map((p) => (
          <Link
            key={p.id}
            to={`/problems/${p.id}`}
            className="block rounded border bg-white p-3 hover:bg-gray-50"
          >
            <div className="font-medium">{p.title}</div>
            <div className="text-sm opacity-70">{p.difficulty}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}