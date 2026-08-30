from __future__ import annotations

from collections.abc import Mapping

from .contracts import CapturePlan, CaptureRequirement, CaptureView, Domain


CAPTURE_PLANS: dict[Domain, CapturePlan] = {
    Domain.HAIR: CapturePlan(
        plan_id="CAP-HAIR-v1",
        domains=(Domain.HAIR,),
        requirements=(
            CaptureRequirement(requirement_id="HAIR-FRONT", view=CaptureView.FRONT, purpose="overall face/hair proportion and frontal hair state"),
            CaptureRequirement(requirement_id="HAIR-LEFT", view=CaptureView.LEFT_PROFILE, purpose="left silhouette, layering and side proportion"),
            CaptureRequirement(requirement_id="HAIR-RIGHT", view=CaptureView.RIGHT_PROFILE, purpose="right silhouette, layering and side proportion"),
            CaptureRequirement(requirement_id="HAIR-BACK", view=CaptureView.BACK, purpose="back shape, length and density distribution"),
        ),
    ),
    Domain.HAIR_COLOR: CapturePlan(
        plan_id="CAP-COLOR-v1",
        domains=(Domain.HAIR_COLOR,),
        requirements=(
            CaptureRequirement(requirement_id="COLOR-FRONT", view=CaptureView.FRONT, purpose="overall visible color distribution and face framing"),
            CaptureRequirement(requirement_id="COLOR-BACK", view=CaptureView.BACK, purpose="visible color distribution through lengths"),
            CaptureRequirement(requirement_id="COLOR-DETAIL", view=CaptureView.EXISTING_COLOR_DETAIL, purpose="visible base, banding, regrowth or tonal detail where observable"),
        ),
    ),
    Domain.MAKEUP: CapturePlan(
        plan_id="CAP-MAKEUP-v1",
        domains=(Domain.MAKEUP,),
        requirements=(
            CaptureRequirement(requirement_id="MAKEUP-FRONT", view=CaptureView.FRONT, purpose="frontal visible features and balance"),
            CaptureRequirement(requirement_id="MAKEUP-LEFT", view=CaptureView.LEFT_PROFILE, purpose="left-side visible feature geometry"),
            CaptureRequirement(requirement_id="MAKEUP-RIGHT", view=CaptureView.RIGHT_PROFILE, purpose="right-side visible feature geometry"),
        ),
    ),
    Domain.NAILS: CapturePlan(
        plan_id="CAP-NAILS-v1",
        domains=(Domain.NAILS,),
        requirements=(
            CaptureRequirement(requirement_id="NAILS-HANDS", view=CaptureView.HANDS, purpose="overall visible hand and nail context"),
            CaptureRequirement(requirement_id="NAILS-DETAIL", view=CaptureView.NAIL_DETAIL, purpose="visible nail shape, length and surface detail"),
        ),
    ),
    Domain.MENS_HAIR_BEARD: CapturePlan(
        plan_id="CAP-MENS-v1",
        domains=(Domain.MENS_HAIR_BEARD,),
        requirements=(
            CaptureRequirement(requirement_id="MENS-FRONT", view=CaptureView.FRONT, purpose="frontal hair/beard balance"),
            CaptureRequirement(requirement_id="MENS-LEFT", view=CaptureView.LEFT_PROFILE, purpose="left fade, sideburn and beard-line context"),
            CaptureRequirement(requirement_id="MENS-RIGHT", view=CaptureView.RIGHT_PROFILE, purpose="right fade, sideburn and beard-line context"),
            CaptureRequirement(requirement_id="MENS-BACK", view=CaptureView.BACK, purpose="back taper and haircut silhouette"),
        ),
    ),
    Domain.BRIDAL_GROOM: CapturePlan(
        plan_id="CAP-EVENT-v1",
        domains=(Domain.BRIDAL_GROOM,),
        requirements=(
            CaptureRequirement(requirement_id="EVENT-FRONT", view=CaptureView.FRONT, purpose="full frontal event-look coordination context"),
            CaptureRequirement(requirement_id="EVENT-LEFT", view=CaptureView.LEFT_PROFILE, purpose="left profile event-look coordination"),
            CaptureRequirement(requirement_id="EVENT-RIGHT", view=CaptureView.RIGHT_PROFILE, purpose="right profile event-look coordination"),
        ),
    ),
    Domain.CONTROLLED_SERVICE: CapturePlan(
        plan_id="CAP-CONTROLLED-v1",
        domains=(Domain.CONTROLLED_SERVICE,),
        requirements=(
            CaptureRequirement(requirement_id="CONTROLLED-FRONT", view=CaptureView.FRONT, purpose="minimum visible context before professional check"),
            CaptureRequirement(requirement_id="CONTROLLED-DETAIL", view=CaptureView.DETAIL, purpose="service-relevant visible detail before professional check"),
        ),
    ),
}


def capture_plan_for_services(
    service_ids: tuple[str, ...],
    *,
    service_domain_map: Mapping[str, Domain],
) -> tuple[CapturePlan, ...]:
    """Resolve capture plans without guessing service ontology.

    The caller must supply the governed service→domain mapping. Unknown service IDs
    fail closed rather than being inferred from prefixes, labels, or model output.
    """
    domains: list[Domain] = []
    for service_id in service_ids:
        try:
            domain = service_domain_map[service_id]
        except KeyError as exc:
            raise KeyError(f"service domain is not governed for {service_id}") from exc
        if domain not in domains:
            domains.append(domain)
    return tuple(CAPTURE_PLANS[domain] for domain in domains)
