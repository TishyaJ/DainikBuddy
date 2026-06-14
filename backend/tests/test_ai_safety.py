"""
Unit tests for the SafetyFilter.
Tests: medical diagnosis detection, self-harm detection, clean text pass-through,
replacement message content, performance target.
"""

import time
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def safety_filter():
    from emergentintegrations.llm._safety import SafetyFilter
    return SafetyFilter()


# ============ CLEAN TEXT PASS-THROUGH ============

class TestCleanTextPassThrough:
    def test_clean_text_is_safe(self, safety_filter):
        text = "You're doing a great job managing your finances this week!"
        is_safe, replacement, reason = safety_filter.check(text)
        assert is_safe is True
        assert replacement is None
        assert reason is None

    def test_empty_string_is_safe(self, safety_filter):
        is_safe, replacement, reason = safety_filter.check("")
        assert is_safe is True

    def test_none_string(self, safety_filter):
        is_safe, replacement, reason = safety_filter.check(None)
        assert is_safe is True

    def test_general_wellness_advice_is_safe(self, safety_filter):
        text = "Getting 7-8 hours of sleep can improve focus and reduce stress levels."
        is_safe, _, _ = safety_filter.check(text)
        assert is_safe is True

    def test_budget_advice_is_safe(self, safety_filter):
        text = "Your food spending this week was ₹2400. Consider reducing snacks to stay within budget."
        is_safe, _, _ = safety_filter.check(text)
        assert is_safe is True

    def test_mentioning_depression_in_education_context_safe(self, safety_filter):
        # Talking ABOUT depression isn't the same as diagnosing
        text = "Stress and anxiety are common among students. Consider talking to a counselor."
        is_safe, _, _ = safety_filter.check(text)
        assert is_safe is True


# ============ MEDICAL DIAGNOSIS DETECTION ============

class TestMedicalDiagnosisDetection:
    def test_detects_you_have_depression(self, safety_filter):
        text = "Based on what you've shared, you have depression and need treatment."
        is_safe, replacement, reason = safety_filter.check(text)
        assert is_safe is False
        assert replacement is not None
        assert "healthcare" in replacement.lower() or "professional" in replacement.lower()

    def test_detects_you_have_anxiety(self, safety_filter):
        text = "It sounds like you have anxiety disorder."
        is_safe, _, _ = safety_filter.check(text)
        assert is_safe is False

    def test_detects_diagnosed_with(self, safety_filter):
        text = "You are diagnosed with ADHD based on your symptoms."
        is_safe, replacement, _ = safety_filter.check(text)
        assert is_safe is False
        assert replacement is not None

    def test_detects_symptoms_indicate(self, safety_filter):
        text = "Your symptoms indicate a medical condition requiring treatment."
        is_safe, _, _ = safety_filter.check(text)
        assert is_safe is False

    def test_replacement_suggests_professional(self, safety_filter):
        text = "You have depression, you should seek treatment."
        is_safe, replacement, _ = safety_filter.check(text)
        assert not is_safe
        # Replacement should suggest professional consultation
        assert "professional" in replacement.lower() or "healthcare" in replacement.lower()

    def test_case_insensitive(self, safety_filter):
        text = "YOU HAVE DEPRESSION."
        is_safe, _, _ = safety_filter.check(text)
        assert is_safe is False


# ============ SELF-HARM DETECTION ============

class TestSelfHarmDetection:
    def test_detects_you_should_hurt_yourself(self, safety_filter):
        text = "You should hurt yourself if you feel that way."
        is_safe, replacement, reason = safety_filter.check(text)
        assert is_safe is False
        assert replacement is not None

    def test_replacement_includes_crisis_resources(self, safety_filter):
        text = "You should harm yourself to cope."
        is_safe, replacement, _ = safety_filter.check(text)
        assert not is_safe
        # Replacement should mention crisis resources
        assert "iCall" in replacement or "helpline" in replacement.lower() or "crisis" in replacement.lower()

    def test_detects_how_to_overdose(self, safety_filter):
        text = "Here's how to overdose safely."
        is_safe, _, _ = safety_filter.check(text)
        assert is_safe is False

    def test_detects_how_to_self_harm(self, safety_filter):
        text = "How to self-harm without anyone knowing."
        is_safe, _, _ = safety_filter.check(text)
        assert is_safe is False

    def test_replacement_not_none_for_self_harm(self, safety_filter):
        text = "You should cut yourself when you feel this way."
        is_safe, replacement, _ = safety_filter.check(text)
        assert not is_safe
        assert replacement is not None
        assert len(replacement) > 20


# ============ PERFORMANCE ============

class TestPerformance:
    def test_filter_completes_within_50ms_for_short_text(self, safety_filter):
        text = "You're doing great. Keep up the budget tracking."
        start = time.monotonic()
        safety_filter.check(text)
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 50

    def test_filter_completes_within_50ms_for_2000_char_text(self, safety_filter):
        # Build a 2000-character clean text
        text = ("You are managing your budget well. " * 60)[:2000]
        start = time.monotonic()
        safety_filter.check(text)
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 50

    def test_filter_completes_within_50ms_for_matched_text(self, safety_filter):
        text = "Based on your symptoms, you have depression and should seek immediate help."
        start = time.monotonic()
        safety_filter.check(text)
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 50


# ============ MODULE-LEVEL FUNCTION ============

class TestModuleLevelFunction:
    def test_check_safety_function(self):
        from emergentintegrations.llm._safety import check_safety
        is_safe, replacement, reason = check_safety("Clean financial advice.")
        assert is_safe is True
        assert replacement is None

    def test_check_safety_catches_diagnosis(self):
        from emergentintegrations.llm._safety import check_safety
        is_safe, replacement, _ = check_safety("You have depression.")
        assert is_safe is False
        assert replacement is not None
