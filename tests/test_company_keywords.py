from app.services.company_keywords import generate_tender_search_keywords


def test_ai_company_keywords_are_specific_and_filter_generic_words():
    profile = {
        "interest_tags": ["AI & Automation", "Technology", "Support"],
        "tender_topics": ["NLP", "Government services"],
        "metadata": {
            "domains": ["AI & Automation", "Technology Services"],
            "capabilities": ["Predictive Analytics", "Software Development"],
            "technologies": ["ML", "Data Analytics"],
            "summary": "We build artificial intelligence, NLP, automation, and analytics systems.",
        },
    }

    keywords = generate_tender_search_keywords(profile, max_keywords=20)

    assert "artificial intelligence" in keywords
    assert "automation" in keywords
    assert "natural language processing" in keywords
    assert "predictive analytics" in keywords
    assert "data analytics" in keywords
    assert "software development" in keywords
    assert "government" not in keywords
    assert "management" not in keywords
    assert "experience" not in keywords
    assert "technology" not in keywords
    assert "services" not in keywords
    assert "support" not in keywords
