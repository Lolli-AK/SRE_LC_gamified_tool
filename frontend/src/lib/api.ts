const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export type ProblemListItem = {
  id: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
  tags: string[];
  baseline_ms: number;
};

export type ProblemDetail = ProblemListItem & {
  statement: string;
  canonical_solution_language: string;
  canonical_solution_code: string;
  time_complexity: string;
};

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

export const api = {
  health: () => http<{ status: string }>("/health"),
  listProblems: () => http<ProblemListItem[]>("/problems"),
  getProblem: (id: string) => http<ProblemDetail>(`/problems/${id}`),
  race: (body: RaceRequest) =>
    http<RaceResponse>("/race", { method: "POST", body: JSON.stringify(body) }),
};