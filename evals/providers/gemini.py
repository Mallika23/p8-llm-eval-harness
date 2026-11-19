import os
import time
import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from evals.providers.base import ProviderError,Provider,Completion

# Load environment variables from .env
load_dotenv()

class GeminiProvider(Provider):
   
    name = "gemini"

    def __init__(self, model="gemini-3.5-flash-lite", max_attempts=3, wait_s=10, timeout_s=300):
        """
        Initializes the Gemini Client.
        The SDK automatically checks os.environ["GEMINI_API_KEY"]
        """

        #fail early with clear message
        if not os.environ.get("GEMINI_API_KEY"):
            raise ProviderError("Gemini api key not set in .env")

        # without a timeout a hung request waits forever (one hung for 7 hours on 19 Nov 2026).
        # The SDK takes the timeout in milliseconds.
        self.client = genai.Client(http_options=types.HttpOptions(timeout=timeout_s * 1000))
        self.timeout_s = timeout_s
        self.model = model
        self.max_attempts = max_attempts
        self.wait_s = wait_s

    def complete(self, prompt:str, *, case_id:str | None = None) -> Completion:
        """ Provider generates response for given prompt prompt which has ticket attached"""
        for attempt in range(1, self.max_attempts +1):
            start = time.perf_counter()
            try: 
                response = self.client.models.generate_content(
                model = self.model,
                contents=prompt
                )
            except (errors.ClientError, errors.ServerError) as e:
                # 429 (rate limit) and 503 (overloaded) are temporary: wait and retry.
                # Anything else (bad key, bad request) or out of attempts: fail now.
                if e.code in (429,503) and attempt < self.max_attempts:
                    wait = self.wait_s * 2 ** (attempt -1)
                    print(f"Gemini error {e.code}, retrying in {wait}s (attempt {attempt}/{self.max_attempts})")
                    time.sleep(wait)
                    continue
                else:
                    raise ProviderError(
                        f"Gemini error (Status {e.code}): {e.message} - attempt {attempt}/{self.max_attempts}"
                    ) from e
            except httpx.TimeoutException as e:
                # no reply within timeout_s: temporary, same treatment as a 503
                if attempt < self.max_attempts:
                    wait = self.wait_s * 2 ** (attempt -1)
                    print(f"Gemini timed out after {self.timeout_s}s, retrying in {wait}s (attempt {attempt}/{self.max_attempts})")
                    time.sleep(wait)
                    continue
                raise ProviderError(
                    f"Gemini timed out after {self.timeout_s}s - attempt {attempt}/{self.max_attempts}"
                ) from e
            except errors.APIError as e:
                # Catch-all fallback for generic API communication issues
                raise ProviderError(f"Unexpected API error occur: {e}") from e

            latency_ms = (time.perf_counter() - start) * 1000
            usage = response.usage_metadata
            return Completion(text=response.text or "",
                            model_name=self.model,
                            latency_ms=latency_ms,
                            token_in=usage.prompt_token_count if usage else None,
                            token_out=usage.candidates_token_count if usage else None
                            )

        # only reached if max_attempts < 1, since the last attempt always returns or raises
        raise ProviderError(f"No attempt made: max_attempts={self.max_attempts}")

        


    



