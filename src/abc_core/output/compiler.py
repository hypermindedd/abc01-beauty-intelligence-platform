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


# Exact canonical ID set is authoritative. Human-readable labels are intentionally not invented
# when the frozen authority only supplies the ID range.
OUTPUT_REGISTRY = {output_id: {"output_id": output_id, "authority_label": None} for output_id in OUTPUT_IDS}


class OutputCompiler:
    def compile(self, state: SalonSessionState, request: OutputRequest) -> dict:
        unknown = tuple(output_id for output_id in request.output_ids if output_id not in OUTPUT_REGISTRY)
        if unknown:
            raise OutputContractViolation(f"unknown canonical output ids: {unknown}")
        if len(set(request.output_ids)) != len(request.output_ids):
            raise OutputContractViolation("duplicate output ids")

        if request.audience is OutputAudience.SHARED:
            # Client/shared payload is deliberately free of raw runtime IDs and specialist-only detail.
            payload = {
                "audience": request.audience,
                "requested_output_count": len(request.output_ids),
                "analysis": None,
                "recommendations": None,
                "selection_present": state.client_selection is not None,
                "specialist_validation_status": state.specialist_validation.status if state.specialist_validation else None,
                "service_decision_status": state.service_decision.status if state.service_decision else None,
                "safety_attention_required": any(not flag.resolved for flag in state.safety_flags),
                "final_look_board_present": state.final_look_board is not None,
                "read_only_projection": True,
                "execution_claims": {"booking_completed": False, "payment_completed": False},
            }
            if state.analysis:
                payload["analysis"] = {
                    "shared_summary": state.analysis.shared_summary,
                    "strategy_summary": state.analysis.strategy_summary,
                    "reviewed_by_specialist": state.analysis.reviewed_by_specialist,
                }
            if state.recommendations:
                payload["recommendations"] = tuple(
                    {
                        "title": option.title,
                        "role": option.role,
                        "intensity": option.intensity,
                        "maintenance": option.maintenance,
                        "tradeoff": option.tradeoff,
                        "preview_ready": option.preview_ready,
                    }
                    for option in state.recommendations.core_options + state.recommendations.explore_options
                )
            return payload

        return {
            "output_ids": request.output_ids,
            "audience": request.audience,
            "session_id": state.session_id,
            "revision": state.revision,
            "request": state.request.model_dump(mode="json") if state.request else None,
            "analysis": state.analysis.model_dump(mode="json") if state.analysis else None,
            "recommendations": state.recommendations.model_dump(mode="json") if state.recommendations else None,
            "client_selection": state.client_selection.model_dump(mode="json") if state.client_selection else None,
            "specialist_validation": state.specialist_validation.model_dump(mode="json") if state.specialist_validation else None,
            "service_decision": state.service_decision.model_dump(mode="json") if state.service_decision else None,
            "safety": [flag.model_dump(mode="json") for flag in state.safety_flags],
            "final_look_board": state.final_look_board.model_dump(mode="json") if state.final_look_board else None,
            "read_only_projection": True,
            "execution_claims": {"booking_completed": False, "payment_completed": False},
        }
