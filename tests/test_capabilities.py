from abc_core.capabilities import CAPABILITIES


def test_unimplemented_capabilities_fail_closed():
    assert CAPABILITIES.production_auth is False
    assert CAPABILITIES.production_persistence is False
    assert CAPABILITIES.external_visual_provider is False
    assert CAPABILITIES.deterministic_full_frame_lock_compositor is False
    assert CAPABILITIES.live_cross_domain_validation is False
    assert CAPABILITIES.pilot_ready is False
    assert CAPABILITIES.production_ready is False
