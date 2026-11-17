"""Provider wrapper that calls a real provider and saves each reply as a fixture."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from evals.providers.base import Completion, Provider

# __file__ is evals/providers/recording.py, so parents[2] is the repo root
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_DIR = ROOT / "fixtures" / "responses"


class RecordingProvider(Provider):
    """Wraps any provider: calls it, writes the reply to fixtures/, returns it unchanged."""

    name = "recording"

    def __init__(
        self,
        inner: Provider,
        fixture_dir: Path | str = DEFAULT_FIXTURE_DIR,
        delay_s: float = 4.0,
    ) -> None:
        self.inner = inner
        self.fixture_dir = Path(fixture_dir)
        # pause after each call so the free tier's requests-per-minute limit isn't hit
        self.delay_s = delay_s

    def complete(self, prompt: str, *, case_id: str | None = None) -> Completion:
        if case_id is None:
            raise ValueError("case_id must be provided for recording provider.")

        completion = self.inner.complete(prompt, case_id=case_id)

        # keys match what MockProvider reads back
        fixture_data = {
            "case_id": case_id,
            "model": completion.model_name,
            "latency_ms": completion.latency_ms,
            "tokens_in": completion.token_in,
            "tokens_out": completion.token_out,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "text": completion.text,
        }

        self.fixture_dir.mkdir(parents=True, exist_ok=True)
        path = self.fixture_dir / f"{case_id}.json"
        path.write_text(json.dumps(fixture_data, indent=2), encoding="utf-8")

        time.sleep(self.delay_s)
        return completion
