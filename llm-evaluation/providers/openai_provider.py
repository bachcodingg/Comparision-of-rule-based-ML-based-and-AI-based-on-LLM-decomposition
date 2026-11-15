"""OpenAI models via the official OpenAI SDK (Chat Completions, strict JSON schema).

No default model is set: choose the model under evaluation in config.yaml and
record its exact ID. `temperature` is sent only when configured, because
reasoning models reject non-default values.

NOT yet exercised against the live API in this repository (no key was
available when it was written). Run `run_eval.py --providers openai --limit 1`
once before a full run.
"""

from __future__ import annotations

import time

from openai import OpenAI

from prompt import RESPONSE_SCHEMA


class OpenAIProvider:
    name = "openai"

    def __init__(self, model: str | None = None, temperature: float | None = None, max_tokens: int = 16000):
        if not model:
            raise ValueError("Set providers.openai.model in config.yaml to the exact model ID you are evaluating.")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = OpenAI()  # reads OPENAI_API_KEY

    def settings(self) -> dict:
        return {"model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens}

    def complete(self, prompt: str) -> dict:
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": self.max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "god_class_review", "strict": True, "schema": RESPONSE_SCHEMA},
            },
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        started = time.perf_counter()
        response = self.client.chat.completions.create(**kwargs)
        latency = time.perf_counter() - started

        choice = response.choices[0]
        return {
            "text": choice.message.content or "",
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "model_reported": response.model,
            "stop_reason": choice.finish_reason,
            "request_id": getattr(response, "_request_id", None),
            "latency_s": round(latency, 3),
            "note": getattr(choice.message, "refusal", None),
        }
