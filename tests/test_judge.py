"""Unit tests for SummaryJudge, using a stub provider - no API calls."""

import pytest

from evals.providers.base import Completion, Provider
from evals.scorers.judge import JudgeError, SummaryJudge

CASE = {"id": "case_x", "input": "I was charged twice for my September invoice."}
GOOD_OUTPUT = (
    '{"category": "billing", "priority": "high", "needs_human": true,'
    ' "summary": "Customer was charged twice for September."}'
)


class StubJudge(Provider):
    """Returns one fixed reply and remembers the prompts it was sent."""

    name = "stub"

    def __init__(self, reply_text: str) -> None:
        self.reply_text = reply_text
        self.prompts = []

    def complete(self, prompt, *, case_id=None):
        self.prompts.append(prompt)
        return Completion(text=self.reply_text, model_name="stub", latency_ms=0.0)


def test_score_5_maps_to_1_and_passes():
    judge = SummaryJudge(StubJudge('{"reasoning": "all supported", "score": 5}'))
    result = judge(GOOD_OUTPUT, CASE)
    assert result.score == 1.0
    assert result.passed
    assert result.reason == "5/5: all supported"


def test_score_2_maps_to_quarter_and_fails():
    judge = SummaryJudge(StubJudge('{"reasoning": "invents a refund", "score": 2}'))
    result = judge(GOOD_OUTPUT, CASE)
    assert result.score == 0.25
    assert not result.passed


def test_prompt_contains_ticket_and_summary():
    stub = StubJudge('{"reasoning": "ok", "score": 5}')
    SummaryJudge(stub)(GOOD_OUTPUT, CASE)
    sent = stub.prompts[0]
    assert CASE["input"] in sent
    assert "Customer was charged twice for September." in sent
    assert "{ticket}" not in sent and "{summary}" not in sent


@pytest.mark.parametrize("bad_output", [
    "not json at all",
    '{"category": "billing"}',          # no summary key
    '{"summary": "   "}',               # empty summary
])
def test_no_summary_scores_zero_without_calling_judge(bad_output):
    stub = StubJudge('{"reasoning": "ok", "score": 5}')
    result = SummaryJudge(stub)(bad_output, CASE)
    assert result.score == 0.0
    assert not result.passed
    assert stub.prompts == []  # judge never called


@pytest.mark.parametrize("bad_reply", [
    "Sure! The score is 5.",                       # not JSON
    '{"reasoning": "ok", "score": 7}',             # out of range
    '{"reasoning": "ok", "score": "5"}',           # string, not int
    '{"reasoning": "ok"}',                         # no score
])
def test_broken_judge_reply_raises(bad_reply):
    with pytest.raises(JudgeError):
        SummaryJudge(StubJudge(bad_reply))(GOOD_OUTPUT, CASE)
