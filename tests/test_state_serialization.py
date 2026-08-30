from abc_core.state import SalonSessionState


def test_canonical_state_round_trips_as_json_without_mutation():
    state = SalonSessionState(tenant_id="T-1", session_id="S-1")
    payload = state.model_dump_json()
    restored = SalonSessionState.model_validate_json(payload)
    assert restored == state
    assert restored.revision == 0
