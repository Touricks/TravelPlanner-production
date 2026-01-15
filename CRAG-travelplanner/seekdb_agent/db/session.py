"""
Session Management
==================
用户会话管理 - 基于 OceanBase user_sessions 表

功能：
- 会话创建和 ID 生成
- 消息历史加载和保存
- 会话过期管理
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any

import httpx
import pymysql  # type: ignore[import-untyped]
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

load_dotenv()

logger = logging.getLogger(__name__)

# 会话过期时间（小时）
SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))

# Java API 配置
JAVA_API_URL = os.getenv("JAVA_API_URL", "http://localhost:8080")
JAVA_SYNC_TIMEOUT = float(os.getenv("JAVA_SYNC_TIMEOUT", "5.0"))


def _get_db_connection() -> pymysql.Connection:
    """获取数据库连接"""
    return pymysql.connect(
        host=os.getenv("DATABASE_HOST", "127.0.0.1"),
        port=int(os.getenv("DATABASE_PORT", "2881")),
        user=os.getenv("DATABASE_USER", "root@test"),
        password=os.getenv("DATABASE_PASSWORD", ""),
        database=os.getenv("DATABASE_NAME", "crag_travelplanner"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def generate_session_id() -> str:
    """
    生成唯一会话 ID

    Returns:
        UUID 格式的会话 ID
    """
    return str(uuid.uuid4())


def _serialize_message(msg: BaseMessage) -> dict[str, Any]:
    """
    序列化单个消息为 JSON 可存储格式

    Args:
        msg: LangChain 消息对象

    Returns:
        包含 type 和 content 的字典
    """
    msg_type = "human"
    if isinstance(msg, AIMessage):
        msg_type = "ai"
    elif isinstance(msg, SystemMessage):
        msg_type = "system"
    elif isinstance(msg, HumanMessage):
        msg_type = "human"

    return {"type": msg_type, "content": msg.content}


def _deserialize_message(data: dict[str, Any]) -> BaseMessage:
    """
    反序列化消息

    Args:
        data: 包含 type 和 content 的字典

    Returns:
        LangChain 消息对象
    """
    msg_type = data.get("type", "human")
    content = data.get("content", "")

    if msg_type == "ai":
        return AIMessage(content=content)
    elif msg_type == "system":
        return SystemMessage(content=content)
    else:
        return HumanMessage(content=content)


def load_session_history(session_id: str) -> list[BaseMessage]:
    """
    从数据库加载会话历史

    Args:
        session_id: 会话 ID

    Returns:
        消息列表，如果会话不存在或已过期返回空列表
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT state FROM user_sessions
                WHERE session_id = %s
                AND (expires_at IS NULL OR expires_at > NOW())
            """
            cursor.execute(sql, (session_id,))
            result = cursor.fetchone()

            if not result or not result.get("state"):
                return []

            # 解析 state JSON
            state_data = result["state"]
            if isinstance(state_data, str):
                state_data = json.loads(state_data)

            # 提取 messages
            messages_data = state_data.get("messages", [])
            return [_deserialize_message(m) for m in messages_data]

    finally:
        conn.close()


def load_session_state(session_id: str) -> dict[str, Any]:
    """
    从数据库加载完整会话状态（用于工作流）

    Args:
        session_id: 会话 ID

    Returns:
        包含 messages, optional_asked, 和 user_features 的字典
        {
            "messages": list[BaseMessage],
            "optional_asked": bool,
            "user_features": dict | None
        }
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT state FROM user_sessions
                WHERE session_id = %s
                AND (expires_at IS NULL OR expires_at > NOW())
            """
            cursor.execute(sql, (session_id,))
            result = cursor.fetchone()

            if not result or not result.get("state"):
                return {"messages": [], "optional_asked": False, "user_features": None}

            # 解析 state JSON
            state_data = result["state"]
            if isinstance(state_data, str):
                state_data = json.loads(state_data)

            # 提取 messages
            messages_data = state_data.get("messages", [])
            messages = [_deserialize_message(m) for m in messages_data]

            # 提取 user_features（用于多轮对话特征持久化）
            user_features = state_data.get("user_features")

            return {
                "messages": messages,
                "optional_asked": state_data.get("optional_asked", False),
                "user_features": user_features if user_features else None,
            }

    finally:
        conn.close()


def save_session_history(
    session_id: str,
    messages: list[BaseMessage],
    user_features: dict[str, Any] | None = None,
    search_results: list[dict[str, Any]] | None = None,
    recommended_pois: list[dict[str, Any]] | None = None,
    suggested_plan: dict[str, Any] | None = None,
    plan_ready: bool = False,
    optional_asked: bool = False,
) -> None:
    """
    保存会话历史到数据库

    Args:
        session_id: 会话 ID
        messages: 消息列表
        user_features: 用户特征（可选）
        search_results: 搜索结果（可选）- 用于调试和追踪
        recommended_pois: 推荐的 POI 列表（可选）
        suggested_plan: 建议的行程计划（可选）
        plan_ready: 计划是否可保存
        optional_asked: 是否已询问过可选字段
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 序列化消息
            messages_data = [_serialize_message(m) for m in messages]

            # 构建 state JSON - 包含完整数据
            state_data = json.dumps(
                {
                    "messages": messages_data,
                    "user_features": user_features or {},
                    "search_results": search_results or [],
                    "recommended_pois": recommended_pois or [],
                    "suggested_plan": suggested_plan or {},
                    "plan_ready": plan_ready,
                    "optional_asked": optional_asked,
                },
                ensure_ascii=False,
            )

            # 用户特征 JSON
            features_data = json.dumps(user_features, ensure_ascii=False) if user_features else None

            # 计算过期时间
            expires_at = datetime.now() + timedelta(hours=SESSION_EXPIRE_HOURS)

            # 使用 INSERT ... ON DUPLICATE KEY UPDATE
            sql = """
                INSERT INTO user_sessions
                    (session_id, state, user_features, total_queries, expires_at, updated_at)
                VALUES
                    (%s, %s, %s, 1, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    state = VALUES(state),
                    user_features = VALUES(user_features),
                    total_queries = total_queries + 1,
                    expires_at = VALUES(expires_at),
                    updated_at = NOW()
            """
            cursor.execute(sql, (session_id, state_data, features_data, expires_at))
            conn.commit()

    finally:
        conn.close()


