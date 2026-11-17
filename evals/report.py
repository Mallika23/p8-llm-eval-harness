"""Turns per-case scorer results into dataset-level scores and a markdown report."""

from datetime import datetime
from pathlib import Path

from evals.scorers.deterministic import ScorerResult

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "reports"


def summarise(run_results: dict[str, list[ScorerResult]]) -> dict[str, dict]:
    """Average each scorer across all cases.

    run_results: {"case_01": [ScorerResult, ...], "case_02": [...], ...}
    returns:     {"exact_field_match": {"score": 0.875, "passed": 7, "total": 8}, ...}
    """
    by_scorer: dict[str, list[ScorerResult]] = {}
    for results in run_results.values():
        for r in results:
            by_scorer.setdefault(r.name, []).append(r)

    summary = {}
    for name, results in by_scorer.items():
        summary[name] = {
            "score": sum(r.score for r in results) / len(results),
            "passed": sum(1 for r in results if r.passed),
            "total": len(results),
        }
    return summary


def write_report(
    run_results: dict[str, list[ScorerResult]],
    summary: dict[str, dict],
    thresholds: dict[str, float],
    provider_name: str,
    report_dir: Path | str = DEFAULT_REPORT_DIR,
) -> Path:
    """Write a markdown report for this run and return its path."""
    now = datetime.now()
    lines = [
        f"# Eval run — {now:%Y-%m-%d %H:%M}",
        "",
        f"- Provider: `{provider_name}`",
        f"- Cases: {len(run_results)}",
        "",
        "## Scores",
        "",
        "| Scorer | Score | Cases passed | Threshold | Result |",
        "|---|---|---|---|---|",
    ]
    for name, s in summary.items():
        threshold = thresholds.get(name)
        if threshold is None:
            result, threshold_text = "no threshold", "—"
        else:
            result = "PASS" if s["score"] >= threshold else "FAIL"
            threshold_text = f"{threshold:.2f}"
        lines.append(
            f"| {name} | {s['score']:.2f} | {s['passed']}/{s['total']} | {threshold_text} | {result} |"
        )

    lines += ["", "## Failed checks", ""]
    failed = [(case_id, r) for case_id, results in run_results.items() for r in results if not r.passed]
    if not failed:
        lines.append("None.")
    for case_id, r in failed:
        lines.append(f"- **{case_id}** · `{r.name}`: {r.reason}")

    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"run_{now:%Y%m%d_%H%M%S}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
