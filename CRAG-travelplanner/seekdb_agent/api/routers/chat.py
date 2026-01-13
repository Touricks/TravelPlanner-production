"""
Chat API Router
===============
对话接口 - 调用 LangGraph 工作流

POST /api/v1/chat - 对话接口（同步）
POST /api/v1/chat/stream - 对话接口（SSE 流式，带进度推送）

更新记录:
- 2026-01-12: 添加 SSE 流式端点，支持实时进度推送
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from sse_starlette.sse import EventSourceResponse

from seekdb_agent.api.schemas import (
    ChatRequest,
    ChatResponse,
    POIForExport,
    SuggestedDay,
    SuggestedPlan,
    SuggestedStop,
)
from seekdb_agent.db.session import (
    generate_session_id,
    get_full_session_data,
    load_session_state,
    save_session_history,
)
from seekdb_agent.graph import app as crag_graph
from seekdb_agent.state import POIResult
from seekdb_agent.utils.progress import reset_progress_callback, set_progress_callback

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_recovery_response(session_id: str, session_state: dict[str, Any]) -> ChatResponse:
    """
    快速构建会话恢复响应（不调用 LLM）

    Args:
        session_id: 会话 ID
        session_state: 从数据库加载的基础会话状态

    Returns:
        ChatResponse 包含恢复的会话数据
    """
    # 获取完整会话数据（包括 POI 和 Plan）
    full_data = get_full_session_data(session_id)

    if not full_data:
        # 会话不存在或已过期
        return ChatResponse(
            session_id=session_id,
            message="会话不存在或已过期，请开始新对话。",
            user_features=None,
            feature_complete=False,
            plan_ready=False,
            recommended_pois=None,
            suggested_plan=None,
        )

    # 提取最后一条 AI 消息
    messages = session_state.get("messages", [])
    ai_messages = [m for m in messages if isinstance(m, AIMessage)]
    last_message = str(ai_messages[-1].content) if ai_messages else "会话已恢复。"

    # 转换 user_features
    user_features = full_data.get("user_features")

    # 转换 recommended_pois（已是 dict 列表）
    pois_raw = full_data.get("recommended_pois", [])
    recommended_pois = None
    if pois_raw:
        recommended_pois = [
            POIForExport(
                id=poi.get("id", ""),
                name=poi.get("name", ""),
                city=poi.get("city"),
                latitude=poi.get("latitude") or 0.0,
                longitude=poi.get("longitude") or 0.0,
                address=poi.get("address", ""),
                description=poi.get("description"),
                rating=poi.get("rating"),
                primary_category=poi.get("primary_category"),
                image_url=poi.get("image_url"),
                opening_hours=poi.get("opening_hours"),
            )
            for poi in pois_raw
        ]

    # 转换 suggested_plan
    plan_raw = full_data.get("suggested_plan", {})
    suggested_plan = None
    if plan_raw and plan_raw.get("days"):
        days = []
        for day_data in plan_raw.get("days", []):
            stops = [
                SuggestedStop(
                    poi_id=stop.get("poi_id", ""),
                    poi_name=stop.get("poi_name", ""),
                    arrival_time=stop.get("arrival_time", ""),
                    departure_time=stop.get("departure_time", ""),
                    duration_minutes=stop.get("duration_minutes", 0),
                    activity=stop.get("activity"),
                )
                for stop in day_data.get("stops", [])
            ]
            days.append(
                SuggestedDay(
                    date=day_data.get("date", ""),
                    day_number=day_data.get("day_number", 0),
                    theme=day_data.get("theme"),
                    stops=stops,
                )
            )
        suggested_plan = SuggestedPlan(
            destination=plan_raw.get("destination", ""),
            start_date=plan_raw.get("start_date"),
            end_date=plan_raw.get("end_date"),
            total_days=plan_raw.get("total_days", 0),
            days=days,
        )

    # 判断特征完整性
    feature_complete = False
    if user_features:
        # 核心字段：destination, travel_days, interests
        feature_complete = bool(
            user_features.get("destination")
            and user_features.get("travel_days")
            and user_features.get("interests")
        )

    return ChatResponse(
        session_id=session_id,
        message=f"[会话已恢复] {last_message}",
        user_features=user_features,
        feature_complete=feature_complete,
        plan_ready=full_data.get("plan_ready", False),
        recommended_pois=recommended_pois,
        suggested_plan=suggested_plan,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    对话接口

    处理流程：
    1. 加载/创建会话
    2. 添加用户消息（如果有）
    3. 调用 LangGraph 工作流
    4. 提取 AI 回复
    5. 保存会话历史

    Args:
        request: ChatRequest 包含 session_id 和 message

    Returns:
        ChatResponse 包含 AI 回复和会话信息

    Raises:
        HTTPException: 工作流执行失败时抛出 500 错误
    """
    try:
        # 1. 加载/创建会话
        session_id = request.session_id or generate_session_id()

        if request.session_id:
            # 加载完整会话状态（包括 messages 和 optional_asked）
            session_state = load_session_state(request.session_id)
            messages = session_state["messages"]
            optional_asked = session_state["optional_asked"]

            # 快速恢复模式：如果有 session_id 但没有新消息，直接返回保存的状态
            # 这样可以实现毫秒级会话恢复，无需调用 LLM
            if not request.message:
                return _build_recovery_response(session_id, session_state)
        else:
            messages = []  # 新会话，空消息 → 触发冷启动问候
            optional_asked = False

        # 2. 添加用户消息（如果有内容）
        if request.message:
            messages.append(HumanMessage(content=request.message))

        # 3. 调用 LangGraph 工作流（传入完整状态）
        state: dict[str, Any] = {
            "messages": messages,
            "optional_asked": optional_asked,
        }
        result = crag_graph.invoke(state)

        # 4. 提取 AI 回复
        result_messages = result.get("messages", [])
        ai_messages = [m for m in result_messages if isinstance(m, AIMessage)]

        if ai_messages:
            ai_reply = str(ai_messages[-1].content)
        else:
            ai_reply = "抱歉，我暂时无法回复。"

        # 5. 提取用户特征
        user_features = result.get("user_features")
        if user_features:
            # 转换 Pydantic/TypedDict 为普通 dict
            if hasattr(user_features, "model_dump"):
                user_features = user_features.model_dump()
            else:
                user_features = dict(user_features)

        feature_complete = result.get("feature_complete")

        # 6. 提取 Java 集成字段
        plan_ready = result.get("plan_ready", False)
        recommended_pois_raw = result.get("recommended_pois")
        suggested_plan_raw = result.get("suggested_plan")

        # 转换 POIResult/dict 为 POIForExport
        recommended_pois = None
        if recommended_pois_raw:
            recommended_pois = []
            for poi in recommended_pois_raw:
                # 处理 POIResult 对象
                if isinstance(poi, POIResult):
                    recommended_pois.append(
                        POIForExport(
                            id=poi.id,
                            name=poi.name,
                            city=poi.city,
                            latitude=poi.latitude or 0.0,
                            longitude=poi.longitude or 0.0,
                            address=poi.address,
                            description=poi.editorial_summary,
                            rating=poi.rating,
                            primary_category=poi.primary_category,
                            image_url=poi.image_url,
                            opening_hours=poi.opening_hours,
                        )
                    )
                # 处理 dict 对象（来自 GradingMiddleware 的 search_results）
                elif isinstance(poi, dict):
                    recommended_pois.append(
                        POIForExport(
                            id=poi.get("id", ""),
                            name=poi.get("name", ""),
                            city=poi.get("city"),
                            latitude=poi.get("latitude") or 0.0,
                            longitude=poi.get("longitude") or 0.0,
                            address=poi.get("address", ""),
                            description=poi.get("editorial_summary"),
                            rating=poi.get("rating"),
                            primary_category=poi.get("primary_category"),
                            image_url=poi.get("image_url"),
                            opening_hours=poi.get("opening_hours"),
                        )
                    )

        # 转换 suggested_plan dict 为 SuggestedPlan
        suggested_plan = None
        if suggested_plan_raw and isinstance(suggested_plan_raw, dict):
            days = []
            for day_data in suggested_plan_raw.get("days", []):
                stops = [
                    SuggestedStop(
                        poi_id=stop.get("poi_id", ""),
                        poi_name=stop.get("poi_name", ""),
                        arrival_time=stop.get("arrival_time", ""),
                        departure_time=stop.get("departure_time", ""),
                        duration_minutes=stop.get("duration_minutes", 0),
                        activity=stop.get("activity"),
                    )
                    for stop in day_data.get("stops", [])
                ]
                days.append(
                    SuggestedDay(
                        date=day_data.get("date", ""),
                        day_number=day_data.get("day_number", 0),
                        theme=day_data.get("theme"),
                        stops=stops,
                    )
                )
            suggested_plan = SuggestedPlan(
                destination=suggested_plan_raw.get("destination", ""),
                start_date=suggested_plan_raw.get("start_date"),
                end_date=suggested_plan_raw.get("end_date"),
                total_days=suggested_plan_raw.get("total_days", 0),
                days=days,
            )

        # 7. 提取 optional_asked 状态（用于多轮对话）
        result_optional_asked = result.get("optional_asked", optional_asked)

        # 8. 提取 search_results 用于持久化（调试追踪）
        search_results_raw = result.get("search_results", [])
        search_results_for_storage = None
        if search_results_raw:
            search_results_for_storage = []
            for sr in search_results_raw:
                if isinstance(sr, POIResult):
                    search_results_for_storage.append(sr.model_dump())
                elif isinstance(sr, dict):
                    search_results_for_storage.append(sr)

        # 9. 保存会话历史（包含完整 POI 和 Plan 数据）
        # 将 POIForExport 转换为 dict 以便 JSON 序列化
        pois_for_storage = None
        if recommended_pois:
            pois_for_storage = [poi.model_dump() for poi in recommended_pois]

        plan_for_storage = None
        if suggested_plan:
            plan_for_storage = suggested_plan.model_dump()

        save_session_history(
            session_id=session_id,
            messages=result_messages,
            user_features=user_features,
            search_results=search_results_for_storage,
            recommended_pois=pois_for_storage,
            suggested_plan=plan_for_storage,
            plan_ready=plan_ready,
            optional_asked=result_optional_asked,
        )

        return ChatResponse(
            session_id=session_id,
            message=ai_reply,
            user_features=user_features,
            feature_complete=feature_complete,
            plan_ready=plan_ready,
            recommended_pois=recommended_pois,
            suggested_plan=suggested_plan,
        )

    except Exception as e:
        logger.exception("Chat API error")
        raise HTTPException(
            status_code=500,
            detail=f"对话处理失败: {e!s}",
        ) from e