def get_session_info(session_id: str) -> dict[str, Any] | None:
    """
    获取会话详细信息

    Args:
        session_id: 会话 ID

    Returns:
        会话信息字典，不存在返回 None
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT session_id, user_features, total_queries,
                       retry_count, fallback_triggered, created_at, updated_at, expires_at
                FROM user_sessions
                WHERE session_id = %s
            """
            cursor.execute(sql, (session_id,))
            result = cursor.fetchone()

            if not result:
                return None

            # 解析 user_features JSON
            if result.get("user_features"):
                if isinstance(result["user_features"], str):
                    result["user_features"] = json.loads(result["user_features"])

            return dict(result)

    finally:
        conn.close()


def get_full_session_data(session_id: str) -> dict[str, Any] | None:
    """
    获取完整的会话数据（包括 POI 和 Plan）

    Args:
        session_id: 会话 ID

    Returns:
        包含完整状态的字典，不存在返回 None
        {
            "session_id": str,
            "user_features": dict,
            "search_results": list,
            "recommended_pois": list,
            "suggested_plan": dict,
            "plan_ready": bool
        }
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT session_id, state
                FROM user_sessions
                WHERE session_id = %s
                AND (expires_at IS NULL OR expires_at > NOW())
            """
            cursor.execute(sql, (session_id,))
            result = cursor.fetchone()

            if not result or not result.get("state"):
                return None

            # 解析 state JSON
            state_data = result["state"]
            if isinstance(state_data, str):
                state_data = json.loads(state_data)

            return {
                "session_id": session_id,
                "user_features": state_data.get("user_features", {}),
                "search_results": state_data.get("search_results", []),
                "recommended_pois": state_data.get("recommended_pois", []),
                "suggested_plan": state_data.get("suggested_plan", {}),
                "plan_ready": state_data.get("plan_ready", False),
            }

    finally:
        conn.close()


def delete_session(session_id: str) -> bool:
    """
    删除会话

    Args:
        session_id: 会话 ID

    Returns:
        是否删除成功
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM user_sessions WHERE session_id = %s"
            cursor.execute(sql, (session_id,))
            conn.commit()
            return bool(cursor.rowcount > 0)

    finally:
        conn.close()


def cleanup_expired_sessions() -> int:
    """
    清理过期会话

    Returns:
        清理的会话数量
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM user_sessions WHERE expires_at < NOW()"
            cursor.execute(sql)
            conn.commit()
            return int(cursor.rowcount or 0)

    finally:
        conn.close()


def fetch_pinned_pois_from_java(session_id: str) -> list[dict[str, Any]]:
    """
    从 Java 后端获取用户 pinned 的 POI 列表

    当用户继续对话时，调用此函数同步 Java 端的 pinned POI 状态。
    用户可能在 Java 前端添加/删除了感兴趣的 POI，这些变更需要同步到 CRAG。

    Args:
        session_id: CRAG session ID（对应 Java 的 itinerary.cragSessionId）

    Returns:
        POI 字典列表（CRAG 格式），失败时返回空列表

    Note:
        - 使用短超时（5秒）避免阻塞对话流程
        - 任何错误都返回空列表（优雅降级）
        - POI 格式已转换为 CRAG 兼容结构
    """
    try:
        with httpx.Client(timeout=JAVA_SYNC_TIMEOUT) as client:
            url = f"{JAVA_API_URL}/api/itineraries/by-session/{session_id}/pinned-pois"
            logger.debug(f"[JavaSync] Fetching pinned POIs from: {url}")

            response = client.get(url)
            response.raise_for_status()

            data = response.json()
            java_pois = data.get("pois", [])

            if not java_pois:
                logger.debug(f"[JavaSync] No pinned POIs found for session {session_id}")
                return []

            # Convert Java format to CRAG format
            crag_pois = []
            for poi in java_pois:
                crag_pois.append(
                    {
                        "id": poi.get("id", ""),
                        "name": poi.get("name", ""),
                        "city": poi.get("city"),
                        "latitude": poi.get("latitude") or 0.0,
                        "longitude": poi.get("longitude") or 0.0,
                        "address": poi.get("address", ""),
                        "description": poi.get("description"),
                        "editorial_summary": poi.get("description"),  # CRAG alias
                        "rating": poi.get("rating"),
                        "primary_category": poi.get("primaryCategory"),
                        "image_url": poi.get("imageUrl"),
                        "opening_hours": poi.get("openingHours"),
                    }
                )

            logger.info(
                f"[JavaSync] Fetched {len(crag_pois)} pinned POIs from Java for session {session_id}"
            )
            return crag_pois

    except httpx.HTTPStatusError as e:
        logger.warning(
            f"[JavaSync] Java API returned error for session {session_id}: {e.response.status_code}"
        )
        return []
    except httpx.RequestError as e:
        logger.warning(f"[JavaSync] Failed to connect to Java API: {e}")
        return []
    except Exception as e:
        logger.error(f"[JavaSync] Unexpected error fetching pinned POIs: {e}")
        return []
