"""Runs every dataset case through the provider and scorers, then scores the whole run.

Two layers:
- test_cases (once per case): collects scores. Fails only if OUR code breaks
  (missing fixture, exception, unknown scorer) - never because the model was wrong.
- test_thresholds (once, after all cases): averages each scorer across the
  dataset, writes the markdown report, and fails if a score is below its threshold.
"""

import pytest

from evals.dataset import LoadDataset
from evals.report import summarise, write_report
from evals.scorers import SCORERS

# Minimum average score (0.0-1.0) per scorer across the whole dataset.
# Choosing these is a risk decision: format checks must be perfect,
# category accuracy is allowed one miss in 8 (7/8 = 0.875).
THRESHOLDS = {
    "json_schema_valid": 1.0,
    "allowed_values": 1.0,
    "no_refusal": 1.0,
    "exact_field_match": 0.85,
}

# runs once, when pytest loads this file
dataset = LoadDataset()
CASES = dataset.load_cases()


# runs once per case; ids make each one show as test_cases[case_01] etc.
@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_cases(case, provider, run_results):
    # 1. fill the prompt with this case's ticket
    prompt = dataset.build_prompt(case)

    # 2. get the model's answer (mock replays a fixture; --record calls Gemini and saves it)
    completion = provider.complete(prompt, case_id=case["id"])

    # 3. run each scorer listed for this case and keep every result
    results = []
    for name in case["scorers"]:
        scorer = SCORERS[name]
        results.append(scorer(completion.text, case))

    # 4. store them for the run-level score - no assert on quality here
    run_results[case["id"]] = results


# defined after test_cases, so pytest runs it after all the cases
def test_thresholds(provider, run_results):
    missing = [c["id"] for c in CASES if c["id"] not in run_results]
    if missing:
        pytest.skip(f"not every case ran, so no run score: {missing}")

    # 5. average each scorer across all cases and write the report
    summary = summarise(run_results)
    report_path = write_report(run_results, summary, THRESHOLDS, provider.name)
    print(f"\nreport: {report_path}")

    # 6. the gate: fail the run if any scorer's average is below its threshold
    below = {
        name: f"{summary[name]['score']:.2f} < {threshold:.2f}"
        for name, threshold in THRESHOLDS.items()
        if name in summary and summary[name]["score"] < threshold
    }
    assert not below, f"scores below threshold: {below} (see {report_path})"
