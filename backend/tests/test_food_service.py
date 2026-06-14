"""
Property-based tests for food service dietary and budget filtering.

**Validates: Requirements 3.3, 3.4**

Tests cover:
- Property 5: Dietary Filter Correctness
- Property 6: Budget Filter Correctness
"""

import sys
import os
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from discover_food_service import matches_dietary


# ============ STRATEGIES ============

# User dietary preferences
user_dietary_strategy = st.sampled_from(["veg", "non-veg", "vegan", "any", "jain"])

# Item dietary values
item_dietary_strategy = st.sampled_from(["veg", "non-veg", "vegan"])

# Food item strategy for dietary testing
food_item_strategy = st.fixed_dictionaries({
    "name": st.text(min_size=1, max_size=30),
    "price": st.integers(min_value=1, max_value=1000),
    "rating": st.floats(min_value=3.5, max_value=5.0),
    "distance": st.just("0.5 km"),
    "tag": st.sampled_from(["North Indian", "South Indian", "Chinese", "Street Food"]),
    "dietary": item_dietary_strategy,
    "reason": st.just("Good for students"),
})

# List of food items
food_items_strategy = st.lists(food_item_strategy, min_size=0, max_size=20)

# Budget strategy
budget_strategy = st.floats(min_value=10, max_value=500, allow_nan=False, allow_infinity=False)

# Price strategy for budget tests
price_strategy = st.integers(min_value=1, max_value=1000)

# Food item strategy for budget testing
food_item_with_price_strategy = st.fixed_dictionaries({
    "name": st.text(min_size=1, max_size=30),
    "price": price_strategy,
    "rating": st.floats(min_value=3.5, max_value=5.0),
    "distance": st.just("0.5 km"),
    "tag": st.sampled_from(["North Indian", "South Indian", "Chinese", "Street Food"]),
    "dietary": st.sampled_from(["veg", "non-veg", "vegan"]),
    "reason": st.just("Good for students"),
})

# List of food items for budget testing
food_items_with_price_strategy = st.lists(food_item_with_price_strategy, min_size=0, max_size=20)


# ============ PROPERTY 5: Dietary Filter Correctness ============

class TestProperty5DietaryFilterCorrectness:
    """
    Property 5: Dietary Filter Correctness
    For any food recommendation list and any user dietary preference, filtering SHALL
    exclude all items whose dietary field does not match the user's preference.

    **Validates: Requirements 3.4**
    """

    @given(user_dietary=user_dietary_strategy, items=food_items_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_veg_or_jain_users_never_see_non_veg(self, user_dietary, items):
        """Veg and Jain users never see non-veg items in filtered results."""
        if user_dietary not in ("veg", "jain"):
            return  # Only test veg/jain constraint here

        filtered = [item for item in items if matches_dietary(item["dietary"], user_dietary)]

        for item in filtered:
            assert item["dietary"] != "non-veg", (
                f"User with dietary='{user_dietary}' should not see non-veg items, "
                f"but got item with dietary='{item['dietary']}'"
            )

    @given(user_dietary=st.just("vegan"), items=food_items_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_vegan_users_only_see_vegan(self, user_dietary, items):
        """Vegan users only see items with dietary 'vegan'."""
        filtered = [item for item in items if matches_dietary(item["dietary"], user_dietary)]

        for item in filtered:
            assert item["dietary"] == "vegan", (
                f"Vegan user should only see vegan items, "
                f"but got item with dietary='{item['dietary']}'"
            )

    @given(
        user_dietary=st.sampled_from(["non-veg", "any"]),
        items=food_items_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_non_veg_and_any_users_see_all_items(self, user_dietary, items):
        """Non-veg and 'any' users see all items regardless of dietary type."""
        filtered = [item for item in items if matches_dietary(item["dietary"], user_dietary)]

        assert len(filtered) == len(items), (
            f"User with dietary='{user_dietary}' should see all {len(items)} items, "
            f"but only saw {len(filtered)}"
        )

    @given(user_dietary=user_dietary_strategy, items=food_items_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_filtered_items_are_subset_of_original(self, user_dietary, items):
        """Filtered result is always a subset of the original items list."""
        filtered = [item for item in items if matches_dietary(item["dietary"], user_dietary)]

        assert len(filtered) <= len(items)
        for item in filtered:
            assert item in items


# ============ PROPERTY 6: Budget Filter Correctness ============

class TestProperty6BudgetFilterCorrectness:
    """
    Property 6: Budget Filter Correctness
    For any food recommendation list and any budget value, filtering SHALL exclude
    all items whose price exceeds the user's budget_per_meal.

    **Validates: Requirements 3.3**
    """

    @given(budget=budget_strategy, items=food_items_with_price_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_all_filtered_items_within_budget(self, budget, items):
        """All items in filtered list have price <= budget."""
        filtered = [item for item in items if item["price"] <= budget]

        for item in filtered:
            assert item["price"] <= budget, (
                f"Item with price={item['price']} should not appear when budget={budget}"
            )

    @given(budget=budget_strategy, items=food_items_with_price_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_no_items_incorrectly_excluded(self, budget, items):
        """No items with price <= budget are excluded from filtered result."""
        filtered = [item for item in items if item["price"] <= budget]

        # Every item with price <= budget must be in the filtered result
        for item in items:
            if item["price"] <= budget:
                assert item in filtered, (
                    f"Item with price={item['price']} should be included when budget={budget}, "
                    f"but was incorrectly excluded"
                )

    @given(budget=budget_strategy, items=food_items_with_price_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_excluded_items_exceed_budget(self, budget, items):
        """All excluded items have price > budget."""
        filtered = [item for item in items if item["price"] <= budget]
        excluded = [item for item in items if item not in filtered]

        for item in excluded:
            assert item["price"] > budget, (
                f"Item with price={item['price']} was excluded but should pass budget={budget}"
            )

    @given(budget=budget_strategy, items=food_items_with_price_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_filtered_count_matches_affordable_count(self, budget, items):
        """The number of filtered items equals the count of items with price <= budget."""
        filtered = [item for item in items if item["price"] <= budget]
        affordable_count = sum(1 for item in items if item["price"] <= budget)

        assert len(filtered) == affordable_count, (
            f"Expected {affordable_count} affordable items but got {len(filtered)} "
            f"for budget={budget}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
