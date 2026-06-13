"""
Categorization Service for PocketBuddy.

Provides user-specific merchant-to-category rule storage and lookup.
Implements a cascading categorization strategy:
  1. User-specific rules (case-insensitive exact match on merchant name)
  2. Keyword-based detection (existing logic)
  3. Default to "misc"

Stores rules in `user_category_rules` collection with compound unique index
on (user_id, merchant_lower). Supports up to 500 rules per user.
"""

from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

MAX_RULES_PER_USER = 500


def _keyword_detect_category(text: str) -> Optional[str]:
    """Keyword-based category detection. Returns category or None if no match."""
    t = (text or "").lower()
    if any(k in t for k in ["pizza", "burger", "mess", "food", "lunch", "dinner", "snack", "coffee", "tea", "thali"]):
        return "food"
    if any(k in t for k in ["uber", "ola", "metro", "bus", "auto", "taxi", "fuel", "petrol", "ride"]):
        return "transport"
    if any(k in t for k in ["movie", "netflix", "game", "concert", "ticket"]):
        return "entertainment"
    if any(k in t for k in ["book", "course", "udemy", "stationery", "tuition", "print"]):
        return "education"
    return None


async def get_user_rule(db: AsyncIOMotorDatabase, user_id: str, merchant: str) -> Optional[str]:
    """
    Look up a user-specific categorization rule for a merchant.
    Returns the category if a rule exists, None otherwise.
    Case-insensitive exact match on merchant name.
    """
    if not merchant or not merchant.strip():
        return None

    merchant_lower = merchant.strip().lower()
    rule = await db.user_category_rules.find_one(
        {"user_id": user_id, "merchant_lower": merchant_lower},
        {"_id": 0}
    )
    if rule:
        return rule["category"]
    return None


async def categorize_expense(db: AsyncIOMotorDatabase, user_id: str, merchant: str, note: str = "") -> tuple[str, bool]:
    """
    Categorize an expense using the cascading strategy:
      1. User-specific rules (case-insensitive exact match on merchant)
      2. Keyword-based detection (merchant + note text)
      3. Default to "misc"

    Returns a tuple of (category, is_misc) where is_misc indicates if the
    category was defaulted to "misc" (user should be prompted to confirm/correct).
    """
    # Step 1: Check user-specific rules
    user_category = await get_user_rule(db, user_id, merchant)
    if user_category:
        return user_category, False

    # Step 2: Keyword-based detection
    combined_text = f"{merchant} {note}"
    keyword_category = _keyword_detect_category(combined_text)
    if keyword_category:
        return keyword_category, False

    # Step 3: Default to "misc"
    return "misc", True


async def store_category_rule(db: AsyncIOMotorDatabase, user_id: str, merchant: str, category: str) -> dict:
    """
    Store or overwrite a user-specific categorization rule.

    - Case-insensitive exact match on merchant name
    - Overwrites existing rule for the same merchant
    - Enforces max 500 rules per user (rejects if at capacity and merchant is new)

    Returns dict with status info:
      {"success": True, "action": "created"|"updated"}
      or {"success": False, "reason": "..."}
    """
    if not merchant or not merchant.strip():
        return {"success": False, "reason": "Merchant name is required"}

    if not category or not category.strip():
        return {"success": False, "reason": "Category is required"}

    merchant_lower = merchant.strip().lower()
    now = datetime.now(timezone.utc).isoformat()

    # Check if rule already exists for this merchant
    existing = await db.user_category_rules.find_one(
        {"user_id": user_id, "merchant_lower": merchant_lower}
    )

    if existing:
        # Overwrite existing rule
        await db.user_category_rules.update_one(
            {"user_id": user_id, "merchant_lower": merchant_lower},
            {"$set": {"category": category.strip(), "updated_at": now}}
        )
        return {"success": True, "action": "updated"}

    # Check capacity before creating new rule
    rule_count = await db.user_category_rules.count_documents({"user_id": user_id})
    if rule_count >= MAX_RULES_PER_USER:
        return {"success": False, "reason": f"Maximum of {MAX_RULES_PER_USER} rules reached"}

    # Create new rule
    await db.user_category_rules.insert_one({
        "user_id": user_id,
        "merchant_lower": merchant_lower,
        "category": category.strip(),
        "updated_at": now
    })
    return {"success": True, "action": "created"}


async def ensure_indexes(db: AsyncIOMotorDatabase):
    """Create necessary indexes for the user_category_rules collection."""
    await db.user_category_rules.create_index(
        [("user_id", 1), ("merchant_lower", 1)],
        unique=True
    )
