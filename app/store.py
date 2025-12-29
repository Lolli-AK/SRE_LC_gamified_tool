import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# makes database migration - moving from one database to another - easier

DATA_PATH = Path(__file__).parent / "data" / "problems.json"

# Load once at import time (simple + fast for MVP).
# Later you can swap this for DynamoDB/Postgres without changing routes.
with DATA_PATH.open("r", encoding="utf-8") as f:
    _PROBLEMS: List[Dict[str, Any]] = json.load(f)

_INDEX: Dict[str, Dict[str, Any]] = {p["id"]: p for p in _PROBLEMS}


def list_problems() -> List[Dict[str, Any]]:
    return _PROBLEMS


def get_problem(problem_id: str) -> Optional[Dict[str, Any]]:
    return _INDEX.get(problem_id)