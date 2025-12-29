import json
import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Provides a TestClient with a temporary problems JSON file.
    """
    problems = [
        {
            "id": "two-sum",
            "title": "Two Sum",
            "difficulty": "easy",
            "tags": ["array", "hashmap"],
            "baseline_ms": 1200,
            "statement": "Given an array of integers ...",
            "canonical_solution_language": "python",
            "canonical_solution_code": "def twoSum(nums, target): ...",
            "time_complexity": "O(n)",
        },
        {
            "id": "merge-intervals",
            "title": "Merge Intervals",
            "difficulty": "medium",
            "tags": ["array", "sorting"],
            "baseline_ms": 3500,
            "statement": "Given intervals ...",
            "canonical_solution_language": "python",
            "canonical_solution_code": "def merge(intervals): ...",
            "time_complexity": "O(n log n)",
        },
    ]

    tmp_file = tmp_path / "problems.json"
    tmp_file.write_text(json.dumps(problems), encoding="utf-8")

    # need to set this to correct PROBLEMS_PATH:
    monkeypatch.setenv("PROBLEMS_PATH", str(tmp_file))

    # If your app caches problems at import time, you may need to reload them here.
    # e.g. app.state.problem_store.load()

    return TestClient(app)
