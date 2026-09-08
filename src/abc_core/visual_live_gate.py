"""R03.6 evidence gate for representative visual validation; never fabricates live PASS."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VisualDomain(StrEnum):
    HAIR = "HAIR"
    HAIR_COLOR = "HAIR_COLOR"
    MAKEUP = "MAKEUP"
    NAILS = "NAILS"
    MENS_HAIR_BEARD = "MENS_HAIR_BEARD"
    BRIDAL_GROOM = "BRIDAL_GROOM"


class ReviewVerdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    PENDING = "PENDING"


@dataclass(frozen=True)
class RepresentativeVisualEvidence:
    domain: VisualDomain
    case_id: str
    provider_execution_id: str
    composite_sha256: str
    qa_approved: bool
    human_review: ReviewVerdict
    reviewer_id: str = ""

    def __post_init__(self) -> None:
        if not self.case_id or not self.provider_execution_id:
            raise ValueError("R03.6 requires a real case and provider execution identifier")
        if len(self.composite_sha256) != 64:
            raise ValueError("R03.6 requires a SHA-256 composite digest")
        if self.human_review is ReviewVerdict.PASS and not self.reviewer_id:
            raise ValueError("a passing human review requires reviewer attribution")


@dataclass(frozen=True)
class R03_6GateDecision:
    verdict: ReviewVerdict
    missing_domains: tuple[VisualDomain, ...]
    failed_domains: tuple[VisualDomain, ...]
    runtime_product_pass: bool = False
    pilot_ready: bool = False
    production_ready: bool = False


def evaluate_r03_6(evidence: tuple[RepresentativeVisualEvidence, ...]) -> R03_6GateDecision:
    by_domain = {item.domain: item for item in evidence}
    missing = tuple(domain for domain in VisualDomain if domain not in by_domain)
    failed = tuple(
        domain for domain, item in by_domain.items()
        if not item.qa_approved or item.human_review is ReviewVerdict.FAIL
    )
    pending = any(item.human_review is ReviewVerdict.PENDING for item in by_domain.values())
    verdict = ReviewVerdict.FAIL if failed else ReviewVerdict.PENDING if missing or pending else ReviewVerdict.PASS
    return R03_6GateDecision(verdict, missing, failed)
