"""
Generator Node
==============
根据搜索结果生成最终的旅游建议响应

职责：
- 将 POI 搜索结果转化为自然语言推荐
- 根据用户特征组织行程
- 生成结构化的旅游建议（支持 Java 后端集成）

更新记录：
- 2026-01-09: 添加结构化输出支持（Java 后端集成）
"""

import logging
import sys
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from seekdb_agent.llm import create_fallback_llm, create_llm
from seekdb_agent.prompts.generator import GENERATOR_PROMPT
from seekdb_agent.state import CRAGState, POIResult, UserFeatures
from seekdb_agent.utils.progress import emit_progress

# 配置日志输出到 stderr（确保立即显示）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("generator")

# Fallback Prompt（当搜索结果为空时使用）
FALLBACK_GENERATOR_PROMPT = """你是专业旅游顾问。数据库中没有找到相关 POI，请基于你的知识和联网搜索能力提供旅游建议。

**用户需求：**
- 目的地: {destination}
- 旅行天数: {travel_days}天
- 兴趣偏好: {interests}
- 餐饮预算: {budget_meal}
- 交通方式: {transportation}
- 每天景点数: {pois_per_day}个
- 必去景点: {must_visit}
- 饮食偏好: {dietary_options}

**要求：**
1. 提供详细的每日行程安排
2. 推荐真实存在的景点、餐厅
3. 考虑用户的预算和交通偏好
4. 包含实用的旅行建议

请为用户生成完整的旅行计划。"""

# ===== Generator 结构化输出模型 =====


class StopOutput(BaseModel):
    """单个停靠点输出"""

    poi_id: str = Field(description="对应 search_results 中的 POI ID")
    arrival_time: str = Field(description="建议到达时间 HH:MM 格式")
    departure_time: str = Field(description="建议离开时间 HH:MM 格式")
    activity: str | None = Field(default=None, description="活动建议")


class DayItinerary(BaseModel):
    """单天行程输出"""

    day_number: int = Field(description="第几天 (1-based)")
    theme: str = Field(description="当天主题")
    stops: list[StopOutput] = Field(default_factory=list, description="停靠点列表")


class GeneratorOutput(BaseModel):
    """Generator 结构化输出"""

    message: str = Field(description="给用户的自然语言推荐")
    daily_itinerary: list[DayItinerary] = Field(default_factory=list, description="按天组织的行程")


# ===== 辅助函数 =====


def _get_llm() -> BaseChatModel:
    """获取 LLM 实例"""
    return create_llm(temperature=0.7)


def _format_search_results_for_structured(results: Sequence[POIResult | dict[str, Any]]) -> str:
    """
    格式化搜索结果供结构化输出使用（包含 POI ID）

    Args:
        results: POI 搜索结果列表（支持 POIResult 或 dict）

    Returns:
        格式化的 POI 文本（包含 ID）
    """
    if not results:
        return "无搜索结果"

    lines = []
    for i, poi in enumerate(results, 1):
        # 统一处理 POIResult 和 dict
        if isinstance(poi, dict):
            poi_id = poi.get("id", f"poi_{i}")
            name = poi.get("name", "Unknown")
            city = poi.get("city")
            rating = poi.get("rating")
            primary_category = poi.get("primary_category")
            price_level = poi.get("price_level")
            editorial_summary = poi.get("editorial_summary")
        else:
            poi_id = poi.id
            name = poi.name
            city = poi.city
            rating = poi.rating
            primary_category = poi.primary_category
            price_level = poi.price_level
            editorial_summary = poi.editorial_summary

        line = f"{i}. [ID: {poi_id}] {name}"
        if city:
            line += f" ({city})"
        if rating:
            line += f" - 评分: {rating}"
        if primary_category:
            line += f" - 类型: {primary_category}"
        if price_level:
            price_map = {1: "低", 2: "中", 3: "高", 4: "豪华"}
            line += f" - 价格: {price_map.get(price_level, '未知')}"
        if editorial_summary:
            line += f"\n   描述: {editorial_summary[:100]}..."
        lines.append(line)

    return "\n".join(lines)


