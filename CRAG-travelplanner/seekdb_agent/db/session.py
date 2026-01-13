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
import os
import uuid
from datetime import datetime, timedelta
from typing import Any

import pymysql  # type: ignore[import-untyped]
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

load_dotenv()

# 会话过期时间（小时）
SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))


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
        包含 messages 和 optional_asked 的字典
        {
            "messages": list[BaseMessage],
            "optional_asked": bool
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
                return {"messages": [], "optional_asked": False}

            # 解析 state JSON
            state_data = result["state"]
            if isinstance(state_data, str):
                state_data = json.loads(state_data)

            # 提取 messages
            messages_data = state_data.get("messages", [])
            messages = [_deserialize_message(m) for m in messages_data]

            return {
                "messages": messages,
                "optional_asked": state_data.get("optional_asked", False),
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
