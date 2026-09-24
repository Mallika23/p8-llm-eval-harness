"""Deterministic scorers — code checks the model's output. No model involved."""

import json
import re
from dataclasses import dataclass
from unicodedata import category

#sets
REQUIRED_KEYS = {"category", "priority", "needs_human", "summary"}
ALLOWED_CATEGORIES = {"billing", "accounts", "technical", "other"}
ALLOWED_PRIORITIES = {"high", "medium", "low"}

REFUSAL_PATTERNS = [
    r"\bI can'?t\b",
    r"\bI cannot\b",
    r"\bI'?m unable\b",
    r"\bas an AI\b",
    r"\bI'?m sorry, but\b",
]
@dataclass(frozen=True)
class ScorerResult:
    """Result of scoring a model's output."""
    name: str
    score: float
    passed: bool
    reason: str 


# the _ (underscore) prefix is a convention to indicate that this function is intended for internal use only and not part of the public API.
def _parse(output: str):
    """Try to read the model's text as JSON. Returns (data, error_message)."""
    try:
        return json.loads(output), ""
    except json.JSONDecodeError as e:
        return None, f"JSON not valid: {e.msg} at position {e.pos}. Output was: {output}"

def json_schema_valid(output, case):
    data, err = _parse(output)
    if data is None:
        return ScorerResult(name="json_schema_valid", score=0.0, passed=False, reason=err)
    if not isinstance(data, dict):
        return ScorerResult(name="json_schema_valid", score=0.0, passed=False, reason=f"Output is not a JSON object: {data}")
    missing = REQUIRED_KEYS - data.keys()
    if missing:
        return ScorerResult(name="json_schema_valid", score=0.0, passed=False, reason=f"Missing required keys: {missing}. Output was: {data}")  
    return ScorerResult(name="json_schema_valid", score=1.0, passed=True, reason="Output is valid JSON and contains all required keys.")

def exact_field_match(output, case):
    data, err = _parse(output)
    if data is None:
        return ScorerResult(name="exact_field_match", score=0.0, passed=False, reason=err)
    got = data.get("category","").strip().lower()
    expected = str(case["expected"]["category"]).strip().lower()
    if got !=expected:
        return ScorerResult(name="exact_field_match", score=0.0, passed=False, reason=f"Category mismatch: expected '{expected}', got '{got}'.")
    return ScorerResult(name="exact_field_match", score=1.0, passed=True, reason="Category matches expected value.")

def allowed_values(output, case):
    data, err = _parse(output)
    if data is None:
        return ScorerResult(name="allowed_values", score=0.0, passed=False, reason=err)
    category = data.get("category","").strip().lower()
    if category not in ALLOWED_CATEGORIES:
        return ScorerResult(name="allowed_values", score=0.0, passed=False, reason=f"Category '{category}' is not in allowed categories: {ALLOWED_CATEGORIES}.")
    priority = data.get("priority","").strip().lower()
    if priority not in ALLOWED_PRIORITIES:
        return ScorerResult(name="allowed_values", score=0.0, passed=False, reason=f"Priority '{priority}' is not in allowed priorities: {ALLOWED_PRIORITIES}.")
    return ScorerResult(name="allowed_values", score=1.0, passed=True, reason="All fields have allowed values.")


def no_refusal(output, case):
    data, err = _parse(output)
    for pattern in REFUSAL_PATTERNS:
        #re.IGNORECASE — a flag making the match case-insensitive
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return ScorerResult(name="no_refusal", score=0.0, passed=False, reason=f"Output contains refusal pattern: '{pattern}'.")
    return ScorerResult(name="no_refusal", score=1.0, passed=True, reason="No refusal patterns found in output.")
