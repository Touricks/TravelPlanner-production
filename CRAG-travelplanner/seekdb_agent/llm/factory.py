"""
LLM Factory Module
==================
统一的 LLM 工厂，支持多种 Provider（通过 OpenAI 兼容协议）

设计原则：
1. 统一使用 ChatOpenAI 作为接口
2. 通过环境变量切换 Provider
3. 向后兼容现有代码
4. 支持 Fallback 策略
"""

import logging
import os
from functools import lru_cache
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

logger = logging.getLogger(__name__)

# 支持的 Provider 类型（均使用 OpenAI 兼容协议）
LLMProvider = Literal["qwen", "openai", "gemini", "deepseek"]
LLM_FALLBACK_PROVIDER = "gemini"
# Provider 配置映射
PROVIDER_CONFIG: dict[str, dict[str, str]] = {
    "qwen": {
        "api_key_var": "QWEN_API_KEY",
        "base_url_var": "QWEN_BASE_URL",
        "model_var": "QWEN_MODEL",
        "default_model": "qwen-plus-latest",
    },
    "openai": {
        "api_key_var": "OPENAI_API_KEY",
        "base_url_var": "OPENAI_BASE_URL",
        "model_var": "OPENAI_MODEL",
        "default_model": "gpt-4-turbo-preview",
    },
    "gemini": {
        "api_key_var": "GEMINI_API_KEY",
        "base_url_var": "GEMINI_BASE_URL",
        "model_var": "GEMINI_MODEL",
        "default_model": "gemini-3-pro-preview",
    },
    "deepseek": {
        "api_key_var": "DEEPSEEK_API_KEY",
        "base_url_var": "DEEPSEEK_BASE_URL",
        "model_var": "DEEPSEEK_MODEL",
        "default_model": "deepseek-chat",
    },
}


def get_default_provider() -> LLMProvider:
    """获取默认 Provider（从环境变量读取，默认 qwen）"""
    provider = os.getenv("LLM_PROVIDER", "qwen").lower()
    if provider not in PROVIDER_CONFIG:
        logger.warning(f"Unknown LLM_PROVIDER '{provider}', falling back to 'qwen'")
        return "qwen"
    return provider  # type: ignore


def get_provider_config(provider: LLMProvider) -> dict[str, str]:
    """
    获取指定 Provider 的配置（用于其他模块复用）

    Args:
        provider: LLM 提供商名称

    Returns:
        包含 api_key, base_url, model 的配置字典

    Example:
        >>> config = get_provider_config("gemini")
        >>> print(config["model"])  # gemini-3-pro-preview
    """
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        raise ValueError(f"Unsupported provider: {provider}")

    return {
        "api_key": os.getenv(config["api_key_var"], ""),
        "base_url": os.getenv(config["base_url_var"], ""),
        "model": os.getenv(config["model_var"], config["default_model"]),
    }


def create_llm(
    provider: LLMProvider | None = None,
    temperature: float = 0.7,
    **kwargs,
) -> BaseChatModel:
    """
    创建 LLM 实例

    Args:
        provider: LLM 提供商（默认从 LLM_PROVIDER 环境变量读取）
        temperature: 温度参数
        **kwargs: 其他 ChatOpenAI 参数（如 max_tokens）

    Returns:
        BaseChatModel 实例

    Raises:
        ValueError: 缺少必要的环境变量

    Example:
        >>> llm = create_llm()  # 使用默认 provider
        >>> llm = create_llm(provider="openai", temperature=0.0)
    """
    provider = provider or get_default_provider()
    config = PROVIDER_CONFIG.get(provider)

    if not config:
        raise ValueError(f"Unsupported provider: {provider}")

    api_key = os.getenv(config["api_key_var"])
    if not api_key:
        raise ValueError(
            f"{config['api_key_var']} environment variable is not set "
            f"(required for provider '{provider}')"
        )

    base_url = os.getenv(config["base_url_var"])
    model = os.getenv(config["model_var"], config["default_model"])

    logger.debug(f"Creating LLM: provider={provider}, model={model}")

    return ChatOpenAI(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
        temperature=temperature,
        **kwargs,
    )


def create_fallback_llm(temperature: float = 0.7) -> BaseChatModel:
    """
    创建 Fallback LLM 实例

    优先级：
    1. LLM_FALLBACK_PROVIDER 环境变量指定的 provider
    2. Gemini（如果配置了 API Key）
    3. OpenAI（如果配置了 API Key）
    4. Qwen（默认）

    Returns:
        BaseChatModel 实例
    """
    # 检查是否指定了 fallback provider
    fallback_provider = os.getenv("LLM_FALLBACK_PROVIDER", "").lower()
    if fallback_provider and fallback_provider in PROVIDER_CONFIG:
        try:
            return create_llm(provider=fallback_provider, temperature=temperature)  # type: ignore
        except ValueError:
            logger.warning(f"Fallback provider '{fallback_provider}' not configured")

    # 尝试 Gemini
    if os.getenv("GEMINI_API_KEY"):
        try:
            return create_llm(provider="gemini", temperature=temperature)
        except Exception as e:
            logger.debug(f"Gemini fallback failed: {e}")

    # 尝试 OpenAI
    if os.getenv("OPENAI_API_KEY"):
        try:
            return create_llm(provider="openai", temperature=temperature)
        except Exception as e:
            logger.debug(f"OpenAI fallback failed: {e}")

    # 回退到 Qwen
    logger.debug("Using Qwen as fallback LLM")
    return create_llm(provider="qwen", temperature=temperature)


@lru_cache(maxsize=4)
def get_cached_llm(
    provider: LLMProvider | None = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """
    获取缓存的 LLM 实例

    适用于需要频繁调用的场景（如 search_agent）

    Note:
        由于使用 lru_cache，相同参数会返回同一实例
        temperature 使用 float 而非 Decimal 以支持缓存

    Args:
        provider: LLM 提供商
        temperature: 温度参数

    Returns:
        BaseChatModel 实例（缓存）
    """
    return create_llm(provider=provider, temperature=temperature)