def _format_search_results(results: list[POIResult]) -> str:
    """
    格式化搜索结果供 Generator 使用（兼容旧版本）

    Args:
        results: POI 搜索结果列表

    Returns:
        格式化的 POI 文本
    """
    if not results:
        return "无搜索结果"

    lines = []
    for i, poi in enumerate(results, 1):
        line = f"{i}. {poi.name}"
        if poi.city:
            line += f" ({poi.city})"
        if poi.rating:
            line += f" - 评分: {poi.rating}"
        if poi.primary_category:
            line += f" - 类型: {poi.primary_category}"
        if poi.price_level:
            price_map = {1: "低", 2: "中", 3: "高", 4: "豪华"}
            line += f" - 价格: {price_map.get(poi.price_level, '未知')}"
        if poi.editorial_summary:
            line += f"\n   描述: {poi.editorial_summary[:100]}..."
        lines.append(line)

    return "\n".join(lines)


def _format_user_features(features: dict[str, Any] | UserFeatures | None) -> str:
    """
    格式化用户特征供 Generator 使用

    Args:
        features: 用户特征（可以是 dict 或 UserFeatures）

    Returns:
        格式化的用户特征文本
    """
    if features is None:
        return "未提供用户特征"

    # 如果是 UserFeatures，转为 dict
    if isinstance(features, UserFeatures):
        features = features.model_dump()

    lines = []

    if features.get("destination"):
        lines.append(f"目的地: {features['destination']}")
    if features.get("travel_days"):
        lines.append(f"旅行天数: {features['travel_days']}天")
    if features.get("interests"):
        lines.append(f"兴趣偏好: {', '.join(features['interests'])}")
    if features.get("budget_meal"):
        lines.append(f"餐饮预算: {features['budget_meal']}")
    if features.get("transportation"):
        lines.append(f"交通方式: {features['transportation']}")
    if features.get("pois_per_day"):
        lines.append(f"每天景点数: {features['pois_per_day']}个")
    if features.get("must_visit"):
        lines.append(f"必去景点: {', '.join(features['must_visit'])}")
    if features.get("dietary_options"):
        lines.append(f"饮食偏好: {', '.join(features['dietary_options'])}")
    # 新增字段
    if features.get("start_date"):
        lines.append(f"开始日期: {features['start_date']}")
    if features.get("end_date"):
        lines.append(f"结束日期: {features['end_date']}")
    if features.get("number_of_travelers"):
        lines.append(f"出行人数: {features['number_of_travelers']}人")

    return "\n".join(lines) if lines else "未提供用户特征"


def _calculate_duration(arrival: str, departure: str) -> int:
    """计算停留时长（分钟）"""
    try:
        arr_time = datetime.strptime(arrival, "%H:%M")
        dep_time = datetime.strptime(departure, "%H:%M")
        delta = dep_time - arr_time
        return max(int(delta.total_seconds() / 60), 0)
    except Exception:
        return 120  # 默认 2 小时


def _get_poi_name_by_id(poi_id: str, search_results: Sequence[POIResult | dict[str, Any]]) -> str:
    """根据 POI ID 获取名称（支持 POIResult 或 dict）"""
    for poi in search_results:
        if isinstance(poi, dict):
            if poi.get("id") == poi_id:
                name = poi.get("name", "Unknown POI")
                return str(name) if name else "Unknown POI"
        else:
            if poi.id == poi_id:
                return poi.name
    return "Unknown POI"


def _convert_to_suggested_plan(
    daily_itinerary: list[DayItinerary],
    user_features: dict[str, Any] | UserFeatures | None,
    search_results: Sequence[POIResult | dict[str, Any]],
) -> dict[str, Any]:
    """
    将 Generator 输出转换为 SuggestedPlan 格式

    Args:
        daily_itinerary: Generator 输出的每日行程
        user_features: 用户特征
        search_results: POI 搜索结果

    Returns:
        SuggestedPlan 格式的字典
    """
    if user_features is None:
        user_features = {}
    elif isinstance(user_features, UserFeatures):
        user_features = user_features.model_dump()

    destination = user_features.get("destination", "Unknown")
    travel_days = user_features.get("travel_days", len(daily_itinerary))
    start_date = user_features.get("start_date")
    end_date = user_features.get("end_date")

    # 如果没有具体日期，生成占位日期
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    if not end_date and travel_days:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = start_dt + timedelta(days=travel_days - 1)
            end_date = end_dt.strftime("%Y-%m-%d")
        except Exception:
            end_date = start_date

    # 构建每日行程
    days = []
    for day in daily_itinerary:
        try:
            day_dt = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=day.day_number - 1)
            day_date = day_dt.strftime("%Y-%m-%d")
        except Exception:
            day_date = start_date

        stops = []
        for stop in day.stops:
            stops.append(
                {
                    "poi_id": stop.poi_id,
                    "poi_name": _get_poi_name_by_id(stop.poi_id, search_results),
                    "arrival_time": stop.arrival_time,
                    "departure_time": stop.departure_time,
                    "duration_minutes": _calculate_duration(stop.arrival_time, stop.departure_time),
                    "activity": stop.activity,
                }
            )

        days.append(
            {
                "date": day_date,
                "day_number": day.day_number,
                "theme": day.theme,
                "stops": stops,
            }
        )

    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "total_days": travel_days or len(days),
        "days": days,
    }


