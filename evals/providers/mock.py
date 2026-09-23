"""Provider that replays recorded responses instead of actually calling a model/api."""
#"""docstring""" used for class and function documentation, not for comments.

import json
from pathlib import Path

from evals.providers.base import Completion, Provider

class FixtureNotFoundError(Exception):
    """Raised when a fixture file is not found."""

class MockProvider(Provider):
    name="mock"

    def __init__(self, fixture_dir: Path | str = "fixtures/responses") -> None:
        self.fixture_dir = Path(fixture_dir)

    def complete(self, prompt:str, *, case_id:str | None = None) -> Completion:
        if case_id is None:
            raise ValueError("case_id must be provided for mock provider.")

        path = self.fixture_dir / f"{case_id}.json"
        if not path.exists():
            raise FixtureNotFoundError(f"Fixture file not found: {path}. Create it by hand"
                                       f" or record it from a live run later")
        
        data = json.loads(path.read_text(encoding="utf-8"))

        return Completion(
            #[] brackets mean required, .get() means optional, defaults to None if not provided
            text=data["text"],
            model_name=data.get("model","mock"),
            latency_ms=data.get("latency_ms",0.0),
            token_in=data.get("token_in"),
            token_out=data.get("token_out")
        )