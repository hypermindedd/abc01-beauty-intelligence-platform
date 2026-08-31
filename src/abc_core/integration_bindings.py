"""R02.7 integration ownership bindings from frozen ABC agent semantics."""

R02_7_AGENT_BINDINGS = {
    "AG-06": "SERVICE_INTELLIGENCE",
    "AG-08": "SAFETY_AND_BOUNDARY_CONTROL",
    "AG-10": "OUTPUT_AND_HANDOFF",
}

if set(R02_7_AGENT_BINDINGS) != {"AG-06", "AG-08", "AG-10"}:
    raise RuntimeError("R02.7 agent binding set drift")
