import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app, get_repository
from app.repository import IncidentRepository

SAMPLE = pd.DataFrame(
    [
        {"id": 1, "timestamp": "2024-03-04 07:15", "locality": "Kennedy", "severity": "injured", "vehicle_type": "motorcycle"},
        {"id": 2, "timestamp": "2024-03-04 07:40", "locality": "Kennedy", "severity": "property_damage", "vehicle_type": "car"},
        {"id": 3, "timestamp": "2024-03-09 18:05", "locality": "Suba", "severity": "fatal", "vehicle_type": "pedestrian"},
        {"id": 4, "timestamp": "2025-01-10 07:30", "locality": "Chapinero", "severity": "property_damage", "vehicle_type": "car"},
    ]
)


@pytest.fixture
def client():
    app.dependency_overrides[get_repository] = lambda: IncidentRepository(SAMPLE)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_list_incidents_newest_first_with_pagination(client):
    body = client.get("/incidents", params={"limit": 2}).json()
    assert body["total"] == 4
    assert [i["id"] for i in body["items"]] == [4, 3]


def test_filter_by_locality_is_case_insensitive(client):
    body = client.get("/incidents", params={"locality": "kennedy"}).json()
    assert body["total"] == 2


def test_filter_by_year_and_severity(client):
    body = client.get("/incidents", params={"year": 2024, "severity": "fatal"}).json()
    assert [i["id"] for i in body["items"]] == [3]


def test_invalid_severity_returns_422(client):
    assert client.get("/incidents", params={"severity": "minor"}).status_code == 422


def test_get_incident_and_404(client):
    assert client.get("/incidents/3").json()["locality"] == "Suba"
    assert client.get("/incidents/999").status_code == 404


def test_summary(client):
    body = client.get("/stats/summary").json()
    assert body["total"] == 4
    assert body["by_severity"]["property_damage"] == 2
    assert body["fatality_rate_pct"] == 25.0
    assert body["busiest_hour"] == 7


def test_group_by_hour_returns_all_24_hours(client):
    body = client.get("/stats/group", params={"by": "hour"}).json()
    assert len(body) == 24
    assert body[7] == {"key": 7, "count": 3}


def test_group_by_locality(client):
    body = client.get("/stats/group", params={"by": "locality"}).json()
    assert body[0] == {"key": "Kennedy", "count": 2}


def test_repository_rejects_missing_columns():
    with pytest.raises(ValueError):
        IncidentRepository(pd.DataFrame({"id": [1]}))
