"""
Jina Reranker Module
====================
使用 Jina Reranker API 对搜索结果重排序

配置（.env）:
- RERANK_MODEL_NAME: 模型名称（默认 jina-reranker-v2-base-multilingual）
- RERANK_API_KEY: Jina API Key
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Jina Reranker API 端点
JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"

# 全局 HTTP 客户端（复用连接）
_http_client: httpx.Client | None = None


def get_http_client() -> httpx.Client:
    """获取 HTTP 客户端（延迟初始化，复用连接）"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=30.0)
    return _http_client


def jina_rerank(
    query: str,
    documents: list[str],
    model_name: str | None = None,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """
    使用 Jina Reranker API 对文档重排序

    Args:
        query: 查询文本
        documents: 待重排序的文档列表
        model_name: Reranker 模型名称（None 使用环境变量默认值）
        top_n: 返回的结果数量

    Returns:
        [{"document": str, "score": float, "index": int}, ...]
        按 score 降序排列

    Raises:
        如果 API 调用失败，返回原始顺序作为 fallback
    """
    if not documents:
        return []

    # 获取配置
    api_key = os.getenv("RERANK_API_KEY")
    if not api_key:
        logger.warning("RERANK_API_KEY not configured, skipping rerank")
        return _fallback_results(documents, top_n)

    if model_name is None:
        model_name = os.getenv("RERANK_MODEL_NAME", "jina-reranker-v2-base-multilingual")

    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model_name,
        "query": query,
        "documents": documents,
        "top_n": min(top_n, len(documents)),
    }

    try:
        client = get_http_client()
        response = client.post(JINA_RERANK_URL, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        # 转换为统一格式
        reranked = []
        for item in results:
            reranked.append(
                {
                    "document": item.get("document", {}).get("text", documents[item["index"]]),
                    "score": item.get("relevance_score", 0.0),
                    "index": item.get("index", 0),
                }
            )

        logger.info(f"Jina rerank completed: {len(reranked)} results, model={model_name}")
        return reranked

    except httpx.HTTPStatusError as e:
        logger.error(f"Jina rerank API error: {e.response.status_code} - {e.response.text}")
        return _fallback_results(documents, top_n)
    except httpx.RequestError as e:
        logger.error(f"Jina rerank request failed: {e}")
        return _fallback_results(documents, top_n)
    except Exception as e:
        logger.error(f"Jina rerank unexpected error: {e}")
        return _fallback_results(documents, top_n)


def _fallback_results(documents: list[str], top_n: int) -> list[dict[str, Any]]:
    """
    Fallback: 返回原始顺序（当 rerank 失败时）

    Args:
        documents: 原始文档列表
        top_n: 返回数量

    Returns:
        原始顺序的结果，score 按倒数衰减
    """
    return [
        {"document": doc, "score": 1.0 / (i + 1), "index": i}
        for i, doc in enumerate(documents[:top_n])
    ]


def close_http_client() -> None:
    """关闭 HTTP 客户端（用于测试清理）"""
    global _http_client
    if _http_client is not None:
        _http_client.close()
        _http_client = None
