"""API route tests."""

from fastapi.testclient import TestClient

from src.api import routes
from src.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_healthz_returns_healthy():
    response = _client().get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readyz_returns_not_ready_when_graph_unset():
    routes.set_claims_graph(None)
    response = _client().get("/readyz")
    assert response.status_code == 503


def test_explain_requires_api_key(test_app, sample_claim_question):
    response = test_app.post("/v1/claims/explain", json=sample_claim_question)
    assert response.status_code in (401, 422)


def test_explain_happy_path(test_app, api_headers, sample_claim_question):
    response = test_app.post(
        "/v1/claims/explain",
        headers=api_headers,
        json=sample_claim_question,
    )
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["explanation"]["claim_id"] == "C-50012"
    assert body["explanation"]["member_id"] == "M10023"
    assert len(body["explanation"]["next_steps"]) >= 1


def test_explain_rejects_invalid_api_key(test_app, sample_claim_question):
    response = test_app.post(
        "/v1/claims/explain",
        headers={"X-API-Key": "bad-key", "Content-Type": "application/json"},
        json=sample_claim_question,
    )
    assert response.status_code == 401