def _invoke_chat_workflow(request: ChatRequest) -> dict[str, Any]:
    """
    执行 CRAG 工作流核心逻辑（同步）

    提取自 chat() 函数，供 SSE 端点复用。

    Args:
        request: ChatRequest

    Returns:
        包含完整响应数据的字典
    """
    # 1. 加载/创建会话
    session_id = request.session_id or generate_session_id()

    if request.session_id:
        session_state = load_session_state(request.session_id)
        messages = session_state["messages"]
        optional_asked = session_state["optional_asked"]
    else:
        messages = []
        optional_asked = False

    # 2. 添加用户消息
    if request.message:
        messages.append(HumanMessage(content=request.message))

    # 3. 调用 LangGraph 工作流
    state: dict[str, Any] = {
        "messages": messages,
        "optional_asked": optional_asked,
    }
    result = crag_graph.invoke(state)

    # 4. 提取 AI 回复
    result_messages = result.get("messages", [])
    ai_messages = [m for m in result_messages if isinstance(m, AIMessage)]
    ai_reply = str(ai_messages[-1].content) if ai_messages else "抱歉，我暂时无法回复。"

    # 5. 提取用户特征
    user_features = result.get("user_features")
    if user_features:
        if hasattr(user_features, "model_dump"):
            user_features = user_features.model_dump()
        else:
            user_features = dict(user_features)

    feature_complete = result.get("feature_complete")
    plan_ready = result.get("plan_ready", False)
    recommended_pois_raw = result.get("recommended_pois")
    suggested_plan_raw = result.get("suggested_plan")

    # 6. 转换 POI
    recommended_pois = None
    if recommended_pois_raw:
        recommended_pois = []
        for poi in recommended_pois_raw:
            if isinstance(poi, POIResult):
                recommended_pois.append(
                    POIForExport(
                        id=poi.id,
                        name=poi.name,
                        city=poi.city,
                        latitude=poi.latitude or 0.0,
                        longitude=poi.longitude or 0.0,
                        address=poi.address,
                        description=poi.editorial_summary,
                        rating=poi.rating,
                        primary_category=poi.primary_category,
                        image_url=poi.image_url,
                        opening_hours=poi.opening_hours,
                    )
                )
            elif isinstance(poi, dict):
                recommended_pois.append(
                    POIForExport(
                        id=poi.get("id", ""),
                        name=poi.get("name", ""),
                        city=poi.get("city"),
                        latitude=poi.get("latitude") or 0.0,
                        longitude=poi.get("longitude") or 0.0,
                        address=poi.get("address", ""),
                        description=poi.get("editorial_summary"),
                        rating=poi.get("rating"),
                        primary_category=poi.get("primary_category"),
                        image_url=poi.get("image_url"),
                        opening_hours=poi.get("opening_hours"),
                    )
                )

    # 7. 转换 Plan
    suggested_plan = None
    if suggested_plan_raw and isinstance(suggested_plan_raw, dict):
        days = []
        for day_data in suggested_plan_raw.get("days", []):
            stops = [
                SuggestedStop(
                    poi_id=stop.get("poi_id", ""),
                    poi_name=stop.get("poi_name", ""),
                    arrival_time=stop.get("arrival_time", ""),
                    departure_time=stop.get("departure_time", ""),
                    duration_minutes=stop.get("duration_minutes", 0),
                    activity=stop.get("activity"),
                )
                for stop in day_data.get("stops", [])
            ]
            days.append(
                SuggestedDay(
                    date=day_data.get("date", ""),
                    day_number=day_data.get("day_number", 0),
                    theme=day_data.get("theme"),
                    stops=stops,
                )
            )
        suggested_plan = SuggestedPlan(
            destination=suggested_plan_raw.get("destination", ""),
            start_date=suggested_plan_raw.get("start_date"),
            end_date=suggested_plan_raw.get("end_date"),
            total_days=suggested_plan_raw.get("total_days", 0),
            days=days,
        )

    # 8. 保存会话
    result_optional_asked = result.get("optional_asked", optional_asked)
    search_results_raw = result.get("search_results", [])
    search_results_for_storage = None
    if search_results_raw:
        search_results_for_storage = []
        for sr in search_results_raw:
            if isinstance(sr, POIResult):
                search_results_for_storage.append(sr.model_dump())
            elif isinstance(sr, dict):
                search_results_for_storage.append(sr)

    pois_for_storage = None
    if recommended_pois:
        pois_for_storage = [poi.model_dump() for poi in recommended_pois]

    plan_for_storage = None
    if suggested_plan:
        plan_for_storage = suggested_plan.model_dump()

    save_session_history(
        session_id=session_id,
        messages=result_messages,
        user_features=user_features,
        search_results=search_results_for_storage,
        recommended_pois=pois_for_storage,
        suggested_plan=plan_for_storage,
        plan_ready=plan_ready,
        optional_asked=result_optional_asked,
    )

    # 9. 返回响应数据
    return {
        "session_id": session_id,
        "message": ai_reply,
        "user_features": user_features,
        "feature_complete": feature_complete,
        "plan_ready": plan_ready,
        "recommended_pois": (
            [poi.model_dump() for poi in recommended_pois] if recommended_pois else None
        ),
        "suggested_plan": suggested_plan.model_dump() if suggested_plan else None,
    }


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> EventSourceResponse:
    """
    SSE 流式对话接口

    与 /chat 功能相同，但以 Server-Sent Events 格式返回，
    并在工作流执行过程中推送进度事件。

    进度事件格式:
        {"stage": "collector", "message": "正在理解您的需求...", "percent": 10}
        {"stage": "search", "message": "正在搜索景点...", "percent": 40}
        {"stage": "complete", "data": {...}}  # 最终结果

    Args:
        request: ChatRequest

    Returns:
        EventSourceResponse SSE 流
    """
    # 快速恢复模式：直接返回，不需要 SSE
    if request.session_id and not request.message:
        session_state = load_session_state(request.session_id)
        response = _build_recovery_response(request.session_id, session_state)

        async def single_event():
            yield {
                "event": "complete",
                "data": json.dumps(response.model_dump(), ensure_ascii=False),
            }

        return EventSourceResponse(single_event())

    # SSE 进度推送
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    workflow_done = asyncio.Event()

    # 在主协程中捕获事件循环，供线程池回调使用
    main_loop = asyncio.get_running_loop()

    def progress_callback(event: dict[str, Any]) -> None:
        """同步回调，将事件放入队列（从线程池调用）"""
        try:
            # 使用预先捕获的事件循环
            main_loop.call_soon_threadsafe(queue.put_nowait, event)
        except Exception as e:
            logger.warning(f"Failed to queue progress event: {e}")

    async def run_workflow() -> None:
        """在 threadpool 中运行同步工作流"""
        token = set_progress_callback(progress_callback)
        try:
            result = await asyncio.to_thread(_invoke_chat_workflow, request)
            await queue.put({"stage": "complete", "data": result})
        except Exception as e:
            logger.exception("Workflow error in SSE stream")
            await queue.put({"stage": "error", "message": str(e)})
        finally:
            reset_progress_callback(token)
            workflow_done.set()

    async def event_generator():
        """生成 SSE 事件"""
        # 启动工作流
        asyncio.create_task(run_workflow())

        while True:
            try:
                # 等待事件（带超时以便检查完成状态）
                event = await asyncio.wait_for(queue.get(), timeout=1.0)

                if event.get("stage") == "complete":
                    yield {
                        "event": "complete",
                        "data": json.dumps(event.get("data", {}), ensure_ascii=False),
                    }
                    break
                elif event.get("stage") == "error":
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": event.get("message")}, ensure_ascii=False),
                    }
                    break
                else:
                    yield {
                        "event": "progress",
                        "data": json.dumps(event, ensure_ascii=False),
                    }
            except TimeoutError:
                # 超时但工作流未完成，继续等待
                if workflow_done.is_set():
                    break
                continue

    return EventSourceResponse(event_generator())
