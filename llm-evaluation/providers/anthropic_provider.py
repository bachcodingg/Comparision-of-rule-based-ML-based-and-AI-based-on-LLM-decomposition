"""Claude via the official Anthropic SDK.

Notes that matter for an evaluation:
- Current Claude models reject `temperature`/`top_p`/`top_k`, so determinism
  cannot be requested. Run-to-run variation is measured with repeated trials.
- Thinking is always on for Claude Opus 5.5; depth is set with
  `output_config.effort` and recorded with every result.
- Server-side refusal fallbacks are deliberately NOT enabled: a fallback would
  let a different model answer, and the answer would be attributed to the model
  under evaluation. A refusal is recorded as an outcome instead.
"""

from __future__ import annotations

import time

import anthropic

from prompt import RESPONSE_SCHEMA

DEFAULT_MODEL = "claude-opus-5-5"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str | None = None, effort: str = "medium", max_tokens: int = 16000):
        self.model = model or DEFAULT_MODEL
        self.effort = effort
        self.max_tokens = max_tokens
        # Resolves ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN or an `ant auth login` profile.
        self.client = anthropic.Anthropic()

    def settings(self) -> dict:
        return {"model": self.model, "effort": self.effort, "max_tokens": self.max_tokens,
                "temperature": "not supported by this model"}

    def complete(self, prompt: str) -> dict:
        started = time.perf_counter()
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                output_config={
                    "effort": self.effort,
                    "format": {"type": "json_schema", "schema": RESPONSE_SCHEMA},
                },
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.NotFoundError as e:
            raise RuntimeError(f"Unknown Claude model '{self.model}': {e.message}") from e
        except anthropic.RateLimitError as e:
            retry_after = e.response.headers.get("retry-after", "unknown")
            raise RuntimeError(f"Rate limited after SDK retries (retry-after={retry_after}s)") from e
        except anthropic.APIStatusError as e:
            raise RuntimeError(f"Anthropic API error {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise RuntimeError(f"Network error calling the Anthropic API: {e}") from e
        latency = time.perf_counter() - started

        if response.stop_reason == "refusal":
            category = response.stop_details.category if response.stop_details else None
            text = ""
            note = f"refusal (category={category})"
        else:
            text = next((b.text for b in response.content if b.type == "text"), "")
            note = None

        return {
            "text": text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model_reported": response.model,
            "stop_reason": response.stop_reason,
            "request_id": response._request_id,
            "latency_s": round(latency, 3),
            "note": note,
        }
