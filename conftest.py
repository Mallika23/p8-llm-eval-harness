import pytest
from evals.providers.mock import MockProvider


def pytest_addoption(parser):
    """Register the --record"""
    parser.addoption(
        "--record",
        action="store_true",
        default=False,
        help="Call the live model and save replies to fixtures/"
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
def run_results():
    """One shared dict for the whole run: {case_id: [ScorerResult, ...]}.

    Each case adds its results; test_thresholds reads them all at the end.
    """
    return {}
