import pytest
from abc_core.visual_live_gate import (RepresentativeVisualEvidence, ReviewVerdict, VisualDomain, evaluate_r03_6)


def item(domain, review=ReviewVerdict.PASS, qa=True):
    return RepresentativeVisualEvidence(domain, f"ABC-TC-{domain.value}", f"provider-{domain.value}", "a" * 64, qa, review, "specialist-1" if review is ReviewVerdict.PASS else "")


def test_no_evidence_is_pending_not_live_pass():
    result = evaluate_r03_6(())
    assert result.verdict is ReviewVerdict.PENDING
    assert len(result.missing_domains) == 6
    assert result.runtime_product_pass is False


def test_all_domains_and_attributed_human_review_are_required():
    result = evaluate_r03_6(tuple(item(domain) for domain in VisualDomain))
    assert result.verdict is ReviewVerdict.PASS
    assert result.pilot_ready is False


def test_failed_qa_or_human_review_fails_closed():
    evidence = tuple(item(domain) for domain in VisualDomain)
    changed = evidence[:-1] + (item(VisualDomain.BRIDAL_GROOM, ReviewVerdict.FAIL),)
    assert evaluate_r03_6(changed).verdict is ReviewVerdict.FAIL


def test_passing_human_review_needs_attribution():
    with pytest.raises(ValueError, match="reviewer attribution"):
        RepresentativeVisualEvidence(VisualDomain.HAIR, "case", "provider", "a" * 64, True, ReviewVerdict.PASS)
