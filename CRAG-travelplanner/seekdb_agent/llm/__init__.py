"""
LLM Factory Module
==================
统一的 LLM 工厂，支持多种 Provider

Usage:
    from seekdb_agent.llm import create_llm, create_fallback_llm

    # 使用默认 provider (从 LLM_PROVIDER 环境变量读取，默认 qwen)
    llm = create_llm()

    # 指定 provider
    llm = create_llm(provider="openai", temperature=0.0)

    # Fallback LLM (优先 Gemini，回退 Qwen)
    fallback_llm = create_fallback_llm()

    # 缓存版本 (用于频繁调用场景)
    cached_llm = get_cached_llm()
"""

from seekdb_agent.llm.factory import (
    LLMProvider,
    create_fallback_llm,
    create_llm,
    get_cached_llm,
    get_default_provider,
    get_provider_config,
)

__all__ = [
    "LLMProvider",
    "create_llm",
    "create_fallback_llm",
    "get_cached_llm",
    "get_default_provider",
    "get_provider_config",
]
