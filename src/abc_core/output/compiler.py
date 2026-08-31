from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from abc_core.contracts import OUTPUT_IDS
from abc_core.state import SalonSessionState


class OutputAudience(StrEnum):
    SHARED = "SHARED"
    SPECIALIST = "SPECIALIST"


@dataclass(frozen=True)
class OutputRequest:
    output_ids: tuple[str, ...]
    audience: OutputAudience


class OutputContractViolation(RuntimeError):
    pass


OUTPUT_REGISTRY = {output_id: {"output_id": output_id, "authority_label": None} for output_id in OUTPUT_IDS}


class OutputCompiler:
    def compile(self, state: SalonSessionState, request: OutputRequest) -> dict:
        unknown = tuple(output_id for output_id in request.output_ids if output_id not in OUTPUT_REGISTRY)
        if unknown:
            raise OutputContractViolation(f"unknown canonical output ids: {unknown}")
        if len(set(request.output_ids)) != len(request.output_ids):
            raise OutputContractViolation("duplicate output ids")

        payload = {
            "output_ids": request.output_ids,
            "audience": request.audience,
            "session_id": state.session_id,
            "revision": state.revision,
            "request": state.request.model_dump(mode="json") if state.request else None,
            "recommendations": state.recommendations.model_dump(mode="json") if state.recommendations else None,
            "client_selection": state.client_selection.model_dump(mode="json") if state.client_selection else None,
            "specialist_validation": state.specialist_validation.model_dump(mode="json") if state.specialist_validation else None,
            "service_decision": state.service_decision.model_dump(mode="json") if state.service_decision else None,
            "safety": [flag.model_dump(mode="json") for flag in state.safety_flags],
            "final_look_board": state.final_look_board.model_dump(mode="json") if state.final_look_board else None,
            "read_only_projection": True,
            "execution_claims": {"booking_completed": False, "payment_completed": False},
        }
        if state.analysis:
            analysis = state.analysis.model_dump(mode="json")
            if request.audience is OutputAudience.SHARED:
                payload["analysis"] = {
                    "analysis_id": analysis["analysis_id"],
                    "shared_summary": analysis.get("shared_summary", ""),
                    "strategy_summary": analysis.get("strategy_summary", ""),
                    "reviewed_by_specialist": analysis.get("reviewed_by_specialist", False),
                }
            else:
                payload["analysis"] = analysis
        else:
            payload["analysis"] = None
        return payload
