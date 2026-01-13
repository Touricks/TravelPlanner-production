"""
Search API Router
=================
搜索接口 - 直接调用 Hybrid Search

POST /api/v1/search - 搜索接口
"""

import logging

from fastapi import APIRouter, HTTPException

from seekdb_agent.api.schemas import POIResultSchema, SearchRequest, SearchResponse
from seekdb_agent.db.connection import get_hybrid_store
from seekdb_agent.db.search import hybrid_search
from seekdb_agent.state import UserFeatures

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    搜索接口

    直接调用 Hybrid Search 进行 POI 搜索，支持多种搜索模式：
    - balanced: 均衡模式（默认）
    - semantic: 语义搜索优先
    - keyword: 关键词匹配优先
    - exact: 精确匹配

    Args:
        request: SearchRequest 包含 query, mode, top_k, city

    Returns:
        SearchResponse 包含搜索结果

    Raises:
        HTTPException: 搜索失败时抛出 500 错误
    """
    try:
        # 获取 VectorStore 实例
        store = get_hybrid_store()

        # 构建 user_features 用于过滤
        user_features: UserFeatures | None = None
        if request.city:
            user_features = UserFeatures(destination=request.city)

        # 调用 Hybrid Search
        # request.mode 已经是 Literal["balanced", "semantic", "keyword", "exact"]
        results = hybrid_search(
            store=store,
            query=request.query,
            user_features=user_features,
            search_mode=request.mode,  # type: ignore[arg-type]
            top_k=request.top_k,
        )

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

        return SearchResponse(
            results=poi_results,
            total=len(poi_results),
            query=request.query,
            mode=request.mode,
        )

    except Exception as e:
        logger.exception("Search API error")
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {e!s}",
        ) from e
