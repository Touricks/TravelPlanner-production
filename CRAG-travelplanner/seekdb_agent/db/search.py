"""
Hybrid Search Module
====================
OceanBase Hybrid Search + AI Rerank 两阶段检索

架构：
- Phase 1: advanced_hybrid_search (Vector + Sparse + Fulltext)
- Phase 2: AI_RERANK (OceanBaseAIFunctions) - 可选
"""

import logging
import os
from pathlib import Path
from typing import Any, Literal

from langchain_core.documents import Document
from langchain_oceanbase.ai_functions import OceanBaseAIFunctions
from langchain_oceanbase.vectorstores import OceanbaseVectorStore

from seekdb_agent.db.city_aliases import get_all_valid_cities, parse_destination
from seekdb_agent.db.sparse_encoder import TFIDFEncoder
from seekdb_agent.state import POIResult, UserFeatures

logger = logging.getLogger(__name__)

# 全局TF-IDF编码器（延迟加载）
_tfidf_encoder: TFIDFEncoder | None = None

# 全局AI Functions客户端（延迟加载）
_ai_functions: OceanBaseAIFunctions | None = None

# 搜索模式权重预设
WEIGHT_PRESETS: dict[str, dict[str, float]] = {
    "balanced": {"vector": 0.4, "sparse": 0.3, "fulltext": 0.3},
    "semantic": {"vector": 0.7, "sparse": 0.2, "fulltext": 0.1},
    "keyword": {"vector": 0.2, "sparse": 0.6, "fulltext": 0.2},
    "exact": {"vector": 0.1, "sparse": 0.2, "fulltext": 0.7},
}

SearchMode = Literal["balanced", "semantic", "keyword", "exact"]


def get_tfidf_encoder() -> TFIDFEncoder:
    """
    获取TF-IDF编码器（延迟加载）
    从数据导出文件训练，确保与数据库中的词汇表一致
    """
    global _tfidf_encoder

    if _tfidf_encoder is None:
        import json

        # 加载POI数据
        data_file = Path(__file__).parent.parent.parent / "data" / "pois_export.json"

        if not data_file.exists():
            logger.error(f"POI 数据文件不存在: {data_file}")
            raise FileNotFoundError(f"POI data file not found: {data_file}")

        try:
            with open(data_file, encoding="utf-8") as f:
                pois = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"POI 数据文件格式错误: {e}")
            raise

        if not pois:
            logger.error("POI 数据文件为空")
            raise ValueError("POI data file is empty")

        # 准备文本（与迁移脚本保持一致）
        texts = []
        for poi in pois:
            parts = [poi["name"]]
            if poi.get("city"):
                parts.append(f"{poi['city']}, {poi.get('state', '')}")
            if poi.get("primary_category"):
                parts.append(poi["primary_category"])
            if poi.get("editorial_summary"):
                parts.append(poi["editorial_summary"])
            texts.append(". ".join(filter(None, parts)))

        # 训练TF-IDF
        encoder = TFIDFEncoder(max_vocab_size=100000)
        encoder.fit(texts)
        _tfidf_encoder = encoder  # 只在成功 fit 后赋值

        logger.info(f"TF-IDF 编码器初始化成功，词汇量: {encoder.get_vocab_size()}")

    return _tfidf_encoder


def get_ai_functions() -> OceanBaseAIFunctions | None:
    """
    获取 AI Functions 客户端（延迟加载）

    Returns:
        OceanBaseAIFunctions 实例，如果配置错误返回 None
    """
    global _ai_functions

    if _ai_functions is None:
        from seekdb_agent.db.connection import get_oceanbase_connection_args

        try:
            connection_args = get_oceanbase_connection_args()
            _ai_functions = OceanBaseAIFunctions(connection_args=connection_args)
            logger.info("AI Functions 客户端初始化成功")
        except Exception as e:
            logger.warning(f"AI Functions 初始化失败，将跳过 rerank: {e}")
            return None

    return _ai_functions