def _generate_fallback_response(user_features: dict[str, Any]) -> dict[str, Any]:
    """
    当搜索结果为空时，使用 Fallback LLM 生成响应（支持结构化输出）

    Args:
        user_features: 用户特征字典

    Returns:
        包含 fallback 响应的状态更新字典
    """
    import logging

    logger = logging.getLogger(__name__)

    destination = user_features.get("destination") or "未知"
    travel_days = user_features.get("travel_days") or 3
    interests = ", ".join(user_features.get("interests", [])) or "未指定"
    budget_meal = user_features.get("budget_meal") or "未指定"
    transportation = user_features.get("transportation") or "未指定"
    pois_per_day = user_features.get("pois_per_day") or 4
    must_visit = ", ".join(user_features.get("must_visit", [])) or "无"
    dietary_options = ", ".join(user_features.get("dietary_options", [])) or "无"

    # 构建 Prompt
    prompt = FALLBACK_GENERATOR_PROMPT.format(
        destination=destination,
        travel_days=travel_days,
        interests=interests,
        budget_meal=budget_meal,
        transportation=transportation,
        pois_per_day=pois_per_day,
        must_visit=must_visit,
        dietary_options=dietary_options,
    )

    logger.info(f"[Fallback] 触发 Gemini 生成，目的地: {destination}")

    try:
        # 使用 Fallback LLM（优先 Gemini，支持联网搜索）
        fallback_llm = create_fallback_llm(temperature=0.7)

        # 尝试结构化输出
        try:
            structured_llm = fallback_llm.with_structured_output(GeneratorOutput)
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content="请为我规划旅行行程，并生成结构化的行程安排。"),
            ]
            raw_output = structured_llm.invoke(messages)

            if isinstance(raw_output, GeneratorOutput):
                logger.info(f"[Fallback] 结构化输出成功，天数: {len(raw_output.daily_itinerary)}")
                response_content = raw_output.message

                # 从结构化输出生成 POI 和 Plan
                fallback_pois = _extract_pois_from_itinerary(
                    raw_output.daily_itinerary, destination
                )
                suggested_plan = _convert_fallback_to_plan(
                    raw_output.daily_itinerary, user_features, fallback_pois
                )

                return {
                    "final_response": response_content,
                    "messages": [AIMessage(content=response_content)],
                    "recommended_pois": fallback_pois,
                    "suggested_plan": suggested_plan,
                    "plan_ready": bool(fallback_pois),
                    "fallback_triggered": True,
                }
        except Exception as struct_err:
            logger.warning(f"[Fallback] 结构化输出失败，降级为纯文本: {struct_err}")

        # 降级：纯文本响应
        response = fallback_llm.invoke(
            [
                SystemMessage(content=prompt),
                HumanMessage(content="请为我规划旅行行程"),
            ]
        )
        response_content = str(response.content) if hasattr(response, "content") else str(response)
        logger.info(f"[Fallback] 纯文本输出，长度: {len(response_content)}")

    except Exception as e:
        logger.error(f"[Fallback] 生成失败: {e}")
        response_content = f"抱歉，无法生成旅行建议。请稍后重试。错误信息：{e!s}"

    return {
        "final_response": response_content,
        "messages": [AIMessage(content=response_content)],
        "recommended_pois": [],
        "suggested_plan": None,
        "plan_ready": False,
        "fallback_triggered": True,
    }


