from pydantic import BaseModel, Field
from typing import Literal, List, Optional

class ExecuteRequest(BaseModel):
    problem_id: str
    code: str = Field(min_length=1, max_length=50_000)
    language: Literal["python"] = "python"

class ExecuteTestResult(BaseModel):
    index: int
    passed: bool
    actual_json: str
    expected_json: str
    runtime_ms: int
    error: Optional[str] = None

class ExecuteResponse(BaseModel):
    tests: List[ExecuteTestResult]
    total_runtime_ms: int