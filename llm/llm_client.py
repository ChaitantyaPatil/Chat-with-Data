# ============================================================
#  LLM Client — LangChain + NVIDIA API
#  Wraps ChatOpenAI with custom base_url for the NVIDIA
#  integration endpoint.
# ============================================================

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_llm(
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> ChatOpenAI:
    """
    Return a cached LangChain ChatOpenAI client configured for
    the NVIDIA API endpoint.

    Args:
        temperature: Sampling temperature (0 = deterministic).
        max_tokens: Maximum tokens in the response.

    Returns:
        A ready-to-use :class:`ChatOpenAI` instance.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY is not set. Please configure your .env file.")
        raise ValueError("OPENAI_API_KEY is missing from environment configuration.")

    logger.info(
        "Initializing LLM — model=%s, base_url=%s",
        settings.openai_model,
        settings.openai_base_url,
    )

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return llm
