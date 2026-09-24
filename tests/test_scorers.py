from evals.scorers.deterministic import (json_schema_valid, exact_field_match, allowed_values, no_refusal, ScorerResult)

#constants defined in caps 
GOOD           = '{"category": "billing", "priority": "high", "needs_human": true, "summary": "Charged twice."}'
TRUNCATED      = '{"category": "billing", "priority"'
WRONG_CATEGORY = '{"category": "technical", "priority": "high", "needs_human": true, "summary": "x"}'
BAD_PRIORITY   = '{"category": "billing", "priority": "urgent", "needs_human": true, "summary": "x"}'
MISSING_KEY    = '{"category": "billing", "priority": "high"}'
REFUSAL        = "I'm sorry, but I can't help with that request."

CASE = {"expected": {"category": "billing", "priority": "high"}}


def test_schema_accepts_good():
    assert json_schema_valid(GOOD, CASE).score == 1.0

def test_schema_rejects_truncated():
    r = json_schema_valid(TRUNCATED, CASE)
    assert r.score == 0.0
    assert "not valid" in r.reason

def test_schema_rejects_missing_keys():
    r = json_schema_valid(MISSING_KEY, CASE)
    assert r.passed is False
    assert "Missing" in r.reason

def test_field_match_accepts_billing():
    assert exact_field_match(GOOD, CASE).score == 1.0

def test_field_match_rejects_wrong_category():
    r = exact_field_match(WRONG_CATEGORY, CASE)
    assert r.score == 0.0
    assert "billing" in r.reason

def test_allowed_values_accepts_high():
    assert allowed_values(GOOD, CASE).score == 1.0

def test_allowed_values_rejects_urgent():
    r = allowed_values(BAD_PRIORITY, CASE)
    assert r.score == 0.0
    assert "urgent" in r.reason

def test_no_refusal_passes_normal_output():
    assert no_refusal(GOOD, CASE).score == 1.0

def test_no_refusal_catches_refusal():
    assert no_refusal(REFUSAL, CASE).score == 0.0

def test_no_scorer_crashes_on_garbage():
    for fn in (json_schema_valid, exact_field_match, allowed_values, no_refusal):
        assert isinstance(fn("complete nonsense", CASE), ScorerResult)