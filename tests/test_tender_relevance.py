from app.services.tender_relevance import assess_tender_relevance, build_relevance_terms


def test_ai_profile_relevance_requires_core_ai_terms():
    profile = {
        "interest_tags": ["AI & Automation"],
        "metadata": {
            "summary": "We build artificial intelligence, machine learning, NLP, cloud, and analytics systems.",
            "capabilities": ["Deep Learning", "Natural Language Processing", "Software Development"],
            "technologies": ["Python", "TensorFlow", "AWS"],
            "domains": ["Defence", "Healthcare", "Government"],
        },
    }
    relevant_tender = {
        "scraped_info": {"items": "Artificial intelligence based analytics platform"},
        "metadata": {"summary": "Machine learning software for predictive analytics"},
    }
    unrelated_tender = {
        "scraped_info": {"items": "Pre engineered bunker civil construction work"},
        "metadata": {"summary": "Defence construction with ISO certification"},
    }

    terms = build_relevance_terms(profile)
    assert "artificial intelligence" in terms["core_relevance_terms"]
    assert "machine learning" in terms["core_relevance_terms"]
    assert "defence" not in terms["core_relevance_terms"]
    assert "government" not in terms["core_relevance_terms"]

    assert assess_tender_relevance(profile, relevant_tender)["accepted"] is True
    rejected = assess_tender_relevance(profile, unrelated_tender, search_keyword="machine learning")
    assert rejected["accepted"] is False
    assert "No core profile terms found" in rejected["relevance_reasons"][0]


def test_construction_profile_generates_construction_core_terms():
    profile = {
        "interest_tags": ["Civil Works"],
        "metadata": {
            "summary": "Road construction, building renovation, RCC, and concrete civil works.",
            "capabilities": ["Road construction", "Civil Works", "Building construction"],
            "technologies": [],
            "domains": ["Infrastructure", "Government"],
        },
    }
    tender = {
        "scraped_info": {"items": "Road work and RCC building renovation"},
        "metadata": {"summary": "Civil construction package"},
    }

    terms = build_relevance_terms(profile)
    assert "construction" in terms["core_relevance_terms"]
    assert "civil" in terms["core_relevance_terms"]
    assert "government" not in terms["core_relevance_terms"]
    assert assess_tender_relevance(profile, tender)["accepted"] is True
