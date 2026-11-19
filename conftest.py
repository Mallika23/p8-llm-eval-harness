import pytest
from evals.providers.mock import MockProvider


def pytest_addoption(parser):
    """Register the --record and --record-judge flags"""
    parser.addoption(
        "--record",
        action="store_true",
        default=False,
        help="Call the live model and save replies to fixtures/"
    )
    parser.addoption(
        "--record-judge",
        action="store_true",
        default=False,
        help="Re-record only the judge's replies; replay the saved model answers"
    )

@pytest.fixture(scope="session")
def provider(request):
        if request.config.getoption("--record"):
            from evals.providers.gemini import GeminiProvider
            from evals.providers.recording import RecordingProvider
            return RecordingProvider(GeminiProvider())
        else:
             return MockProvider()


@pytest.fixture(scope="session")
def judge_provider(request):
    """The judge's model, recorded/replayed separately in fixtures/judge/.

    flags given        model answers      judge replies
    (none)             replay             replay
    --record           live + save        live + save
    --record-judge     replay             live + save
    """
    if request.config.getoption("--record") or request.config.getoption("--record-judge"):
        from evals.providers.gemini import GeminiProvider
        from evals.providers.recording import RecordingProvider
        from evals.scorers.judge import JUDGE_MODEL
        return RecordingProvider(GeminiProvider(model=JUDGE_MODEL), fixture_dir="fixtures/judge")
    return MockProvider("fixtures/judge")


@pytest.fixture(scope="session")
def run_results():
    """One shared dict for the whole run: {case_id: [ScorerResult, ...]}.

    Each case adds its results; test_thresholds reads them all at the end.
    """
    return {}
