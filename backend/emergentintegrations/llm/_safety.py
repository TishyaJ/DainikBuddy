"""
Safety filter for AI responses.
Screens AI output for medical diagnoses and self-harm content before delivery.
"""

import re
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ============ SAFE REPLACEMENT MESSAGES ============

_DIAGNOSIS_REPLACEMENT = (
    "I'm not qualified to diagnose medical conditions. "
    "Please consult a qualified healthcare professional for a proper evaluation and guidance."
)

_SELF_HARM_REPLACEMENT = (
    "If you're going through a difficult time, please reach out for support. "
    "In India: iCall (9152987821) or Vandrevala Foundation (1860-2662-345). "
    "You don't have to face this alone — professional help is available."
)


class SafetyFilter:
    """
    Screens AI output for blocked content patterns.

    check(text) returns (is_safe, replacement_text_or_None, filter_reason_or_None).
    If is_safe is False, replacement_text contains the safe alternative to show the user.
    """

    # Medical diagnosis patterns
    # Matches language where the AI claims the user HAS a specific condition
    DIAGNOSIS_PATTERNS = [
        re.compile(r"\byou\s+have\s+(depression|anxiety|adhd|bipolar|ocd|ptsd|schizophrenia|autism|disorder|syndrome|condition)\b", re.IGNORECASE),
        re.compile(r"\byou\s+are\s+diagnosed\s+with\b", re.IGNORECASE),
        re.compile(r"\byour\s+symptoms\s+(indicate|suggest|confirm|show)\s+(that\s+you\s+have\s+)?(a\s+)?(medical\s+)?(condition|disease|disorder)\b", re.IGNORECASE),
        re.compile(r"\bdiagnosis\s+is\b.*\b(depression|anxiety|disorder|syndrome)\b", re.IGNORECASE),
        re.compile(r"\byou\s+(clearly|definitely|obviously)\s+have\s+(a\s+)?(mental|physical)\s+(illness|disorder|condition)\b", re.IGNORECASE),
        re.compile(r"\bbased\s+on\s+your\s+symptoms?\s*[,;]?\s+you\s+have\b", re.IGNORECASE),
    ]

    # Self-harm / dangerous content patterns
    # Matches encouragement of self-harm or suicide methods
    SELF_HARM_PATTERNS = [
        re.compile(r"\b(you\s+should|try|consider)\s+(hurt(ing)?|harm(ing)?|cut(ting)?|kill(ing)?)\s+(your)?self\b", re.IGNORECASE),
        re.compile(r"\b(best|easiest|most\s+effective)\s+way\s+to\s+(commit\s+suicide|end\s+(your|one\'s)\s+life|kill\s+yourself)\b", re.IGNORECASE),
        re.compile(r"\bhow\s+to\s+(commit\s+suicide|overdose|self.harm|cut\s+yourself)\b", re.IGNORECASE),
        re.compile(r"\b(suicide|self.harm)\s+(method|technique|instruction|guide|how.to)\b", re.IGNORECASE),
        re.compile(r"\bend\s+(it\s+all|your\s+life|your\s+suffering)\s+(by|through|with)\b", re.IGNORECASE),
        re.compile(r"\b(encouraging|recommend(ing)?|suggest(ing)?)\s+self.?(harm|injury|hurt)\b", re.IGNORECASE),
        re.compile(r"\b(it\'?s?\s+okay|it\s+is\s+fine|go\s+ahead)\s+(to\s+)?(hurt|harm|cut|kill)\s+(your)?self\b", re.IGNORECASE),
    ]

    def check(self, text: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Check response text for blocked patterns.

        Returns:
            (is_safe, replacement_text, filter_reason)
            - is_safe=True: text passes; replacement_text and filter_reason are None
            - is_safe=False: replacement_text is the safe alternative; filter_reason describes what was caught
        """
        start = time.monotonic()

        if not text or not text.strip():
            return True, None, None

        # Check medical diagnosis patterns
        for pattern in self.DIAGNOSIS_PATTERNS:
            if pattern.search(text):
                elapsed_ms = (time.monotonic() - start) * 1000
                reason = f"medical_diagnosis_pattern: {pattern.pattern[:60]}..."
                logger.warning(
                    f"Safety filter triggered [{elapsed_ms:.1f}ms]: {reason}"
                )
                return False, _DIAGNOSIS_REPLACEMENT, reason

        # Check self-harm patterns
        for pattern in self.SELF_HARM_PATTERNS:
            if pattern.search(text):
                elapsed_ms = (time.monotonic() - start) * 1000
                reason = f"self_harm_pattern: {pattern.pattern[:60]}..."
                logger.warning(
                    f"Safety filter triggered [{elapsed_ms:.1f}ms]: {reason}"
                )
                return False, _SELF_HARM_REPLACEMENT, reason

        elapsed_ms = (time.monotonic() - start) * 1000
        if elapsed_ms > 50:
            logger.warning(f"Safety filter took {elapsed_ms:.1f}ms (exceeded 50ms target) for {len(text)} chars")

        return True, None, None


# Singleton instance for reuse
_filter = SafetyFilter()


def check_safety(text: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Module-level convenience function.
    Returns (is_safe, replacement_text_or_None, reason_or_None).
    """
    return _filter.check(text)
