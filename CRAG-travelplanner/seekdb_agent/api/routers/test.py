"""
Testing API Router
==================
测试接口 - 独立测试 CRAG Agent 各组件

POST /test/collect     - 特征提取测试
POST /test/validate    - 特征验证测试
POST /test/search-raw  - 纯搜索测试
POST /test/evaluate    - 质量评估测试
POST /test/refine      - 查询修正测试
POST /test/search-crag - CRAG搜索测试
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from seekdb_agent.api.schemas import (
    POIResultSchema,
    TestCollectRequest,
    TestCollectResponse,
    TestEvaluateRequest,
    TestEvaluateResponse,
    TestRefineRequest,
    TestRefineResponse,
    TestSearchCRAGRequest,
    TestSearchCRAGResponse,
    TestSearchRawRequest,
    TestSearchRawResponse,
    TestValidateRequest,
    TestValidateResponse,
)
from seekdb_agent.db.connection import get_hybrid_store
from seekdb_agent.db.search import get_search_weights, hybrid_search
from seekdb_agent.llm import get_cached_llm
from seekdb_agent.middleware.grading import create_grader
from seekdb_agent.middleware.refiner import REFINER_SYSTEM_PROMPT, RefinedQuery
from seekdb_agent.nodes import collector_node, validator_node
from seekdb_agent.state import UserFeatures

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["testing"])

# 核心必填字段列表
CORE_REQUIRED_FIELDS = [
    "destination",
    "travel_days",
    "interests",
    "budget_meal",
    "transportation",
    "pois_per_day",
]


@router.post("/collect", response_model=TestCollectResponse)
async def test_collect(request: TestCollectRequest) -> TestCollectResponse:
    """
    特征提取测试

    测试 collector_node 从用户消息提取结构化特征的能力。

    Args:
        request: TestCollectRequest 包含 message

    Returns:
        TestCollectResponse 包含提取的 user_features
    """
    try:
        # 构建 state
        state = {"messages": [HumanMessage(content=request.message)]}

        # 调用 collector_node
        result = collector_node(state)  # type: ignore[arg-type]

        # 提取 user_features
        user_features = result.get("user_features", {})

        # 转换为字典格式
        if hasattr(user_features, "model_dump"):
            features_dict = user_features.model_dump()
        elif isinstance(user_features, dict):
            features_dict = user_features
        else:
            features_dict = dict(user_features)

        return TestCollectResponse(
            user_features=features_dict,
            extraction_success=True,
        )

    except Exception as e:
        logger.exception("Collect test error")
        raise HTTPException(
            status_code=500,
            detail=f"特征提取失败: {e!s}",
        ) from e


@router.post("/validate", response_model=TestValidateResponse)
async def test_validate(request: TestValidateRequest) -> TestValidateResponse:
    """
    特征验证测试

    测试 validator_node 的两级字段分类验证逻辑。

    Args:
        request: TestValidateRequest 包含 user_features

    Returns:
        TestValidateResponse 包含验证结果
    """
    try:
        # 构建 state
        state = {"user_features": request.user_features}

        # 调用 validator_node
        result = validator_node(state)  # type: ignore[arg-type]

        # 计算核心字段状态
        core_fields_status = {}
        for field in CORE_REQUIRED_FIELDS:
            value = request.user_features.get(field)
            # 检查字段是否有效
            if field in ["interests", "must_visit", "dietary_options"]:
                core_fields_status[field] = bool(value and len(value) > 0)
            elif field in ["travel_days", "pois_per_day"]:
                core_fields_status[field] = value is not None and value != 0
            else:
                core_fields_status[field] = bool(value and value != "")

        return TestValidateResponse(
            feature_complete=result.get("feature_complete", False),
            missing_features=result.get("missing_features", []),
            core_fields_status=core_fields_status,
        )

    except Exception as e:
        logger.exception("Validate test error")
        raise HTTPException(
            status_code=500,
            detail=f"特征验证失败: {e!s}",
        ) from e


@router.post("/search-raw", response_model=TestSearchRawResponse)
async def test_search_raw(request: TestSearchRawRequest) -> TestSearchRawResponse:
    """
    纯搜索测试

    直接测试 hybrid_search 函数（无 CRAG 中间件）。

    Args:
        request: TestSearchRawRequest 包含搜索参数

    Returns:
        TestSearchRawResponse 包含搜索结果
    """
    try:
        # 获取 VectorStore 实例
        store = get_hybrid_store()

        # 构建 user_features 用于过滤
        user_features: UserFeatures | None = None
        if request.city:
            user_features = UserFeatures(destination=request.city)

        # 调用 hybrid_search
        results = hybrid_search(
            store=store,
            query=request.query,
            user_features=user_features,
            search_mode=request.mode,  # type: ignore[arg-type]
            top_k=request.top_k,
            use_rerank=request.use_rerank,
        )

        # 获取搜索权重
        weights = get_search_weights(request.mode)  # type: ignore[arg-type]

        # 转换结果格式
        poi_results = []
        for poi in results:
            poi_schema = POIResultSchema(
                id=poi.id,
                name=poi.name,
                city=poi.city,
                state=poi.state,
                rating=poi.rating,
                reviews_count=poi.reviews_count,
                price_level=poi.price_level,
                primary_category=poi.primary_category,
                editorial_summary=poi.editorial_summary,
                score=poi.score,
            )
            poi_results.append(poi_schema)

        return TestSearchRawResponse(
            results=poi_results,
            total=len(poi_results),
            search_mode=request.mode,
            weights=weights,
            rerank_applied=request.use_rerank,
        )

    except Exception as e:
        logger.exception("Search raw test error")
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {e!s}",
        ) from e


@router.post("/evaluate", response_model=TestEvaluateResponse)
async def test_evaluate(request: TestEvaluateRequest) -> TestEvaluateResponse:
    """
    质量评估测试

    测试 DocumentGradingMiddleware 的文档相关性评估。

    Args:
        request: TestEvaluateRequest 包含 query 和 document

    Returns:
        TestEvaluateResponse 包含评估结果
    """
    try:
        # 获取 LLM 并创建 grader
        llm = get_cached_llm(temperature=0.0)
        grader = create_grader(llm)

        # 调用评估器
        result = grader.invoke(
            {
                "question": request.query,
                "document": request.document[:2000],  # 截断避免超长
            }
        )

        # 处理结果
        if result is None:
            return TestEvaluateResponse(
                binary_score="unknown",
                reasoning="评估器返回空结果",
                is_relevant=False,
            )

        binary_score = getattr(result, "binary_score", "unknown")
        reasoning = getattr(result, "reasoning", "")
        is_relevant = binary_score.lower() == "yes"

        return TestEvaluateResponse(
            binary_score=binary_score,
            reasoning=reasoning,
            is_relevant=is_relevant,
        )

    except Exception as e:
        logger.exception("Evaluate test error")
        raise HTTPException(
            status_code=500,
            detail=f"质量评估失败: {e!s}",
        ) from e


@router.post("/refine", response_model=TestRefineResponse)
async def test_refine(request: TestRefineRequest) -> TestRefineResponse:
    """
    查询修正测试

    测试 QueryRefinerMiddleware 的查询优化能力。

    Args:
        request: TestRefineRequest 包含原始查询和上下文

    Returns:
        TestRefineResponse 包含修正后的查询
    """
    try:
        from langchain_core.prompts import ChatPromptTemplate

        # 获取 LLM
        llm = get_cached_llm(temperature=0.7)

        # 创建 refiner chain
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", REFINER_SYSTEM_PROMPT),
                (
                    "human",
                    """**原查询：** {original_query}
