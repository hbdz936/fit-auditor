import pytest
from core.verifier import verify_verdict

LINE_MAP = {
    "L001": "Backend engineer with 3 years building REST APIs in Python.",
    "L002": "Led a cross-functional team of 8 engineers on a platform migration.",
    "L003": "Built CI/CD pipelines using GitHub Actions.",
    "L004": "Enjoys hiking and photography on weekends.",
}


def test_literal_keyword_match_stays_matched():
    v = {"requirement": "REST APIs in Python", "status": "MATCHED", "evidence_line_ids": ["L001"]}
    result = verify_verdict(v, LINE_MAP)
    assert result["status"] == "MATCHED"


def test_paraphrase_with_no_shared_keywords_still_verifies():
    # This is the exact failure mode of the old keyword-only verifier.
    v = {"requirement": "mentoring junior engineers", "status": "MATCHED", "evidence_line_ids": ["L002"]}
    result = verify_verdict(v, LINE_MAP)
    assert result["status"] == "MATCHED", (
        "Semantic similarity should catch 'led a team' as support for "
        "'mentoring junior engineers' even with zero literal keyword overlap."
    )


def test_unrelated_citation_is_flagged_unverified():
    v = {"requirement": "Kubernetes orchestration experience", "status": "MATCHED", "evidence_line_ids": ["L004"]}
    result = verify_verdict(v, LINE_MAP)
    assert result["status"] == "UNVERIFIED"
    assert result["verification_note"] is not None


def test_gap_status_is_never_verified_or_flagged():
    v = {"requirement": "AWS Lambda experience", "status": "GAP", "evidence_line_ids": []}
    result = verify_verdict(v, LINE_MAP)
    assert result["status"] == "GAP"
    assert result["verification_note"] is None


def test_matched_with_no_evidence_ids_is_downgraded():
    v = {"requirement": "Python experience", "status": "MATCHED", "evidence_line_ids": []}
    result = verify_verdict(v, LINE_MAP)
    assert result["status"] == "UNVERIFIED"


def test_cicd_match():
    v = {"requirement": "experience with CI/CD pipelines", "status": "MATCHED", "evidence_line_ids": ["L003"]}
    result = verify_verdict(v, LINE_MAP)
    assert result["status"] == "MATCHED"