"""Brave web search helper for MindMate.

This module provides a simple wrapper around the Brave Search API
so the bot can fetch fresh web results when explicitly requested.

Usage pattern (v1, minimal & opt-in):
- User sends a message starting with "web:" (e.g. "web: bitcoin price today").
- The bot calls `search_web` with the rest of the text as the query.
- The returned string is injected into the LLM prompt as additional context.

No background/implicit calls are made.
"""

from __future__ import annotations

import logging
import os
from typing import List

import httpx

logger = logging.getLogger(__name__)

BRAVE_SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class WebSearchError(Exception):
    """Custom exception for web search failures."""


def _get_brave_api_key() -> str:
    """Read Brave API key from environment.

    Looks for BRAVE_API_KEY first, then BRAVE_SEARCH_API as a fallback.
    Keys are never logged.
    """

    key = os.getenv("BRAVE_API_KEY") or os.getenv("BRAVE_SEARCH_API")
    if not key:
        raise WebSearchError(
            "Brave API key not configured. Set BRAVE_API_KEY or BRAVE_SEARCH_API in the environment."
        )
    return key


def search_web(query: str, max_results: int = 5) -> str:
    """Perform a Brave web search and return a text summary.

    Parameters
    ----------
    query: str
        The search query text.
    max_results: int, optional
        Maximum number of results to include (default: 5, hard-capped at 10).

    Returns
    -------
    str
        A text block containing a short, LLM-friendly summary of results.
        If the search fails, a human-friendly error message string is
        returned instead of raising, so callers can still reply.
    """

    query = (query or "").strip()
    if not query:
        return "No web search query provided. Please include a topic after `web:`."

    # Be defensive with result count and network behaviour
    max_results = max(1, min(int(max_results or 5), 10))

    try:
        api_key = _get_brave_api_key()
    except WebSearchError as e:
        # Log only the fact that config is missing, never the key
        logger.warning(f"Web search unavailable: {e}")
        return (
            "Web search is not configured yet (missing BRAVE_API_KEY). "
            "Ask the maintainer to set it in the environment."
        )

    headers = {
        # Brave uses this header for API key auth
        "X-Subscription-Token": api_key,
        "Accept": "application/json",
    }

    params = {
        "q": query,
        "count": max_results,
        # Keep it generic; the LLM can localise/interpret results
        "safesearch": "moderate",
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(BRAVE_SEARCH_ENDPOINT, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPStatusError as e:
        logger.error("Brave search HTTP error: %s - %s", e.response.status_code, e.response.text[:500])
        return (
            "I tried to search the web, but the search service returned an error. "
            "Please try again in a bit or rephrase your query."
        )
    except httpx.RequestError as e:
        logger.error("Brave search network error: %s", str(e))
        return (
            "I couldn't reach the web search service (network issue). "
            "Please try again in a moment."
        )
    except Exception as e:  # pragma: no cover - defensive catch
        logger.exception("Unexpected error during Brave web search: %s", str(e))
        return "Something went wrong while searching the web. Please try again."

    # Brave returns results under data["web"]["results"] in the v1 API
    web_block = (data or {}).get("web") or {}
    results: List[dict] = web_block.get("results") or []

    if not results:
        return (
            "I searched the web but couldn't find any clear results for that. "
            "Try being more specific with your question."
        )

    lines: List[str] = [
        f"Web search results for: {query}",
        "",
    ]

    for idx, item in enumerate(results[:max_results], start=1):
        title = (item.get("title") or "(no title)").strip()
        url = (item.get("url") or "").strip()
        snippet = (item.get("description") or item.get("snippet") or "").strip()

        line = f"{idx}. {title}"
        if url:
            line += f"\n   {url}"
        if snippet:
            line += f"\n   Summary: {snippet}"
        lines.append(line)
        lines.append("")

    lines.append(
        "Use these results as up-to-date context. "
        "If they don't fully answer the question, say so and reason carefully."
    )

    return "\n".join(lines)
