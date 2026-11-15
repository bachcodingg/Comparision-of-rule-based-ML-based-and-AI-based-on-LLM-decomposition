"""One module per vendor, each using that vendor's own SDK."""


def build_provider(name: str, cfg: dict):
    cfg = cfg or {}
    if name == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(model=cfg.get("model"), effort=cfg.get("effort", "medium"),
                                 max_tokens=cfg.get("max_tokens", 16000))
    if name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(model=cfg.get("model"), temperature=cfg.get("temperature"),
                              max_tokens=cfg.get("max_tokens", 16000))
    if name == "gemini":
        from .gemini_provider import GeminiProvider
        return GeminiProvider(model=cfg.get("model"), temperature=cfg.get("temperature"),
                              max_tokens=cfg.get("max_tokens", 16000))
    raise ValueError(f"Unknown provider '{name}' (expected anthropic, openai or gemini)")
