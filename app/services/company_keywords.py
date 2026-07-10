"""
Company-specific tender discovery keyword generation.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


GENERIC_KEYWORDS = {
    "annual",
    "business",
    "company",
    "consulting",
    "delivery",
    "development",
    "engineering",
    "enterprise",
    "experience",
    "government",
    "industries",
    "industry",
    "infrastructure",
    "management",
    "platform",
    "private",
    "project",
    "projects",
    "public sector",
    "service",
    "services",
    "solution",
    "solutions",
    "support",
    "system",
    "systems",
    "technology",
    "technologies",
}

IMPORTANT_PHRASES = [
    "artificial intelligence",
    "machine learning",
    "generative ai",
    "large language model",
    "natural language processing",
    "predictive analytics",
    "prescriptive analytics",
    "computer vision",
    "data analytics",
    "data engineering",
    "business intelligence",
    "process automation",
    "robotic process automation",
    "cloud computing",
    "cybersecurity",
    "software development",
    "web application",
    "mobile application",
    "devops",
    "mlops",
    "big data",
    "chatbot",
    "ai agent",
    "automation",
]

ABBREVIATION_MAP = {
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "llm": "large language model",
    "bi": "business intelligence",
    "rpa": "robotic process automation",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_keyword(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    text = text.replace("&", " and ")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9+#.]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return ABBREVIATION_MAP.get(text, text)


def generate_tender_search_keywords(profile: Dict[str, Any], max_keywords: int = 12) -> List[str]:
    metadata = profile.get("metadata") or {}
    candidates: List[str] = []

    priority_fields = [
        profile.get("tender_topics") or [],
        profile.get("interest_tags") or [],
        metadata.get("domains") or [],
        metadata.get("capabilities") or [],
        metadata.get("technologies") or [],
        metadata.get("industries") or [],
    ]
    for values in priority_fields:
        candidates.extend(_candidate_terms(values))

    summary = " ".join(
        str(part or "")
        for part in [
            metadata.get("summary"),
            profile.get("description"),
            (profile.get("website_scrape") or {}).get("extracted_text", "")[:3000],
        ]
    ).lower()
    for phrase in IMPORTANT_PHRASES:
        if phrase in summary:
            candidates.append(phrase)

    # Useful expansions for common AI profile wording.
    normalized_blob = " ".join(normalize_keyword(item) for item in candidates) + " " + normalize_keyword(summary)
    if "artificial intelligence" in normalized_blob:
        candidates.extend(["machine learning", "automation"])
    if "machine learning" in normalized_blob:
        candidates.extend(["predictive analytics", "data analytics"])
    if "natural language processing" in normalized_blob:
        candidates.extend(["chatbot", "large language model"])

    keywords: List[str] = []
    seen = set()
    for candidate in candidates:
        keyword = normalize_keyword(candidate)
        if not _is_useful_keyword(keyword) or keyword in seen:
            continue
        seen.add(keyword)
        keywords.append(keyword)
        if len(keywords) >= max_keywords:
            break

    return keywords


def _candidate_terms(values: Iterable[Any]) -> List[str]:
    terms: List[str] = []
    for value in values:
        keyword = normalize_keyword(value)
        if not keyword:
            continue
        terms.append(keyword)

        for part in re.split(r"\band\b|,|/", keyword):
            cleaned = normalize_keyword(part)
            if cleaned and cleaned != keyword:
                terms.append(cleaned)

        for phrase in IMPORTANT_PHRASES:
            if phrase in keyword:
                terms.append(phrase)

    return terms


def _is_useful_keyword(keyword: str) -> bool:
    if not keyword or keyword in GENERIC_KEYWORDS:
        return False
    if len(keyword) < 3:
        return False
    words = keyword.split()
    if len(words) == 1 and words[0] in GENERIC_KEYWORDS:
        return False
    if len(words) > 5:
        return False
    if all(word in GENERIC_KEYWORDS for word in words):
        return False
    return True
