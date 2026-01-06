import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, type ProblemDetail as ProblemDetailType } from "../lib/api";

export default function ProblemDetail() {
  const { id } = useParams();
  const [problem, setProblem] = useState<ProblemDetailType | null>(null);
  const [runtime, setRuntime] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<null | {
    result: "win" | "loss" | "draw";
    delta_ms: number;
    baseline_ms: number;
  }>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setError(null);
    setProblem(null);
    setResult(null);

    api.getProblem(id)
      .then(setProblem)
      .catch((e) => setError(String(e)));
  }, [id]);

  async function submitRace() {
    if (!id) return;
    setError(null);
    setResult(null);

    const ms = Number(runtime);
    if (!Number.isFinite(ms) || ms <= 0) {
      setError("Enter a positive runtime in milliseconds.");
      return;
    }

    setSubmitting(true);
    try {
      const r = await api.race({ problem_id: id, user_time_ms: ms });
      setResult({ result: r.result, delta_ms: r.delta_ms, baseline_ms: r.baseline_ms });
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  }

  if (error && !problem) {
    return (
      <div className="space-y-3">
        <div className="text-red-600">{error}</div>
        <Link to="/problems" className="text-sm underline">
          ← Back to Problems
        </Link>
      </div>
    );
  }

  if (!problem) return <div>Loading…</div>;

  const badge =
    problem.difficulty === "easy"
      ? "bg-green-100 text-green-800"
      : problem.difficulty === "medium"
      ? "bg-yellow-100 text-yellow-800"
      : "bg-red-100 text-red-800";

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm text-gray-500">{problem.id}</div>
          <h1 className="text-2xl font-bold">{problem.title}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${badge}`}>
              {problem.difficulty}
            </span>
            {problem.tags.map((t) => (
              <span key={t} className="rounded-full bg-gray-100 px-3 py-1 text-xs">
                {t}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-xl border bg-white p-4">
          <div className="text-sm text-gray-600">Baseline</div>
          <div className="text-xl font-semibold">{problem.baseline_ms}ms</div>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-4">
        <div className="font-medium">Statement</div>
        <p className="mt-2 whitespace-pre-wrap text-gray-800">{problem.statement}</p>
      </div>

      <div className="rounded-xl border bg-white p-4">
        <div className="font-medium">Race the baseline</div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input
            className="w-56 rounded-lg border p-2"
            placeholder="runtime in ms (e.g. 123)"
            value={runtime}
            onChange={(e) => setRuntime(e.target.value)}
          />
          <button
            onClick={submitRace}
            disabled={submitting}
            className="rounded-lg bg-black px-4 py-2 text-white disabled:opacity-60"
          >
            {submitting ? "Racing…" : "Race"}
          </button>
          <Link to="/problems" className="text-sm text-gray-600 hover:underline">
            Back to Problems
          </Link>
        </div>

        {result && (
          <div className="mt-4 rounded-lg border p-3">
            <div className="font-semibold">
              Result:{" "}
              <span
                className={
                  result.result === "win"
                    ? "text-green-700"
                    : result.result === "loss"
                    ? "text-red-700"
                    : "text-gray-700"
                }
              >
                {result.result.toUpperCase()}
              </span>
            </div>
            <div className="mt-1 text-sm text-gray-700">
              Baseline: <b>{result.baseline_ms}ms</b> • Delta:{" "}
              <b>{result.delta_ms}ms</b>
            </div>
          </div>
        )}

        {error && <div className="mt-3 text-red-600">{error}</div>}
      </div>
    </div>
  );
}