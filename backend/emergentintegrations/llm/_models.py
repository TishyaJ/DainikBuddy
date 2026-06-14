"""
Internal shared data models for the AI engine.
All types used across adapters, fallback handler, safety filter, and cache.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ============ EXCEPTIONS ============

class ConfigurationError(Exception):
    """Raised when a required API key or configuration value is missing."""
    pass


# ============ DATA MODELS ============

@dataclass
class AdapterConfig:
    """Configuration for a specific provider + model combination."""
    provider: str
    model: str
    api_key: str
    temperature: float = 0.7
    top_p: Optional[float] = None
    max_tokens: int = 1024


@dataclass
class UsageInfo:
    """Token usage data returned by LLM providers."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class StreamEvent:
    """Internal event type wrapping either content or completion signal."""
    content: Optional[str] = None
    is_done: bool = False
    usage: Optional[UsageInfo] = None


# ============ PROVIDER CONFIGURATION ============

# Environment variable names per provider
PROVIDER_ENV_KEYS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
}

SUPPORTED_PROVIDERS = frozenset(PROVIDER_ENV_KEYS.keys())


# ============ FALLBACK MESSAGES ============

FALLBACK_MESSAGES: dict[str, str] = {
    "finance": (
        "I'm having trouble connecting right now. In the meantime, "
        "check your expense log in the Expenses tab or review your budget "
        "allocations to stay on track."
    ),
    "wellness": (
        "I'm temporarily unavailable, but you're doing great by checking in. "
        "Try a quick breathing exercise: inhale for 4 counts, hold for 4, "
        "exhale for 4. I'll be back shortly."
    ),
    "discover": (
        "I can't connect right now. While I'm away, check your campus "
        "student portal or notice boards for deals and events. "
        "I'll be back to help soon!"
    ),
    "helper": (
        "I'm experiencing a brief interruption. Please try again in a moment. "
        "In the meantime, your expense logs, mood entries, and tasks are all "
        "accessible from the main tabs."
    ),
}


# ============ KEY RESOLUTION ============

def _resolve_api_key(provider: str, constructor_key: str) -> str:
    """
    Resolve the API key for a provider.

    Priority:
    1. constructor api_key (passed explicitly to LlmChat)
    2. Provider-specific environment variable (e.g., OPENAI_API_KEY)
    3. EMERGENT_LLM_KEY (legacy fallback for backward compatibility)

    Raises ConfigurationError at REQUEST TIME if no key is available.
    The server starts fine even with no keys (lazy init).
    """
    # 1. Constructor key takes highest priority
    if constructor_key and constructor_key.strip():
        return constructor_key.strip()

    # 2. Provider-specific env var
    env_var = PROVIDER_ENV_KEYS.get(provider, "")
    if env_var:
        key = os.environ.get(env_var, "").strip()
        if key:
            return key

    # 3. Legacy EMERGENT_LLM_KEY (maps to openai-style key)
    legacy = os.environ.get("EMERGENT_LLM_KEY", "").strip()
    if legacy:
        logger.warning(
            f"Using legacy EMERGENT_LLM_KEY for provider '{provider}'. "
            f"Set {env_var} for clarity."
        )
        return legacy

    # No key found — raise at request time (not at import/startup)
    env_name = PROVIDER_ENV_KEYS.get(provider, f"{provider.upper()}_API_KEY")
    raise ConfigurationError(
        f"No API key found for provider '{provider}'. "
        f"Set the environment variable {env_name} or pass api_key to LlmChat()."
    )