**失败类型：** {error_type}
**用户兴趣：** {interests}
**目的地：** {destination}
**已尝试查询：** {tried_queries}

请生成改进的查询。""",
                ),
            ]
        )
        refiner_chain = prompt | llm.with_structured_output(RefinedQuery)

        # 调用修正器
        result = refiner_chain.invoke(
            {
                "original_query": request.original_query,
                "error_type": request.error_type,
                "interests": ", ".join(request.interests) if request.interests else "未指定",
                "destination": request.destination or "未知",
                "tried_queries": (
                    ", ".join(request.tried_queries) if request.tried_queries else "无"
                ),
            }
        )

        # 处理结果
        if result is None:
            return TestRefineResponse(
                refined_query=request.original_query,
                modification_reason="修正器返回空结果，保留原查询",
            )

        refined_query = getattr(result, "refined_query", request.original_query)
        modification_reason = getattr(result, "modification_reason", "")

        return TestRefineResponse(
            refined_query=str(refined_query),
            modification_reason=str(modification_reason),
        )

    except Exception as e:
        logger.exception("Refine test error")
        raise HTTPException(
            status_code=500,
            detail=f"查询修正失败: {e!s}",
        ) from e


@router.post("/search-crag", response_model=TestSearchCRAGResponse)
async def test_search_crag(request: TestSearchCRAGRequest) -> TestSearchCRAGResponse:
    """
    CRAG 搜索测试

    测试完整 CRAG 搜索流程（可配置中间件）。

    Args:
        request: TestSearchCRAGRequest 包含搜索参数和中间件配置

    Returns:
        TestSearchCRAGResponse 包含搜索结果和中间件状态
    """
    try:
        from seekdb_agent.agents.search_agent import create_search_agent

        # 创建配置化的 search agent
        agent = create_search_agent(
            include_grading=request.include_grading,
            include_refiner=request.include_refiner,
            include_fallback=request.include_fallback,
            max_retry=request.max_retry,
        )

        # 构建 state
        state: dict[str, Any] = {
            "messages": [HumanMessage(content=request.query)],
        }

        if request.user_features:
            state["user_features"] = request.user_features

        # 调用 agent
        result = agent.invoke(state)

        # 提取搜索结果
        search_results = result.get("search_results", [])
        poi_results = []
        for poi in search_results:
            poi_schema = POIResultSchema(
                id=getattr(poi, "id", "unknown"),
                name=getattr(poi, "name", "Unknown"),
                city=getattr(poi, "city", None),
                state=getattr(poi, "state", None),
                rating=getattr(poi, "rating", None),
                reviews_count=getattr(poi, "reviews_count", None),
                price_level=getattr(poi, "price_level", None),
                primary_category=getattr(poi, "primary_category", None),
                editorial_summary=getattr(poi, "editorial_summary", None),
                score=getattr(poi, "score", 0.0),
            )
            poi_results.append(poi_schema)

        return TestSearchCRAGResponse(
            results=poi_results,
            result_quality=result.get("result_quality"),
            retry_count=result.get("retry_count", 0),
            fallback_triggered=result.get("fallback_triggered", False),
            refined_query=result.get("refined_query"),
        )

    except Exception as e:
        logger.exception("CRAG search test error")
        raise HTTPException(
            status_code=500,
            detail=f"CRAG搜索失败: {e!s}",
        ) from e