def _extract_pois_from_itinerary(
    daily_itinerary: list[DayItinerary], destination: str
) -> list[dict[str, Any]]:
    """
    从 Fallback 生成的行程中提取 POI 信息

    Args:
        daily_itinerary: 每日行程列表
        destination: 目的地

    Returns:
        POI 字典列表（模拟 search_results 格式）
    """
    pois = []
    seen_ids = set()

    for day in daily_itinerary:
        for stop in day.stops:
            poi_id = stop.poi_id
            # 清理 ID（移除可能的前缀）
            if poi_id.startswith("ID: "):
                poi_id = poi_id[4:]

            if poi_id in seen_ids:
                continue
            seen_ids.add(poi_id)

            pois.append(
                {
                    "id": poi_id,
                    "name": poi_id.replace("_", " ").title(),  # 从 ID 推断名称
                    "city": destination,
                    "state": None,
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "rating": None,
                    "reviews_count": None,
                    "price_level": None,
                    "primary_category": "attraction",
                    "editorial_summary": stop.activity or "",
                    "address": f"{destination}",
                    "image_url": None,
                    "opening_hours": None,
                    "score": 0.8,  # Fallback 生成的 POI 给固定分数
                }
            )

    return pois


def _convert_fallback_to_plan(
    daily_itinerary: list[DayItinerary],
    user_features: dict[str, Any],
    fallback_pois: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    将 Fallback 生成的行程转换为 SuggestedPlan 格式

    Args:
        daily_itinerary: 每日行程
        user_features: 用户特征
        fallback_pois: 提取的 POI 列表

    Returns:
        SuggestedPlan 格式的字典
    """
    from datetime import datetime, timedelta

    destination = user_features.get("destination", "Unknown")
    travel_days = user_features.get("travel_days", len(daily_itinerary))
    start_date = user_features.get("start_date") or datetime.now().strftime("%Y-%m-%d")

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=travel_days - 1)
        end_date = end_dt.strftime("%Y-%m-%d")
    except Exception:
        end_date = start_date

    # 构建 POI 名称映射
    poi_name_map = {poi["id"]: poi["name"] for poi in fallback_pois}

    days = []
    for day in daily_itinerary:
        try:
            day_dt = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=day.day_number - 1)
            day_date = day_dt.strftime("%Y-%m-%d")
        except Exception:
            day_date = start_date

        stops = []
        for stop in day.stops:
            poi_id = stop.poi_id
            if poi_id.startswith("ID: "):
                poi_id = poi_id[4:]

            stops.append(
                {
                    "poi_id": poi_id,
                    "poi_name": poi_name_map.get(poi_id, poi_id.replace("_", " ").title()),
                    "arrival_time": stop.arrival_time,
                    "departure_time": stop.departure_time,
                    "duration_minutes": _calculate_duration(stop.arrival_time, stop.departure_time),
                    "activity": stop.activity,
                }
            )

        days.append(
            {
                "date": day_date,
                "day_number": day.day_number,
                "theme": day.theme,
                "stops": stops,
            }
        )

    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "total_days": travel_days,
        "days": days,
    }


# ===== 主节点函数 =====


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def generator_node(state: CRAGState) -> dict[str, Any]:
    """
    生成最终响应节点（支持结构化输出）

    如果 state 中已有 final_response（由 Fallback 生成），则直接返回。
    否则根据 search_results 和 user_features 生成推荐。

    Args:
        state: 当前工作流状态

    Returns:
        包含以下字段的更新字典：
        - final_response: 自然语言响应
        - messages: AIMessage 列表
        - recommended_pois: 推荐的 POI 列表（Java 集成）
        - suggested_plan: 结构化行程（Java 集成）
        - plan_ready: 是否可保存（Java 集成）
    """
    # 发射进度
    emit_progress("generator", "正在生成旅行计划...", 80)

    # ENTRY LOG
    import sys

    print("[GENERATOR_NODE] === ENTRY ===", file=sys.stderr, flush=True)
    print(f"[GENERATOR_NODE] state keys: {list(state.keys())}", file=sys.stderr, flush=True)

    # 如果已有响应（由 Fallback 生成），仍需生成 suggested_plan
    if state.get("final_response"):
        response = state["final_response"]
        search_results = state.get("search_results", [])

        # 获取或生成 suggested_plan
        suggested_plan = state.get("suggested_plan")
        if not suggested_plan and search_results:
            # 转换 user_features 为 dict
            uf = state.get("user_features")
            uf_dict: dict[str, Any]
            if isinstance(uf, UserFeatures):
                uf_dict = uf.model_dump()
            elif uf:
                uf_dict = dict(uf)  # type: ignore[arg-type]
            else:
                uf_dict = {}

            # 尝试使用 LLM 生成结构化行程
            try:
                llm = _get_llm()
                formatted_results = _format_search_results_for_structured(search_results)
                formatted_features = _format_user_features(uf_dict)
                prompt = GENERATOR_PROMPT.format(
                    user_features=formatted_features,
                    search_results=formatted_results,
                )
                structured_llm = llm.with_structured_output(GeneratorOutput)
                messages = [
                    SystemMessage(content=prompt),
                    HumanMessage(content="请根据以上信息生成结构化的行程安排。"),
                ]
                raw_output = structured_llm.invoke(messages)
                if isinstance(raw_output, GeneratorOutput):
                    suggested_plan = _convert_to_suggested_plan(
                        raw_output.daily_itinerary, uf_dict, search_results
                    )
                    logger.info(
                        f"[Fallback Path] Generated suggested_plan with {len(raw_output.daily_itinerary)} days"
                    )
            except Exception as e:
                logger.warning(f"[Fallback Path] Failed to generate suggested_plan: {e}")
                suggested_plan = None

        return {
            "messages": [AIMessage(content=response)],
            "recommended_pois": search_results,
            "suggested_plan": suggested_plan,
            "plan_ready": bool(search_results and suggested_plan),
        }

    # 获取搜索结果和用户特征
    search_results = state.get("search_results", [])
    user_features = state.get("user_features")

    # DEBUG: 日志输出状态信息
    logger.info(f"search_results count: {len(search_results) if search_results else 0}")
    logger.info(f"user_features: {user_features}")
    logger.info(f"fallback_triggered: {state.get('fallback_triggered', False)}")
    logger.info(f"state keys: {list(state.keys())}")

    # 转换 user_features 为 dict
    user_features_dict: dict[str, Any]
    if isinstance(user_features, UserFeatures):
        user_features_dict = user_features.model_dump()
    elif user_features:
        user_features_dict = dict(user_features)  # type: ignore[arg-type]
    else:
        user_features_dict = {}

    # 防御性检查：如果搜索结果为空，触发 Fallback 生成
    # 这是对 FallbackMiddleware 的补充，防止 Agent 跳过 search_pois 工具
    if not search_results:
        logger.warning("search_results is empty, triggering fallback in generator_node")
        return _generate_fallback_response(user_features_dict)

    # 格式化输入（包含 POI ID 以便结构化输出引用）
    formatted_results = _format_search_results_for_structured(search_results)
    formatted_features = _format_user_features(user_features_dict)

    # 构建 Prompt
    prompt = GENERATOR_PROMPT.format(
        user_features=formatted_features,
        search_results=formatted_results,
    )

    # 调用 LLM 生成结构化响应
    llm = _get_llm()

    try:
        # 尝试使用结构化输出
        structured_llm = llm.with_structured_output(GeneratorOutput)
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="请根据以上信息为我生成旅游建议，同时生成结构化的行程安排。"),
        ]
        raw_output = structured_llm.invoke(messages)
        # 确保类型正确
        if not isinstance(raw_output, GeneratorOutput):
            raise TypeError("LLM did not return expected GeneratorOutput type")
        output: GeneratorOutput = raw_output

        response_content = output.message
        suggested_plan = _convert_to_suggested_plan(
            output.daily_itinerary, user_features_dict, search_results
        )
        plan_ready = True

    except Exception:
        # 降级：使用普通输出
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="请根据以上信息为我生成旅游建议。"),
        ]
        llm_response = llm.invoke(messages)
        response_content = (
            str(llm_response.content) if hasattr(llm_response, "content") else str(llm_response)
        )
        suggested_plan = None
        plan_ready = False

    # 发射完成进度
    emit_progress("generator", "计划生成完成", 95)

    return {
        "final_response": response_content,
        "messages": [AIMessage(content=response_content)],
        "recommended_pois": search_results,
        "suggested_plan": suggested_plan,
        "plan_ready": plan_ready,
    }
