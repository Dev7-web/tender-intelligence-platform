"""
Matching utilities for improved tender-company matching.
Provides semantic matching, synonym handling, and fuzzy matching capabilities.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

# Domain synonyms and related terms mapping - PRECISE coverage to avoid false matches
DOMAIN_SYNONYMS: Dict[str, Set[str]] = {
    # Audio Visual related - REMOVED short terms like "av" to avoid false matches
    "audio visual": {"audiovisual", "audio visual system", "audio-visual", "audiovisual equipment", "audio video system"},
    "audiovisual equipment": {"audio visual", "audio visual system", "audio-visual", "audiovisual"},
    "audio visual system": {"audio visual", "audiovisual", "audiovisual equipment", "audio-visual"},

    # LED/Display related - specific to LED walls, not generic LED
    "led wall": {"led walls", "led display wall", "video wall", "led video wall"},
    "led walls": {"led wall", "led display wall", "video wall", "led video wall"},
    "video wall": {"led wall", "led walls", "led display wall", "display wall"},
    "led display": {"led screen", "led panel", "digital display panel"},
    "digital signage": {"led signage", "electronic signage", "digital display signage"},

    # Projector related
    "projector": {"projectors", "projection system", "projection equipment", "lcd projector", "dlp projector", "video projector"},
    "projectors": {"projector", "projection system", "projection equipment"},
    "projection system": {"projector", "projectors", "projection equipment"},

    # Museum/Memorial related
    "museum": {"museums", "memorial museum", "heritage museum"},
    "museums": {"museum", "memorial museum", "heritage museum"},
    "memorial": {"memorials", "national memorial", "war memorial", "monument"},
    "memorials": {"memorial", "national memorial", "monuments"},
    "national memorials": {"memorial", "memorials", "national memorial", "monuments"},
    "heritage": {"heritage site", "cultural heritage", "historical"},
    "archaeology": {"archaeological", "heritage", "historical"},

    # Government related - more specific
    "government infrastructure": {"govt infrastructure", "public infrastructure", "government facility"},
    "public sector": {"government sector", "govt sector"},

    # Maintenance related - specific to AV/technical maintenance
    "amc": {"annual maintenance contract", "maintenance contract"},
    "annual maintenance": {"amc", "annual maintenance contract", "yearly maintenance"},
}

# Technology synonyms - PRECISE to avoid false matches
TECH_SYNONYMS: Dict[str, Set[str]] = {
    "audio visual system": {"audiovisual system", "audio-visual system", "audio video system"},
    "led walls": {"led wall", "video wall", "led display wall", "led video wall"},
    "led wall": {"led walls", "video wall", "led display wall"},
    "projector": {"projectors", "projection system", "video projector", "lcd projector", "dlp projector"},
    "projectors": {"projector", "projection system"},
    "interactive panels": {"interactive display", "touch panel", "smart board", "interactive whiteboard"},
}

# Capability to tender requirement mapping - SPECIFIC keywords only
CAPABILITY_KEYWORDS: Dict[str, List[str]] = {
    "av maintenance": ["audio visual maintenance", "audiovisual maintenance", "projector maintenance", "led wall maintenance"],
    "led wall": ["led wall", "led walls", "video wall", "led display wall"],
    "projector": ["projector", "projectors", "projection system", "projection equipment"],
    "audio visual": ["audio visual", "audiovisual", "audio-visual", "audio video"],
    "content production": ["content production", "media production", "video production"],
    "memorial maintenance": ["memorial maintenance", "museum maintenance", "heritage site maintenance"],
}


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    # Convert to lowercase, remove extra whitespace, normalize separators
    text = text.lower().strip()
    text = re.sub(r'[\s\-_/]+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


def expand_with_synonyms(terms: List[str]) -> Set[str]:
    """Expand a list of terms with their synonyms. STRICT matching to avoid false positives."""
    expanded = set()

    # Common words to ignore when checking word overlap
    IGNORE_WORDS = {
        "system", "systems", "service", "services", "equipment", "contract",
        "management", "maintenance", "support", "solution", "solutions",
        "infrastructure", "technology", "technologies", "annual", "comprehensive"
    }

    for term in terms:
        norm_term = normalize_text(term)
        expanded.add(norm_term)

        # Add individual MEANINGFUL words only (not common words)
        for word in norm_term.split():
            if len(word) > 4 and word not in IGNORE_WORDS:
                expanded.add(word)

        # Add direct synonyms - STRICT matching only
        for key, synonyms in DOMAIN_SYNONYMS.items():
            norm_key = normalize_text(key)
            norm_synonyms = {normalize_text(s) for s in synonyms}

            # Exact match only
            if norm_term == norm_key or norm_term in norm_synonyms:
                expanded.add(norm_key)
                expanded.update(norm_synonyms)
            # Partial match - but only if the key phrase is FULLY contained
            elif len(norm_key) > 6 and norm_key in norm_term:
                expanded.add(norm_key)
                expanded.update(norm_synonyms)

        # Add technology synonyms - STRICT matching only
        for key, synonyms in TECH_SYNONYMS.items():
            norm_key = normalize_text(key)
            norm_synonyms = {normalize_text(s) for s in synonyms}

            # Exact match
            if norm_term == norm_key or norm_term in norm_synonyms:
                expanded.add(norm_key)
                expanded.update(norm_synonyms)
            # Partial match - only if key is FULLY contained (not just word overlap)
            elif len(norm_key) > 6 and norm_key in norm_term:
                expanded.add(norm_key)
                expanded.update(norm_synonyms)

    return expanded


def fuzzy_match_score(str1: str, str2: str) -> float:
    """Calculate fuzzy match score between two strings."""
    s1 = normalize_text(str1)
    s2 = normalize_text(str2)

    if not s1 or not s2:
        return 0.0

    if s1 == s2:
        return 1.0

    # Check if one contains the other
    if s1 in s2 or s2 in s1:
        return 0.8

    # Check word overlap
    words1 = set(s1.split())
    words2 = set(s2.split())

    if not words1 or not words2:
        return 0.0

    overlap = words1.intersection(words2)
    if overlap:
        return len(overlap) / max(len(words1), len(words2))

    return 0.0


def semantic_overlap_score(
    tender_values: List[str],
    profile_values: List[str],
) -> Tuple[float, List[str]]:
    """
    Calculate semantic overlap between tender requirements and company profile.
    Returns score and list of matched terms.
    """
    if not tender_values or not profile_values:
        return 0.0, []

    # Expand both with synonyms
    tender_expanded = expand_with_synonyms(tender_values)
    profile_expanded = expand_with_synonyms(profile_values)

    # Direct overlap after synonym expansion
    direct_overlap = tender_expanded.intersection(profile_expanded)

    # Word-level overlap (for partial matches)
    tender_words = set()
    profile_words = set()
    for term in tender_expanded:
        tender_words.update(term.split())
    for term in profile_expanded:
        profile_words.update(term.split())

    # Remove common short words
    stop_words = {"and", "the", "for", "with", "from", "into"}
    tender_words -= stop_words
    profile_words -= stop_words

    word_overlap = tender_words.intersection(profile_words)
    # Filter to meaningful words (length > 3)
    word_overlap = {w for w in word_overlap if len(w) > 3}

    # Fuzzy matching for non-direct matches
    fuzzy_matches = []
    for t_term in tender_expanded:
        for p_term in profile_expanded:
            if t_term not in direct_overlap and p_term not in direct_overlap:
                score = fuzzy_match_score(t_term, p_term)
                if score >= 0.5:  # Lowered threshold
                    fuzzy_matches.append((t_term, p_term, score))

    # Calculate final score with multiple components
    direct_score = len(direct_overlap) / max(len(tender_values), 1) * 0.5
    word_score = len(word_overlap) / max(len(tender_words), 1) * 0.3
    fuzzy_score = sum(m[2] for m in fuzzy_matches) / max(len(tender_values), 1) * 0.2 if fuzzy_matches else 0

    total_score = min(direct_score + word_score + fuzzy_score, 1.0)

    # Boost if we have strong matches
    if len(direct_overlap) >= 2 or len(word_overlap) >= 3:
        total_score = min(total_score * 1.5, 1.0)

    # Collect matched terms for explanation
    matched_terms = list(direct_overlap)[:5]
    if word_overlap:
        matched_terms.append(f"words: {', '.join(list(word_overlap)[:3])}")
    matched_terms.extend([f"{m[0]}~{m[1]}" for m in fuzzy_matches[:2]])

    return total_score, matched_terms[:5]


def extract_keywords_from_text(text: str) -> Set[str]:
    """Extract relevant keywords from text."""
    if not text:
        return set()

    text = normalize_text(text)
    keywords = set()

    # Check for capability keywords
    for capability, terms in CAPABILITY_KEYWORDS.items():
        for term in terms:
            if term in text:
                keywords.add(capability)
                break

    # Check for domain keywords
    for domain in DOMAIN_SYNONYMS.keys():
        if normalize_text(domain) in text:
            keywords.add(normalize_text(domain))

    return keywords


def capability_match_score(
    tender_summary: str,
    tender_title: str,
    company_capabilities: List[str],
) -> Tuple[float, List[str]]:
    """
    Match company capabilities against tender requirements extracted from text.
    Uses STRICT phrase matching to avoid false positives.
    """
    if not company_capabilities:
        return 0.0, []

    tender_text = normalize_text(f"{tender_title} {tender_summary}")
    matches = []
    score = 0.0

    # Define specific capability phrases to look for (not generic words)
    specific_phrases = {
        "audio visual": ["audio visual", "audiovisual", "audio-visual", "av system"],
        "led wall": ["led wall", "led walls", "video wall", "led display wall"],
        "projector": ["projector", "projectors", "projection system", "projection equipment"],
        "maintenance": ["annual maintenance", "amc", "comprehensive maintenance", "maintenance contract"],
        "content production": ["content production", "media production", "video production"],
        "museum": ["museum", "museums", "memorial", "memorials", "heritage"],
    }

    # Check each capability for specific phrase matches
    for cap in company_capabilities:
        cap_lower = normalize_text(cap)
        for category, phrases in specific_phrases.items():
            # Check if capability relates to this category
            if any(phrase in cap_lower for phrase in phrases):
                # Check if tender text mentions this category
                for phrase in phrases:
                    if phrase in tender_text:
                        matches.append(f"{category}:{phrase}")
                        score += 0.25
                        break

    # Cap score and deduplicate matches
    unique_matches = list(set(matches))
    return min(score, 1.0), unique_matches[:4]


def text_keyword_match_score(
    tender_text: str,
    profile_meta: Dict,
) -> Tuple[float, List[str]]:
    """
    Match company profile keywords against tender text (title + summary).
    This catches matches that structured metadata might miss.
    Uses STRICT matching to avoid false positives.
    """
    if not tender_text:
        return 0.0, []

    tender_text_lower = normalize_text(tender_text)
    matched_keywords = []
    total_keywords = 0

    # Check profile domains in tender text - require longer matches
    for domain in profile_meta.get("domains", []):
        domain_norm = normalize_text(domain)
        # Only match if the full domain phrase or significant portion is found
        if len(domain_norm) > 5 and domain_norm in tender_text_lower:
            matched_keywords.append(f"domain:{domain}")
            total_keywords += 1
        # Also check synonyms but require longer matches
        domain_expanded = expand_with_synonyms([domain])
        for term in domain_expanded:
            if len(term) > 8 and term in tender_text_lower:  # Require longer terms
                matched_keywords.append(f"domain:{term}")
                total_keywords += 1
                break

    # Check profile technologies in tender text - require exact technology name
    for tech in profile_meta.get("technologies", []):
        tech_norm = normalize_text(tech)
        if len(tech_norm) > 5 and tech_norm in tender_text_lower:
            matched_keywords.append(f"tech:{tech}")
            total_keywords += 1

    # Check specific capability phrases in tender text
    capability_phrases = [
        "audio visual", "audiovisual", "led wall", "led walls", "video wall",
        "projector", "projectors", "projection", "memorial", "museum"
    ]
    for phrase in capability_phrases:
        if phrase in tender_text_lower:
            matched_keywords.append(f"phrase:{phrase}")
            total_keywords += 1

    if total_keywords == 0:
        return 0.0, []

    # Score based on quality of matches
    score = min(len(matched_keywords) * 0.2, 1.0)
    return score, matched_keywords[:5]


def cross_match_domains_and_text(
    tender_meta: Dict,
    profile_meta: Dict,
) -> Tuple[float, List[str]]:
    """
    Cross-match tender domains with profile tech/capabilities and vice versa.
    This catches when a tender domain matches company technology.
    Uses STRICT matching to avoid false positives.
    """
    matches = []
    score = 0.0

    # Check if tender domains match profile technologies - require meaningful overlap
    tender_domains = set(normalize_text(d) for d in tender_meta.get("domains", []))
    profile_techs = set(normalize_text(t) for t in profile_meta.get("technologies", []))

    # Check for direct phrase containment (not just word overlap)
    for td in tender_domains:
        for pt in profile_techs:
            # Check if tech is contained in domain or vice versa
            if len(pt) > 8 and (pt in td or td in pt):
                matches.append(f"domain-tech:{pt}")
                score += 0.3
            # Check if they share significant words
            td_words = set(td.split())
            pt_words = set(pt.split())
            common = td_words.intersection(pt_words)
            # Require meaningful words (not just 'and', 'the', etc.)
            meaningful_common = {w for w in common if len(w) > 4}
            if len(meaningful_common) >= 2:
                matches.append(f"domain-tech-words:{', '.join(meaningful_common)}")
                score += 0.2

    # Check if specific profile domains appear in tender text
    tender_text = f"{tender_meta.get('title', '')} {tender_meta.get('summary', '')}"
    tender_text_norm = normalize_text(tender_text)

    # Only check for significant profile domain terms
    important_profile_terms = ["museum", "memorial", "heritage", "archaeology", "audio visual", "audiovisual", "led wall", "projector"]
    for domain in profile_meta.get("domains", []):
        domain_norm = normalize_text(domain)
        for term in important_profile_terms:
            if term in domain_norm and term in tender_text_norm:
                matches.append(f"profile-domain-in-text:{term}")
                score += 0.3
                break

    return min(score, 1.0), matches[:3]


def calculate_enhanced_match_score(
    tender_meta: Dict,
    profile_meta: Dict,
    vector_similarity: float,
) -> Tuple[float, List[str]]:
    """
    Calculate enhanced match score using multiple factors.

    Returns:
        Tuple of (final_score, match_reasons)
    """
    reasons = []
    scores = {}

    # 1. Domain matching with synonyms (weight: 0.20)
    domain_score, domain_matches = semantic_overlap_score(
        tender_meta.get("domains", []),
        profile_meta.get("domains", [])
    )
    scores["domain"] = domain_score
    if domain_matches:
        reasons.append(f"Domain match: {', '.join(domain_matches[:3])}")

    # 2. Technology matching with synonyms (weight: 0.20)
    tech_score, tech_matches = semantic_overlap_score(
        tender_meta.get("required_technologies", []),
        profile_meta.get("technologies", [])
    )
    scores["technology"] = tech_score
    if tech_matches:
        reasons.append(f"Technology match: {', '.join(tech_matches[:3])}")

    # 3. Certification matching (weight: 0.10)
    cert_score, cert_matches = semantic_overlap_score(
        tender_meta.get("required_certifications", []),
        profile_meta.get("certifications", [])
    )
    scores["certification"] = cert_score
    if cert_matches:
        reasons.append(f"Certification match: {', '.join(cert_matches[:2])}")

    # 4. Capability matching from text (weight: 0.15)
    cap_score, cap_matches = capability_match_score(
        tender_meta.get("summary", ""),
        tender_meta.get("title", ""),
        profile_meta.get("capabilities", [])
    )
    scores["capability"] = cap_score
    if cap_matches:
        reasons.append(f"Capability match: {', '.join(cap_matches[:3])}")

    # 5. Text keyword matching (weight: 0.15) - NEW
    tender_text = f"{tender_meta.get('title', '')} {tender_meta.get('summary', '')}"
    text_score, text_matches = text_keyword_match_score(tender_text, profile_meta)
    scores["text_match"] = text_score
    if text_matches:
        reasons.append(f"Text match: {', '.join(text_matches[:3])}")

    # 6. Cross-domain matching (weight: 0.10) - NEW
    cross_score, cross_matches = cross_match_domains_and_text(tender_meta, profile_meta)
    scores["cross_match"] = cross_score
    if cross_matches:
        reasons.append(f"Cross match: {', '.join(cross_matches[:2])}")

    # 7. Government sector bonus (weight: 0.05)
    govt_score = 0.0
    if tender_meta.get("sector") and profile_meta.get("government_experience"):
        govt_score = 1.0
        reasons.append("Government sector experience")
    scores["government"] = govt_score

    # 8. Vector similarity (weight: 0.05)
    scores["vector"] = vector_similarity

    # Calculate weighted score
    weights = {
        "domain": 0.20,
        "technology": 0.20,
        "certification": 0.10,
        "capability": 0.15,
        "text_match": 0.15,
        "cross_match": 0.10,
        "government": 0.05,
        "vector": 0.05,
    }

    # Calculate base weighted score
    base_score = sum(scores[k] * weights[k] for k in weights)

    # Dynamic boosting based on match quality
    strong_matches = sum([
        1 if scores["domain"] > 0.5 else 0,
        1 if scores["technology"] > 0.5 else 0,
        1 if scores["capability"] > 0.5 else 0,
        1 if scores["text_match"] > 0.3 else 0,
        1 if scores["cross_match"] > 0.3 else 0,
    ])

    # Boost score if multiple strong matches
    if strong_matches >= 3:
        final_score = min(base_score * 1.5, 1.0)
    elif strong_matches >= 2:
        final_score = min(base_score * 1.3, 1.0)
    else:
        final_score = base_score

    return min(final_score, 1.0), reasons
