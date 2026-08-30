from abc_core.contracts import AGENT_IDS, OUTPUT_IDS, FORBIDDEN_GROOM_IDS


def test_agent_registry_exact():
    assert AGENT_IDS == tuple(f"AG-{i:02d}" for i in range(1, 11))


def test_output_registry_exact():
    assert OUTPUT_IDS == tuple(f"OUT-{i:02d}" for i in range(1, 18))


def test_forbidden_groom_ids_remain_forbidden():
    assert FORBIDDEN_GROOM_IDS == {"SVC-03-008", "CTRL-011", "CTRL-012", "CTRL-013"}
