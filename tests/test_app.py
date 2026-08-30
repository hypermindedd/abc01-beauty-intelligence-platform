from fastapi.testclient import TestClient

from abc_core.app import app

client = TestClient(app)


def test_health_is_explicitly_engineering_only():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["engineering_scaffold"] is True
    assert data["pilot_ready"] is False
    assert data["production_ready"] is False


def test_build_info_exposes_contract_not_fake_capability():
    r = client.get("/v1/system/build-info")
    assert r.status_code == 200
    data = r.json()
    assert data["project"] == "ABC.01"
    assert data["readiness_claim"] == "ENGINEERING_SCAFFOLD_ONLY"
    assert len(data["agent_ids"]) == 10
    assert len(data["output_ids"]) == 17
    assert all(v is False for v in data["capabilities"].values())
    assert data["infrastructure"] == {
        "AUTH": "INTERFACE_ONLY",
        "PERSISTENCE": "INTERFACE_ONLY",
        "SECRETS": "INTERFACE_ONLY",
        "SALON_CONFIG": "INTERFACE_ONLY",
    }
