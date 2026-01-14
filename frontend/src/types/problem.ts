export type ProblemListItem = {
    id: string;
    title: string;
    difficulty: "easy" | "medium" | "hard";
    tags: string[];
    baseline_ms: number;
  };
  
  export type ProblemDetail = ProblemListItem & {
    statement: string;
    function_signature?: string;
    starter_code?: string;
    samples?: Array<{ args_json: string; expected_json: string }>;
  };