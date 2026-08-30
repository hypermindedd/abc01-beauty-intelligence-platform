"""Cross-domain capture, evidence and beauty-analysis contracts for R02.5."""

from .contracts import (
    AnalysisFinding,
    AnalysisStrategy,
    BeautyAnalysisBundle,
    CaptureAssessment,
    CaptureInput,
    CapturePlan,
    CaptureRequirement,
    CaptureView,
    Domain,
    FindingVisibility,
    ImageQuality,
)
from .engine import AnalysisContractViolation, CrossDomainAnalysisEngine
from .registry import CAPTURE_PLANS, capture_plan_for_services

__all__ = [
    "AnalysisContractViolation",
    "AnalysisFinding",
    "AnalysisStrategy",
    "BeautyAnalysisBundle",
    "CAPTURE_PLANS",
    "CaptureAssessment",
    "CaptureInput",
    "CapturePlan",
    "CaptureRequirement",
    "CaptureView",
    "CrossDomainAnalysisEngine",
    "Domain",
    "FindingVisibility",
    "ImageQuality",
    "capture_plan_for_services",
]
