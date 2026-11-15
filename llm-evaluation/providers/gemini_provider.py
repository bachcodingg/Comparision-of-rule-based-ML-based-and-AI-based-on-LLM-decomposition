"""Gemini models via the google-genai SDK (JSON response mode).

No default model is set: choose the model under evaluation in config.yaml and
record its exact ID ("Gemini Pro" without a version cannot be reproduced).

NOT yet exercised against the live API in this repository (the SDK and a key
were not available when it was written). Install with `pip install google-genai`
and run `run_eval.py --providers gemini --limit 1` once before a full run.
"""

from __future__ import annotations

import time

from prompt import JSON_INSTRUCTION


class GeminiProvider:
    name = "gemini"

    def __init__(self, model: str | None = None, temperature: float | None = None, max_tokens: int = 16000):
        if not model:
            raise ValueError("Set providers.gemini.model in config.yaml to the exact model ID you are evaluating.")
        from google import genai  # imported here so the other providers work without this package

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = genai.Client()  # reads GEMINI_API_KEY or GOOGLE_API_KEY

    def settings(self) -> dict:
        return {"model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens}

    def complete(self, prompt: str) -> dict:
        from google.genai import types

        config_kwargs = {
            "response_mime_type": "application/json",
            "max_output_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            config_kwargs["temperature"] = self.temperature

        started = time.perf_counter()
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt + JSON_INSTRUCTION,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        latency = time.perf_counter() - started

        usage = response.usage_metadata
        candidate = response.candidates[0] if response.candidates else None
        return {
            "text": response.text or "",
            "input_tokens": getattr(usage, "prompt_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None),
            "model_reported": getattr(response, "model_version", self.model),
            "stop_reason": str(candidate.finish_reason) if candidate else None,
            "request_id": getattr(response, "response_id", None),
            "latency_s": round(latency, 3),
            "note": None,
        }
