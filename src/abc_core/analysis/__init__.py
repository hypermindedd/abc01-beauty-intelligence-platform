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
from .ports import AnalysisExtractionRequest, AnalysisExtractionResult, MultimodalAnalysisExtractor
from .registry import CAPTURE_PLANS, capture_plan_for_services
from .runtime import GovernedAnalysisRuntime

__all__ = [
    "AnalysisContractViolation",
    "AnalysisExtractionRequest",
    "AnalysisExtractionResult",
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
    "GovernedAnalysisRuntime",
    "ImageQuality",
    "MultimodalAnalysisExtractor",
    "capture_plan_for_services",
]
