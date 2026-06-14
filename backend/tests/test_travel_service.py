"""
Property-based tests for TravelService fare formula using Hypothesis.

**Validates: Requirements 2.6**

Tests cover:
- Property 2: Fare Formula Non-Negativity and Determinism
- Property 3: Fare Formula Mode Appropriateness
"""

import sys
import os
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from discover_travel_service import TravelService


# Instantiate TravelService with None db — formula doesn't use DB
service = TravelService(None)


# ============ PROPERTY 2: Fare Formula Non-Negativity and Determinism ============

class TestProperty2FareFormulaNonNegativityAndDeterminism:
    """
    Property 2: Fare Formula Non-Negativity and Determinism
    For any positive distance value, the fare formula SHALL produce route options
    where every cost field is >= 0, AND calling it twice with the same distance
    SHALL produce identical results.

    **Validates: Requirements 2.6**
    """

    @given(distance=st.floats(min_value=0.1, max_value=500))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_fare_formula_non_negativity_and_determinism(self, distance):
        """All fare costs are non-negative and results are deterministic."""
        # First call
        routes_1 = service.estimate_via_formula(distance)

        # Verify non-negativity: all costs must be >= 0
        for route in routes_1:
            assert route["cost"] >= 0, (
                f"Negative cost {route['cost']} for mode '{route['mode']}' "
                f"at distance {distance} km"
            )

        # Second call with same distance — verify determinism
        routes_2 = service.estimate_via_formula(distance)
        assert routes_1 == routes_2, (
            f"Non-deterministic output for distance {distance} km: "
            f"first call produced {len(routes_1)} routes, "
            f"second call produced {len(routes_2)} routes"
        )


# ============ PROPERTY 3: Fare Formula Mode Appropriateness ============

class TestProperty3FareFormulaModeAppropriateness:
    """
    Property 3: Fare Formula Mode Appropriateness
    For any distance >= 5km, estimate_via_formula SHALL NOT include "Cycle Rickshaw".
    For any distance >= 3km, it SHALL NOT include "Walk".
    For any distance < 3km, Walk SHALL be included with cost 0.

    **Validates: Requirements 2.6**
    """

    @given(distance=st.floats(min_value=0.1, max_value=500))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_fare_formula_mode_appropriateness(self, distance):
        """Mode inclusion/exclusion follows distance constraints."""
        routes = service.estimate_via_formula(distance)
        modes = [r["mode"] for r in routes]

        # If distance >= 5: Cycle Rickshaw should NOT appear
        if distance >= 5:
            assert "Cycle Rickshaw" not in modes, (
                f"Cycle Rickshaw should not appear for distance {distance} km (>= 5km)"
            )

        # If distance >= 3: Walk should NOT appear
        if distance >= 3:
            assert "Walk" not in modes, (
                f"Walk should not appear for distance {distance} km (>= 3km)"
            )

        # If distance < 3: Walk SHOULD appear with cost 0
        if distance < 3:
            assert "Walk" in modes, (
                f"Walk should appear for distance {distance} km (< 3km)"
            )
            walk_route = next(r for r in routes if r["mode"] == "Walk")
            assert walk_route["cost"] == 0, (
                f"Walk cost should be 0, got {walk_route['cost']} "
                f"for distance {distance} km"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============ PROPERTY 7: Empty/Whitespace Input Rejection ============

from starlette.testclient import TestClient
from server import app
from jwt_middleware import get_current_user

# Override auth dependency so tests don't need real JWT tokens
app.dependency_overrides[get_current_user] = lambda: "test_user"

# Use synchronous TestClient to avoid event loop conflicts with hypothesis
_client = TestClient(app, raise_server_exceptions=False)

# Strategy for generating whitespace-only strings: characters that Python's .strip() removes.
# This includes ASCII whitespace (\t, \n, \r, \x0b, \x0c, space) plus Unicode whitespace
# (category Zs) and a few Cc chars that Python treats as whitespace.
_WHITESPACE_CHARS = "".join(
    chr(c) for c in range(0x10000) if chr(c).strip() == "" and chr(c) != ""
)
whitespace_text = st.text(
    alphabet=_WHITESPACE_CHARS,
    min_size=0,
    max_size=20,
)


class TestProperty7EmptyWhitespaceInputRejection:
    """
    Property 7: Empty/Whitespace Input Rejection
    For any string composed entirely of whitespace (or empty), submitting it as
    source or destination to POST /discover/routes SHALL result in HTTP 400 rejection.

    **Validates: Requirements 2.7**
    """

    @given(source=whitespace_text, destination=whitespace_text)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_whitespace_source_and_destination_rejected(self, source, destination):
        """POST /discover/routes returns 400 when both source and destination are whitespace/empty."""
        response = _client.post("/api/discover/routes", json={"from": source, "to": destination})
        assert response.status_code == 400, (
            f"Expected 400 for whitespace inputs, got {response.status_code}. "
            f"source={repr(source)}, destination={repr(destination)}"
        )

    @given(source=whitespace_text)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_whitespace_source_with_valid_destination_rejected(self, source):
        """POST /discover/routes returns 400 when source is whitespace/empty (destination valid)."""
        response = _client.post("/api/discover/routes", json={"from": source, "to": "Mumbai"})
        assert response.status_code == 400, (
            f"Expected 400 for whitespace source, got {response.status_code}. "
            f"source={repr(source)}"
        )

    @given(destination=whitespace_text)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_whitespace_destination_with_valid_source_rejected(self, destination):
        """POST /discover/routes returns 400 when destination is whitespace/empty (source valid)."""
        response = _client.post("/api/discover/routes", json={"from": "Delhi", "to": destination})
        assert response.status_code == 400, (
            f"Expected 400 for whitespace destination, got {response.status_code}. "
            f"destination={repr(destination)}"
        )
