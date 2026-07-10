"""
Profile-to-tender relevance gate.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


BROAD_CONTEXT_TERMS = {
    "annual",
    "business",
    "company",
    "consulting",
    "contract",
    "defence",
    "department",
    "development",
    "engineering",
    "enterprise",
    "equipment",
    "experience",
    "government",
    "govt",
    "industry",
    "infrastructure",
    "iso",
    "management",
    "maintenance",
    "private",
    "procurement",
    "product",
    "products",
    "project",
    "projects",
    "public",
    "public sector",
    "security",
    "service",
    "services",
    "solution",
    "solutions",
    "support",
    "supply",
    "system",
    "systems",
    "technology",
    "technologies",
    "work",
    "works",
}

GROUP_EXPANSIONS = [
    {
        "triggers": {
            "ai",
            "artificial intelligence",
            "machine learning",
            "ml",
            "deep learning",
            "natural language processing",
            "nlp",
            "large language model",
            "llm",
            "generative ai",
            "computer vision",
            "predictive analytics",
            "prescriptive analytics",
            "data science",
            "data analytics",
            "mlops",
        },
        "terms": {
            "ai",
            "artificial intelligence",
            "machine learning",
            "ml",
            "deep learning",
            "natural language processing",
            "nlp",
            "large language model",
            "llm",
            "generative ai",
            "computer vision",
            "predictive analytics",
            "prescriptive analytics",
            "data science",
            "data analytics",
            "analytics",
            "mlops",
            "big data",
        },
    },
    {
        "triggers": {
            "automation",
            "process automation",
            "robotic process automation",
            "rpa",
            "workflow automation",
            "ai automation",
        },
        "terms": {
            "automation",
            "process automation",
            "robotic process automation",
            "rpa",
            "workflow automation",
        },
    },
    {
        "triggers": {
            "software",
            "software development",
            "application development",
            "web application",
            "mobile application",
            "digital engineering",
            "devops",
        },
        "terms": {
            "software",
            "software development",
            "application development",
            "web application",
            "mobile application",
            "digital engineering",
            "devops",
            "api",
            "portal",
            "dashboard",
        },
    },
    {
        "triggers": {
            "cloud",
            "cloud computing",
            "aws",
            "azure",
            "google cloud",
            "gcp",
            "kubernetes",
            "docker",
        },
        "terms": {
            "cloud",
            "cloud computing",
            "aws",
            "azure",
            "google cloud",
            "gcp",
            "kubernetes",
            "docker",
        },
    },
    {
        "triggers": {
            "cybersecurity",
            "cyber security",
            "information security",
            "network security",
            "vapt",
            "soc",
            "siem",
        },
        "terms": {
            "cybersecurity",
            "cyber security",
            "information security",
            "network security",
            "vapt",
            "soc",
            "siem",
        },
    },
    {
        "triggers": {
            "construction",
            "civil construction",
            "civil works",
            "road construction",
            "road work",
            "building construction",
            "rcc",
            "concrete",
            "bridge",
            "renovation",
            "epc",
        },
        "terms": {
            "construction",
            "civil construction",
            "civil works",
            "civil",
            "road construction",
            "road work",
            "building construction",
            "building",
            "rcc",
            "concrete",
            "cement",
            "bridge",
            "renovation",
            "epc",
        },
    },
    {
        "triggers": {
            "solar",
            "solar pv",
            "renewable energy",
            "energy",
            "power plant",
        },
        "terms": {
            "solar",
            "solar pv",
            "renewable energy",
            "power plant",
        },
    },
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_term(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    text = text.replace("&", " and ")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9+#.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_relevance_terms(profile: Dict[str, Any]) -> Dict[str, List[str]]:
    metadata = profile.get("metadata") or {}
    core_terms: set[str] = set()
    context_terms: set[str] = set()

    priority_values = _flatten(
        [
            profile.get("tender_topics") or [],
            profile.get("interest_tags") or [],
            metadata.get("capabilities") or [],
            metadata.get("technologies") or [],
        ]
    )
    for value in priority_values:
        _add_profile_term(value, core_terms=core_terms, context_terms=context_terms)

    summary = " ".join(
        str(part or "")
        for part in [
            metadata.get("summary"),
            profile.get("description"),
            (profile.get("website_scrape") or {}).get("extracted_text", "")[:3000],
        ]
    )
    summary_norm = normalize_term(summary)
    for group in GROUP_EXPANSIONS:
        if any(_phrase_in_text(trigger, summary_norm) for trigger in group["triggers"]):
            core_terms.update(group["terms"])

    for value in _flatten([metadata.get("domains") or [], metadata.get("industries") or []]):
        term = normalize_term(value)
        if not term:
            continue
        context_terms.add(term)
        for part in _split_term(term):
            if part:
                context_terms.add(part)

    core_terms = {_canonical_core_term(term) for term in core_terms}
    core_terms = {term for term in core_terms if _is_core_term(term)}

    if not core_terms:
        # Fallback for sparse profiles: use non-generic domain/industry terms only
        # when no stronger capability or technology terms were available.
        core_terms = {term for term in context_terms if _is_core_term(term)}

    context_terms = {term for term in context_terms if term and term not in core_terms}
    return {
        "core_relevance_terms": sorted(core_terms, key=lambda item: (-len(item), item)),
        "context_relevance_terms": sorted(context_terms, key=lambda item: (-len(item), item)),
    }


def assess_tender_relevance(
    profile: Dict[str, Any],
    tender: Dict[str, Any],
    *,
    search_keyword: str | None = None,
) -> Dict[str, Any]:
    terms = build_relevance_terms(profile)
    core_terms = terms["core_relevance_terms"]
    context_terms = terms["context_relevance_terms"]
    tender_text = build_tender_relevance_text(tender)

    matched_core_terms = [
        term for term in core_terms
        if _phrase_in_text(term, tender_text)
    ]
    matched_context_terms = [
        term for term in context_terms
        if _phrase_in_text(term, tender_text)
    ][:8]

    accepted = bool(matched_core_terms)
    relevance_score = min(len(matched_core_terms) / max(min(len(core_terms), 5), 1), 1.0)
    if accepted:
        reasons = [f"Matched core profile terms: {', '.join(matched_core_terms[:8])}"]
        if matched_context_terms:
            reasons.append(f"Matched context terms: {', '.join(matched_context_terms[:5])}")
    else:
        expected = ", ".join(core_terms[:8]) if core_terms else "no core terms derived from profile"
        reasons = [f"No core profile terms found in tender text; expected one of: {expected}"]
        if search_keyword:
            reasons.append(f"Rejected result returned for search keyword: {search_keyword}")

    return {
        "accepted": accepted,
        "relevance_status": "accepted" if accepted else "rejected",
        "relevance_score": relevance_score,
        "relevance_reasons": reasons,
        "matched_core_terms": matched_core_terms[:12],
        "matched_context_terms": matched_context_terms,
        **terms,
    }


def build_tender_relevance_text(tender: Dict[str, Any]) -> str:
    metadata = tender.get("metadata") or {}
    scraped = tender.get("scraped_info") or {}
    processed = tender.get("processed_info") or {}
    chunks = [
        metadata.get("title"),
        metadata.get("summary"),
        metadata.get("department"),
        metadata.get("location"),
        " ".join(str(item) for item in (metadata.get("domains") or [])),
        " ".join(str(item) for item in (metadata.get("required_technologies") or [])),
        " ".join(str(item) for item in (metadata.get("required_certifications") or [])),
        scraped.get("title"),
        scraped.get("bid_title"),
        scraped.get("items"),
        scraped.get("department"),
        scraped.get("organisation"),
        processed.get("title"),
        processed.get("summary"),
    ]
    return normalize_term(" ".join(str(part or "") for part in chunks))


def _add_profile_term(value: Any, *, core_terms: set[str], context_terms: set[str]) -> None:
    term = normalize_term(value)
    if not term:
        return
    for expanded in _expand_profile_term(term):
        if _is_core_term(expanded):
            core_terms.add(expanded)
        elif expanded:
            context_terms.add(expanded)


def _expand_profile_term(term: str) -> set[str]:
    expanded = {term}
    tokens = set(term.split())

    if "ai" in tokens:
        expanded.add("artificial intelligence")
    if "ml" in tokens:
        expanded.add("machine learning")
    if "nlp" in tokens:
        expanded.add("natural language processing")
    if "llm" in tokens:
        expanded.add("large language model")
    if "rpa" in tokens:
        expanded.add("robotic process automation")

    for part in _split_term(term):
        expanded.add(part)

    for group in GROUP_EXPANSIONS:
        if any(_phrase_in_text(trigger, term) for trigger in group["triggers"]):
            expanded.update(group["terms"])
    return expanded


def _split_term(term: str) -> List[str]:
    pieces = re.split(r"\band\b|,|/|;|\|", term)
    return [normalize_term(piece) for piece in pieces if normalize_term(piece)]


def _canonical_core_term(term: str) -> str:
    aliases = {
        "ai": "artificial intelligence",
        "ml": "machine learning",
        "nlp": "natural language processing",
        "llm": "large language model",
    }
    return aliases.get(term, term)


def _is_core_term(term: str) -> bool:
    if not term or term in BROAD_CONTEXT_TERMS:
        return False
    if len(term) < 2:
        return False
    words = term.split()
    if len(words) == 1 and words[0] in BROAD_CONTEXT_TERMS:
        return False
    if all(word in BROAD_CONTEXT_TERMS for word in words):
        return False
    return True


def _phrase_in_text(phrase: str, text: str) -> bool:
    normalized_phrase = normalize_term(phrase)
    normalized_text = normalize_term(text)
    if not normalized_phrase or not normalized_text:
        return False
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(normalized_phrase)}(?![a-z0-9])", normalized_text))


def _flatten(values: Iterable[Iterable[Any]]) -> List[Any]:
    flattened: List[Any] = []
    for group in values:
        if isinstance(group, (str, bytes)):
            flattened.append(group)
        else:
            flattened.extend(list(group or []))
    return flattened
