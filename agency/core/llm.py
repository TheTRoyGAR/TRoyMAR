import os
from crewai import LLM

OPUS = "anthropic/claude-opus-4-8"
SONNET = "anthropic/claude-sonnet-4-6"
HAIKU = "anthropic/claude-haiku-4-5-20251001"


def get_llm(tier: str = "sonnet") -> LLM:
    model = {"opus": OPUS, "sonnet": SONNET, "haiku": HAIKU}.get(tier, SONNET)
    # Without an explicit max_tokens, this defaults to 4096 — long tool
    # calls (e.g. FileWriterTool writing a full report as one `content`
    # argument) get truncated mid-generation into malformed JSON, which
    # CrewAI then retries forever instead of failing, burning real API
    # spend on every retry without ever completing. (Same real bug found
    # and fixed in TRoyAI's agency/core/llm.py — carried over here.)
    # No `temperature` kwarg for any tier: the installed anthropic SDK's
    # Messages.create() no longer accepts it at all (confirmed 2026-09-14 —
    # removed from the method signature entirely, not just rejected by the
    # API for Opus as the old comment here claimed). Every sonnet/haiku call
    # was silently failing with "unexpected keyword argument 'temperature'"
    # until this fix — same real bug already found and fixed in TRoyAI.
    kwargs = {"model": model, "api_key": os.getenv("ANTHROPIC_API_KEY"), "max_tokens": 8192}
    return LLM(**kwargs)
