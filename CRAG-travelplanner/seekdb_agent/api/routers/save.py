"""
Save API Router
================
保存行程到 Java 后端

POST /api/v1/session/{session_id}/save - 保存会话计划到 Java 后端
"""

import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from seekdb_agent.db.session import get_full_session_data
from seekdb_agent.utils.geocoding import enrich_pois_sync

logger = logging.getLogger(__name__)

router = APIRouter()

# Java API 配置
JAVA_API_URL = os.getenv("JAVA_API_URL", "http://localhost:8080")
JAVA_API_TIMEOUT = float(os.getenv("JAVA_API_TIMEOUT", "30.0"))


class SaveResponse(BaseModel):
    """保存响应模型"""

    status: str = Field(description="状态: success, error")
    itinerary_id: str | None = Field(default=None, description="Java 后端创建的行程 ID")
    message: str | None = Field(default=None, description="消息")


def _convert_pois_per_day_to_travel_pace(pois_per_day: int | None) -> str:
    """
    将每日 POI 数量转换为 Java TravelPace 枚举值

    Args:
        pois_per_day: 每天计划游览的景点数量

    Returns:
        TravelPace: RELAXED (2-3), MODERATE (4-5), PACKED (6+)
    """
    if pois_per_day is None:
        return "MODERATE"
    if pois_per_day <= 3:
        return "RELAXED"
    elif pois_per_day <= 5:
        return "MODERATE"
    else:
        return "PACKED"


def build_import_request(session_data: dict[str, Any]) -> dict[str, Any]:
    """
    组装 Java API 请求体

    Args:
        session_data: 从 get_full_session_data 获取的完整会话数据

    Returns:
        符合 Java ImportPlanRequest 结构的字典

    Note:
        POIs without coordinates will be enriched using Google Places API
        before sending to Java backend.
    """
    user_features = session_data.get("user_features", {})
    pois = session_data.get("recommended_pois", [])
    plan = session_data.get("suggested_plan", {})

    # Check if any POIs are missing coordinates
    pois_missing_coords = [
        p
        for p in pois
        if p.get("latitude") is None
        or p.get("longitude") is None
        or (p.get("latitude") == 0.0 and p.get("longitude") == 0.0)
    ]

    if pois_missing_coords:
        logger.info(
            f"[Save] {len(pois_missing_coords)}/{len(pois)} POIs missing coordinates, "
            "attempting enrichment via Google Places API"
        )
        destination = user_features.get("destination")
        try:
            pois = enrich_pois_sync(pois, destination=destination)
            enriched_count = sum(
                1
                for p in pois
                if p.get("latitude") is not None
                and p.get("longitude") is not None
                and not (p.get("latitude") == 0.0 and p.get("longitude") == 0.0)
            )
            logger.info(
                f"[Save] Coordinate enrichment complete: {enriched_count}/{len(pois)} POIs have valid coordinates"
            )
        except Exception as e:
            logger.warning(f"[Save] Coordinate enrichment failed: {e}")

    # 转换 pois_per_day 到 travelPace
    pois_per_day = user_features.get("pois_per_day")
    travel_pace = _convert_pois_per_day_to_travel_pace(pois_per_day)

    return {
        "cragSessionId": session_data.get("session_id"),
        "userFeatures": {
            "destination": user_features.get("destination", ""),
            "travelDays": user_features.get("travel_days", 3),
            "startDate": plan.get("start_date") or user_features.get("start_date"),
            "endDate": plan.get("end_date") or user_features.get("end_date"),
            "budgetCents": user_features.get("budget"),
            "interests": user_features.get("interests", []),
            "travelPace": travel_pace,
            "travelMode": user_features.get("transportation"),
            "numberOfTravelers": user_features.get("number_of_travelers"),
            "hasChildren": user_features.get("has_children"),
            "hasElderly": user_features.get("has_elderly"),
        },
        "pois": [
            {
                "externalId": poi.get("id"),
                "name": poi.get("name"),
                "latitude": poi.get("latitude", 0.0),
                "longitude": poi.get("longitude", 0.0),
                "address": poi.get("address", ""),
                "city": poi.get("city"),
                "description": poi.get("description") or poi.get("editorial_summary"),
                "imageUrl": poi.get("image_url"),
                "rating": poi.get("rating"),
                "reviewsCount": poi.get("reviews_count"),
                "priceLevel": poi.get("price_level"),
                "primaryCategory": poi.get("primary_category"),
                "openingHours": poi.get("opening_hours"),
            }
            for poi in pois
        ],
        "plan": {
            "destination": plan.get("destination", user_features.get("destination", "")),
            "startDate": plan.get("start_date"),
            "endDate": plan.get("end_date"),
            "days": [
                {
                    "date": day.get("date", ""),
                    "stops": [
                        {
                            "poiExternalId": stop.get("poi_id", ""),
                            "poiName": stop.get("poi_name", ""),
                            "arrivalTime": stop.get("arrival_time", ""),
                            "departureTime": stop.get("departure_time", ""),
                            "durationMinutes": stop.get("duration_minutes", 60),
                            "activity": stop.get("activity"),
                        }
                        for stop in day.get("stops", [])
                    ],
                }
                for day in plan.get("days", [])
            ],
        },
    }


@router.post("/session/{session_id}/save", response_model=SaveResponse)
async def save_session_plan(
    session_id: str,
    authorization: str = Header(..., description="Bearer token for Java API"),
) -> SaveResponse:
    """
    保存会话计划到 Java 后端

    流程：
    1. 从数据库获取 session 完整数据
    2. 组装 ImportPlanRequest
    3. 调用 Java POST /api/import-plan
    4. 返回结果

    Args:
        session_id: 会话 ID
        authorization: Bearer token（透传给 Java API）

    Returns:
        SaveResponse 包含状态和 itinerary_id

    Raises:
        HTTPException:
            - 404: Session 不存在
            - 400: Plan 未就绪
            - 503: Java API 不可用
    """
    logger.info(f"Save request for session: {session_id}")

    # 1. 获取 session 完整数据
    session_data = get_full_session_data(session_id)
    if not session_data:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. 检查 plan_ready
    if not session_data.get("plan_ready"):
        logger.warning(f"Plan not ready for session: {session_id}")
        raise HTTPException(status_code=400, detail="Plan not ready for saving")

    # 3. 检查是否有 POI 和 Plan 数据
    if not session_data.get("recommended_pois"):
        raise HTTPException(status_code=400, detail="No POIs found in session")

    if not session_data.get("suggested_plan"):
        raise HTTPException(status_code=400, detail="No plan found in session")

    # 4. 组装请求体
    import_request = build_import_request(session_data)
    logger.debug(f"Import request: {import_request}")

    # 5. 调用 Java API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{JAVA_API_URL}/api/import-plan",
                json=import_request,
                headers={"Authorization": authorization, "Content-Type": "application/json"},
                timeout=JAVA_API_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"Plan saved successfully. Itinerary ID: {result.get('itineraryId')}")

            return SaveResponse(
                status="success",
                itinerary_id=result.get("itineraryId"),
                message=f"Plan saved successfully. POIs: {result.get('importedPoisCount', 0)}",
            )

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"Java API HTTP error: {e.response.status_code} - {error_detail}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Java API error: {error_detail}",
            ) from e

        except httpx.RequestError as e:
            logger.error(f"Java API request error: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Java API unavailable: {e}",
            ) from e
