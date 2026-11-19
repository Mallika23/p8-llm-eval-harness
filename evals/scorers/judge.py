"""LLM-as-judge scorer: a second model grades the summary's faithfulness to the ticket."""

import json
from pathlib import Path

from evals.providers.base import Provider
from evals.scorers.deterministic import ScorerResult

# this file is evals/scorers/judge.py, so parents[1] is evals/
DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "judge_summary_v1.txt"

# a larger model than the one under test (gemini-3.5-flash-lite), to reduce
# self-preference bias. Still the same family - a known limitation.
# Switched from gemini-3.5-flash on 19 Nov 2026: it returned 503 (overloaded)
# repeatedly on the free tier.
JUDGE_MODEL = "gemini-3.8-flash"


class JudgeError(Exception):
    """The judge itself misbehaved (unparseable reply, score out of range).

    Raised instead of scoring 0: a broken judge is a tooling fault, and a
    silent 0 would drag the average down and get blamed on the model.
    """


class SummaryJudge:
    """Callable like the deterministic scorers: judge(output, case) -> ScorerResult."""

    name = "summary_faithfulness"

    def __init__(self, provider: Provider, prompt_path: Path | str = DEFAULT_PROMPT_PATH) -> None:
        self.provider = provider
        # read once here, not once per case
        self.template = Path(prompt_path).read_text(encoding="utf-8")

    def __call__(self, output: str, case: dict) -> ScorerResult:
        # 1. pull the summary out of the triage model's answer
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            data = None
        summary = data.get("summary") if isinstance(data, dict) else None
        if not isinstance(summary, str) or not summary.strip():
            # nothing to grade - don't spend a judge call
            return ScorerResult(self.name, 0.0, False, "No summary to judge: output has no usable 'summary'.")

        # 2. fill the rubric (.replace, not .format: the template contains JSON braces)
        prompt = self.template.replace("{ticket}", case["input"]).replace("{summary}", summary)

        # 3. ask the judge; same case_id, so its fixture is fixtures/judge/<case_id>.json
        reply = self.provider.complete(prompt, case_id=case["id"])

        # 4. parse the judge's reply strictly
        try:
            verdict = json.loads(reply.text)
        except json.JSONDecodeError as e:
            raise JudgeError(f"Judge reply is not valid JSON for {case['id']}: {reply.text!r}") from e
        if not isinstance(verdict, dict):
            raise JudgeError(f"Judge reply is not a JSON object for {case['id']}: {reply.text!r}")
        n = verdict.get("score")
        reasoning = verdict.get("reasoning", "")
        # bool is a subclass of int in Python, so exclude it explicitly
        if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 5:
            raise JudgeError(f"Judge score must be an integer 1-5 for {case['id']}, got {n!r}")

        # 5. map 1-5 onto 0.0-1.0; keep the raw score in the reason
        return ScorerResult(
            name=self.name,
            score=(n - 1) / 4,
            passed=n >= 4,
            reason=f"{n}/5: {reasoning}",
        )
