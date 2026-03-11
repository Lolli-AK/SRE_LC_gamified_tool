// pages/ProblemDetail.tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Editor from "@monaco-editor/react";
import { api } from "../lib/api";
import type { ProblemDetail } from "../types/problem";

type ExecuteResponse = {
  tests: Array<{
    index: number;
    passed: boolean;
    actual_json: string;
    expected_json: string;
    runtime_ms: number;
    error?: string;
  }>;
  total_runtime_ms: number;
};

export default function ProblemDetail({ problemId }: { problemId?: string }) {
  const params = useParams();
  const id = problemId ?? params.id;
  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [code, setCode] = useState<string>("");
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState<ExecuteResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      const p = await api.getProblem(id);
      setProblem(p);
      setCode(p.starter_code ?? `${p.function_signature ?? "def solution(*args):"}\n    pass\n`);
    })().catch((e) => setRunError(String(e)));
  }, [id]);

  async function onRun() {
    if (!id) return;
    setRunning(true);
    setRunError(null);
    setRunResult(null);
    try {
      const res = await api.execute({ problem_id: id, code, language: "python" });
      setRunResult(res);
    } catch (e: any) {
      setRunError(e?.message ?? "Run failed");
    } finally {
      setRunning(false);
    }
  }

  if (!problem) return <div>Loading…</div>;

  return (
    <div className="p-4 space-y-4">
      <div>
        <h1 className="text-xl font-semibold">{problem.title}</h1>
        <p className="text-sm opacity-80">{problem.difficulty}</p>
      </div>

      <div className="prose max-w-none">
        <pre className="whitespace-pre-wrap">{problem.statement}</pre>
      </div>

      <div className="rounded-lg overflow-hidden border">
        <Editor
          height="420px"
          defaultLanguage="python"
          value={code}
          onChange={(v) => setCode(v ?? "")}
          options={{ minimap: { enabled: false }, fontSize: 14, scrollBeyondLastLine: false }}
        />
      </div>

      <button
        className="px-3 py-2 rounded bg-black text-white disabled:opacity-50"
        onClick={onRun}
        disabled={running}
      >
        {running ? "Running…" : "Run"}
      </button>

      {runError && <div className="text-red-600">{runError}</div>}

      {runResult && (
        <div className="space-y-2">
          <div className="text-sm">
            Total: <b>{runResult.total_runtime_ms} ms</b>
          </div>
          {runResult.tests.map((t) => (
            <div key={t.index} className="border rounded p-2 text-sm">
              Test {t.index + 1}:{" "}
              <b className={t.passed ? "text-green-700" : "text-red-700"}>
                {t.passed ? "PASS" : "FAIL"}
              </b>{" "}
              ({t.runtime_ms} ms)
            </div>
          ))}
        </div>
      )}
    </div>
  );
}