def rerank_results(
    query: str,
    documents: list[str],
    model_name: str | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """
    使用 AI_RERANK 对搜索结果重排序

    Args:
        query: 查询文本
        documents: 待重排序的文档列表
        model_name: Rerank 模型名称（从环境变量读取默认值）
        top_k: 返回的结果数量

    Returns:
        [{"document": str, "score": float, "rank": int}, ...]
        如果 rerank 失败，返回原始顺序
    """
    if not documents:
        return []

    ai = get_ai_functions()
    if ai is None:
        # Fallback: 返回原始顺序
        return [
            {"document": doc, "score": 1.0 / (i + 1), "rank": i}
            for i, doc in enumerate(documents[:top_k])
        ]

    # 从环境变量获取模型名称
    if model_name is None:
        model_name = os.getenv("RERANK_MODEL_NAME", "bge-reranker")

    try:
        reranked = ai.ai_rerank(
            query=query,
            documents=documents,
            model_name=model_name,
            top_k=top_k,
        )
        logger.debug(f"Rerank 完成: {len(reranked)} 条结果")
        return reranked
    except Exception as e:
        logger.warning(f"Rerank 失败，使用原始排序: {e}")
        # Fallback: 返回原始顺序
        return [
            {"document": doc, "score": 1.0 / (i + 1), "rank": i}
            for i, doc in enumerate(documents[:top_k])
        ]


def hybrid_search(
    store: OceanbaseVectorStore,
    query: str,
    user_features: UserFeatures | None = None,
    search_mode: SearchMode = "balanced",
    top_k: int = 20,
    use_rerank: bool = True,
    rerank_model: str | None = None,
) -> list[POIResult]:
    """
    执行 Hybrid Search + 可选 Rerank（两阶段检索）

    流程：
    1. Phase 1: advanced_hybrid_search (Vector + Sparse + Fulltext) 获取候选
    2. Phase 2: AI_RERANK (可选) 提升相关性

    Args:
        store: OceanBase VectorStore实例（需启用hybrid search）
        query: 搜索查询文本
        user_features: 用户特征（用于过滤）
        search_mode: 搜索模式 (balanced/semantic/keyword/exact)
        top_k: 返回结果数量
        use_rerank: 是否使用 AI_RERANK 重排序
        rerank_model: Rerank 模型名称（None 使用环境变量默认值）

    Returns:
        POIResult列表，按相关性排序
    """
    # 获取搜索权重
    weights = get_search_weights(search_mode)

    # 获取TF-IDF编码器并编码查询
    encoder = get_tfidf_encoder()
    sparse_query = encoder.encode(query)

    # Phase 1: Hybrid Search - 获取更多候选
    # 如果有目的地过滤，需要获取更多候选以补偿过滤损耗
    filter_multiplier = 3 if (user_features and user_features.destination) else 1
    rerank_multiplier = 2 if use_rerank else 1
    candidate_k = top_k * filter_multiplier * rerank_multiplier

    results = store.advanced_hybrid_search(
        vector_query=query,
        sparse_query=sparse_query,
        fulltext_query=query,
        modality_weights=weights,
        k=candidate_k,
    )

    if not results:
        return []

    # Phase 1.5: 目的地过滤（在 Rerank 之前）
    if user_features and user_features.destination:
        results = filter_by_destination(results, user_features)
        if not results:
            logger.warning(
                "[Filter] No results after destination filter for '%s'",
                user_features.destination,
            )
            return []

    # Phase 2: Rerank (可选)
    if use_rerank and len(results) > 1:
        doc_texts = [doc.page_content for doc in results]
        reranked = rerank_results(query, doc_texts, rerank_model, top_k)

        # 按 rerank score 重新排序结果
        doc_by_text = {doc.page_content: doc for doc in results}
        sorted_results = []
        for item in reranked:
            doc_text = item.get("document", "")
            if doc_text in doc_by_text:
                sorted_results.append((doc_by_text[doc_text], item.get("score", 0.0)))

        # 如果 rerank 返回结果正常，使用 rerank 排序
        if sorted_results:
            results = [doc for doc, _ in sorted_results]
            scores = [score for _, score in sorted_results]
        else:
            # Fallback: 保持原始排序
            results = results[:top_k]
            scores = [1.0 / (i + 1) for i in range(len(results))]
    else:
        results = results[:top_k]
        scores = [1.0 / (i + 1) for i in range(len(results))]

    # 转换为POIResult
    poi_results = []
    for i, doc in enumerate(results):
        metadata = doc.metadata

        # 构造 address（短期方案：基于 city + state）
        address = metadata.get("address", "")
        if not address and metadata.get("city"):
            address = f"{metadata.get('city')}, {metadata.get('state', '')}"

        poi = POIResult(
            id=metadata.get("id", f"poi_{i}"),
            name=metadata.get("name", "Unknown"),
            city=metadata.get("city"),
            state=metadata.get("state"),
            latitude=metadata.get("latitude"),
            longitude=metadata.get("longitude"),
            rating=metadata.get("rating"),
            reviews_count=metadata.get("reviews_count"),
            price_level=metadata.get("price_level"),
            primary_category=metadata.get("primary_category"),
            editorial_summary=doc.page_content[:200] if doc.page_content else None,
            score=scores[i] if i < len(scores) else 0.0,
            # Java 集成新增字段
            address=address,
            image_url=metadata.get("image_url"),
            opening_hours=metadata.get("opening_hours"),
        )
        poi_results.append(poi)

    return poi_results


def build_filter_conditions(user_features: UserFeatures) -> dict | None:
    """
    根据用户特征构建过滤条件

    Args:
        user_features: 用户特征 (Pydantic BaseModel)

    Returns:
        过滤条件字典（用于OceanBase查询）
    """
    # TODO: Day 3 实现过滤条件构建
    conditions: dict[str, Any] = {}

    if user_features.destination:
        conditions["city"] = user_features.destination

    budget = user_features.budget_meal
    if budget is not None:
        # 根据每餐预算（美元）映射到价格等级
        # budget <= 20: low, 20-50: medium, 50-100: high, >100: luxury
        if budget <= 20:
            conditions["price_levels"] = ["free", "low"]
        elif budget <= 50:
            conditions["price_levels"] = ["low", "medium"]
        elif budget <= 100:
            conditions["price_levels"] = ["medium", "high"]
        else:
            conditions["price_levels"] = ["high", "luxury"]

    return conditions if conditions else None


def filter_by_destination(
    results: list[Document],
    user_features: UserFeatures | None,
) -> list[Document]:
    """
    按目的地城市过滤搜索结果（支持多目的地）

    Args:
        results: 原始搜索结果 (LangChain Document 列表)
        user_features: 用户特征（包含 destination）

    Returns:
        过滤后的结果列表（多目的地时合并返回）

    Example:
        - "Miami" → 返回 Miami 大都市区所有 POI
        - "Miami and Key West" → 返回两地 POI 的合并结果
    """
    if not user_features or not user_features.destination:
        return results  # 无目的地时返回全部

    # 解析多目的地: "Miami and Key West" → ["Miami", "Key West"]
    destinations = parse_destination(user_features.destination)

    if not destinations:
        return results

    # 获取所有有效城市的并集
    valid_cities_lower = get_all_valid_cities(destinations)

    filtered = []
    for doc in results:
        city = doc.metadata.get("city", "")
        if city and city.lower() in valid_cities_lower:
            filtered.append(doc)

    logger.info(
        "[Filter] destinations=%s, valid_cities=%d, before=%d, after=%d",
        destinations,
        len(valid_cities_lower),
        len(results),
        len(filtered),
    )

    # Fallback: 过滤后为空时返回原始结果（避免触发 Gemini fallback）
    if not filtered and results:
        logger.warning(
            "[Filter] No POIs match destination '%s', returning %d unfiltered results",
            user_features.destination,
            len(results),
        )
        return results

    return filtered


def get_search_weights(mode: SearchMode) -> dict[str, float]:
    """获取搜索模式对应的权重"""
    return WEIGHT_PRESETS.get(mode, WEIGHT_PRESETS["balanced"])
