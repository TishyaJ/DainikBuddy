"""
Analytics Router for PocketBuddy.
Provides endpoints for trend computation, spending anomaly detection,
monthly financial health reports, and habit recovery plan generation.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
"""

from fastapi import APIRouter, Depends, Query
from jwt_middleware import get_current_user
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os

import analytics_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@analytics_router.get("/trends")
async def get_trends(
    period: str = Query("weekly", regex="^(weekly|monthly)$"),
    user_id: str = Depends(get_current_user),
):
    """
    Compute trend lines for spending, mood, sleep, and habit consistency.

    - Weekly trends require minimum 7 days of data.
    - Monthly trends require minimum 28 days of data.
    - Returns spending by category, average mood, average sleep, habit consistency,
      and optional comparison with prior period.

    Validates: Requirements 6.1, 6.2
    Property 18: Trend Computation Data Sufficiency
    """
    result = await analytics_service.compute_trends(db, user_id, period=period)
    return result


@analytics_router.get("/anomalies")
async def get_anomalies(user_id: str = Depends(get_current_user)):
    """
    Detect spending anomalies over the last 30 days.

    Flags days where daily spend exceeds 2× the 30-day daily average.
    Each anomaly includes the anomalous amount, the 30-day daily average,
    and the percentage deviation.

    Validates: Requirement 6.3
    Property 19: Spending Anomaly Threshold Detection
    """
    anomalies = await analytics_service.detect_anomalies(db, user_id)
    return {"anomalies": anomalies, "count": len(anomalies)}


@analytics_router.get("/monthly-report")
async def get_monthly_report(user_id: str = Depends(get_current_user)):
    """
    Generate monthly financial health report.

    Includes: total income vs spending, category-wise budget adherence,
    savings goal progress, and predicted month-end balance based on
    current spending trajectory.

    Validates: Requirement 6.4
    """
    report = await analytics_service.generate_monthly_report(db, user_id)
    return report


@analytics_router.get("/recovery-plan")
async def get_recovery_plan(user_id: str = Depends(get_current_user)):
    """
    Generate personalized habit recovery plan.

    Triggered when habit consistency drops below 40% for 14 consecutive days.
    Suggests up to 3 specific schedule adjustments based on user's energy
    peak and self-care preferences.

    Validates: Requirement 6.5
    Property 20: Habit Decline Triggers Recovery Plan
    """
    plan = await analytics_service.generate_recovery_plan(db, user_id)
    return plan
