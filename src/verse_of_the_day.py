"""Verse of the Day helper for MindMate.

Uses the public OurManna Verse of the Day endpoint because it is simple,
JSON-based, and does not require API keys for basic usage.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

OURMANNA_VOTD_URL = "https://beta.ourmanna.com/api/v1/get?format=json"
OURMANNA_TIMEOUT_SECONDS = 10.0


@dataclass(slots=True)
class VerseOfTheDay:
    text: str
    reference: str
    version: str | None = None
    link: str | None = None
    source: str = "OurManna"


def _clean_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


async def get_verse_of_the_day() -> VerseOfTheDay:
    """Fetch and normalize a daily verse from OurManna."""
    async with httpx.AsyncClient(timeout=OURMANNA_TIMEOUT_SECONDS, follow_redirects=True) as client:
        response = await client.get(OURMANNA_VOTD_URL)
        response.raise_for_status()
        payload = response.json()

    details = payload.get("verse", {}).get("details", {})
    text = _clean_value(details.get("text"))
    reference = _clean_value(details.get("reference"))
    version = _clean_value(details.get("version")) or None
    link = _clean_value(details.get("verseurl")) or None

    if not text or not reference:
        raise ValueError("Verse of the Day response missing text or reference")

    return VerseOfTheDay(
        text=text,
        reference=reference,
        version=version,
        link=link,
    )
