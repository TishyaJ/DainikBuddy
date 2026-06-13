"""
Quick diagnostic script to fix auth issues.

Problem: "Account already exists" on signup + "Invalid credentials" on login
Cause: Stale user record in MongoDB with a password hash that doesn't match

Usage:
    python fix_auth.py --check <email>       # Check if user exists and inspect record
    python fix_auth.py --delete <email>      # Delete the user so you can re-register
    python fix_auth.py --reset <email> <pw>  # Reset password for existing user
    python fix_auth.py --list                # List all registered users
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).parent / '.env')

mongo_url = os.environ.get('MONGO_URL', '')
db_name = os.environ.get('DB_NAME', 'pocketbuddy')


async def main():
    if not mongo_url:
        print("ERROR: MONGO_URL not set in backend/.env")
        print("Make sure your .env has: MONGO_URL=mongodb://...")
        sys.exit(1)

    print(f"Connecting to: {mongo_url[:40]}...")
    print(f"Database: {db_name}")

    try:
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        # Test connection
        await client.server_info()
        print("✓ MongoDB connection successful\n")
    except Exception as e:
        print(f"✗ MongoDB connection FAILED: {e}")
        print("\nCheck your backend/.env file has correct MONGO_URL")
        sys.exit(1)

    db = client[db_name]

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    action = sys.argv[1]

    if action == "--list":
        users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
        if not users:
            print("No users found in database.")
        else:
            print(f"Found {len(users)} user(s):\n")
            for u in users:
                print(f"  Email: {u.get('email')}")
                print(f"  ID:    {u.get('id')}")
                print(f"  Created: {u.get('created_at')}")
                print(f"  Failed attempts: {u.get('failed_login_attempts', 0)}")
                print(f"  Locked until: {u.get('locked_until', 'Not locked')}")
                print()

    elif action == "--check":
        if len(sys.argv) < 3:
            print("Usage: python fix_auth.py --check <email>")
            sys.exit(1)
        email = sys.argv[2].strip().lower()
        user = await db.users.find_one({"email": email}, {"_id": 0})
        if not user:
            print(f"No user found with email: {email}")
            print("You should be able to register with this email.")
        else:
            print(f"User found:")
            print(f"  Email: {user.get('email')}")
            print(f"  ID: {user.get('id')}")
            print(f"  Created: {user.get('created_at')}")
            print(f"  Last login: {user.get('last_login_at')}")
            print(f"  Failed attempts: {user.get('failed_login_attempts', 0)}")
            print(f"  Locked until: {user.get('locked_until')}")
            print(f"  Has password hash: {'Yes' if user.get('password_hash') else 'No'}")
            print(f"  Has refresh token: {'Yes' if user.get('refresh_token_hash') else 'No'}")
            print()
            print("This user exists, so registration will fail.")
            print("To fix: run  python fix_auth.py --delete " + email)
            print("   or:  run  python fix_auth.py --reset " + email + " <new_password>")

    elif action == "--delete":
        if len(sys.argv) < 3:
            print("Usage: python fix_auth.py --delete <email>")
            sys.exit(1)
        email = sys.argv[2].strip().lower()
        user = await db.users.find_one({"email": email})
        if not user:
            print(f"No user found with email: {email}")
            sys.exit(0)
        user_id = user["id"]
        # Delete user and all their data
        await db.users.delete_one({"email": email})
        for coll in ["mood_entries", "expenses", "journal_entries", "goals",
                     "budget_categories", "subscriptions", "savings_goals",
                     "split_bills", "sleep_entries", "chat_messages",
                     "user_profiles", "tasks", "task_sessions",
                     "exercises", "exercise_sessions", "password_resets"]:
            await db[coll].delete_many({"user_id": user_id})
        print(f"✓ Deleted user '{email}' and all associated data.")
        print("You can now register again with this email.")

    elif action == "--reset":
        if len(sys.argv) < 4:
            print("Usage: python fix_auth.py --reset <email> <new_password>")
            sys.exit(1)
        email = sys.argv[2].strip().lower()
        new_password = sys.argv[3]

        from auth_service import hash_password, validate_password
        valid, err = validate_password(new_password)
        if not valid:
            print(f"Invalid password: {err}")
            sys.exit(1)

        user = await db.users.find_one({"email": email})
        if not user:
            print(f"No user found with email: {email}")
            sys.exit(1)

        new_hash = hash_password(new_password)
        await db.users.update_one(
            {"email": email},
            {"$set": {
                "password_hash": new_hash,
                "failed_login_attempts": 0,
                "locked_until": None,
            }}
        )
        print(f"✓ Password reset for '{email}'")
        print(f"  You can now login with the new password.")

    else:
        print(f"Unknown action: {action}")
        print(__doc__)

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
