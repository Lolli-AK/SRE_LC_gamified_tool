# public interface of the service

from pydantic import BaseModel, Field
from typing import List, Literal

# defining schemas - what requests and responses look like

class ProblemListItem(BaseModel):
    id: str
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    tags: List[str]
    baseline_ms: int

class ProblemDetail(ProblemListItem):
    statement: str
    canonical_solution_language: str
    canonical_solution_code: str
    time_complexity: str

class RaceResultRequest(BaseModel):
    problem_id: str
    user_time_ms: int = Field(gt=0)  # must be > 0

class RaceResultResponse(BaseModel):
    result: Literal["win", "loss", "draw"]
    problem_id: str
    baseline_ms: int
    delta_ms: int