from app.services.matching_utils import calculate_enhanced_match_score


def test_enhanced_match_score_with_overlap():
    tender_meta = {
        "title": "Solar infrastructure maintenance",
        "summary": "Supply and installation of solar modules and monitoring systems.",
        "domains": ["Energy", "Infrastructure"],
        "required_technologies": ["Solar PV", "Monitoring"],
        "required_certifications": ["ISO 9001"],
        "sector": "government",
    }
    company_meta = {
        "domains": ["Energy", "Technology"],
        "technologies": ["Solar PV", "IoT Monitoring"],
        "certifications": ["ISO 9001", "ISO 14001"],
        "capabilities": ["Solar installation", "Public works maintenance"],
        "government_experience": True,
    }

    score, reasons = calculate_enhanced_match_score(tender_meta, company_meta, vector_similarity=0.66)

    assert score > 0.3
    assert score <= 1.0
    assert isinstance(reasons, list)
    assert len(reasons) > 0
