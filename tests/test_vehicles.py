"""Vehicle profile CRUD and ownership rules."""

from __future__ import annotations

from fastapi.testclient import TestClient

VEHICLE = {
    "label": "MAN TGX",
    "plate": "wgm 12345",
    "vehicle_type": "articulated_truck",
    "body_type": "curtain_side",
    "payload_kg": 24000,
    "volume_m3": 92.5,
    "max_range_km": 1200,
    "length_m": 16.5,
    "width_m": 2.55,
    "height_m": 4.0,
    "cargo_length_m": 13.6,
    "cargo_width_m": 2.45,
    "cargo_height_m": 2.7,
}


def test_create_vehicle_normalises_plate(client: TestClient, driver: dict) -> None:
    response = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["plate"] == "WGM 12345"
    assert body["payload_kg"] == 24000
    assert body["vehicle_type"] == "articulated_truck"
    assert body["owner_id"] == driver["user"]["id"]


def test_list_starts_empty(client: TestClient, driver: dict) -> None:
    response = client.get("/api/v1/vehicles", headers=driver["headers"])

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_list_returns_created_vehicles(client: TestClient, driver: dict) -> None:
    client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE)
    client.post(
        "/api/v1/vehicles",
        headers=driver["headers"],
        json={**VEHICLE, "plate": "GD 999", "label": "Ford Transit", "vehicle_type": "van",
              "payload_kg": 1200},
    )

    response = client.get("/api/v1/vehicles", headers=driver["headers"])

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["label"] for item in body["items"]] == ["MAN TGX", "Ford Transit"]


def test_get_single_vehicle(client: TestClient, driver: dict) -> None:
    created = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).json()

    response = client.get(f"/api/v1/vehicles/{created['id']}", headers=driver["headers"])

    assert response.status_code == 200
    assert response.json()["plate"] == "WGM 12345"


def test_update_vehicle_partially(client: TestClient, driver: dict) -> None:
    created = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).json()

    response = client.patch(
        f"/api/v1/vehicles/{created['id']}",
        headers=driver["headers"],
        json={"payload_kg": 25000, "body_type": "refrigerated"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["payload_kg"] == 25000
    assert body["body_type"] == "refrigerated"
    assert body["label"] == "MAN TGX"  # untouched


def test_delete_vehicle(client: TestClient, driver: dict) -> None:
    created = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).json()

    assert client.delete(f"/api/v1/vehicles/{created['id']}", headers=driver["headers"]).status_code == 204
    assert client.get(f"/api/v1/vehicles/{created['id']}", headers=driver["headers"]).status_code == 404
    assert client.get("/api/v1/vehicles", headers=driver["headers"]).json()["total"] == 0


def test_duplicate_plate_for_same_owner_conflicts(client: TestClient, driver: dict) -> None:
    assert client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).status_code == 201

    second = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE)

    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


def test_same_plate_allowed_for_different_owners(
    client: TestClient, register
) -> None:
    first = register(email="one@example.com")
    second = register(email="two@example.com")

    assert client.post("/api/v1/vehicles", headers=first["headers"], json=VEHICLE).status_code == 201
    assert client.post("/api/v1/vehicles", headers=second["headers"], json=VEHICLE).status_code == 201


def test_other_users_vehicle_is_invisible(client: TestClient, register) -> None:
    owner = register(email="owner@example.com")
    stranger = register(email="stranger@example.com")
    created = client.post("/api/v1/vehicles", headers=owner["headers"], json=VEHICLE).json()

    assert client.get(f"/api/v1/vehicles/{created['id']}", headers=stranger["headers"]).status_code == 404
    assert client.get("/api/v1/vehicles", headers=stranger["headers"]).json()["total"] == 0
    assert client.delete(f"/api/v1/vehicles/{created['id']}", headers=stranger["headers"]).status_code == 404


def test_vehicle_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/vehicles").status_code == 401
    assert client.post("/api/v1/vehicles", json=VEHICLE).status_code == 401


def test_create_vehicle_rejects_invalid_payload(client: TestClient, driver: dict) -> None:
    response = client.post(
        "/api/v1/vehicles",
        headers=driver["headers"],
        json={**VEHICLE, "payload_kg": 0},
    )
    assert response.status_code == 422


def test_create_vehicle_rejects_unknown_type(client: TestClient, driver: dict) -> None:
    response = client.post(
        "/api/v1/vehicles",
        headers=driver["headers"],
        json={**VEHICLE, "vehicle_type": "spaceship"},
    )
    assert response.status_code == 422


def test_reference_countries_available(client: TestClient) -> None:
    response = client.get("/api/v1/reference/countries")

    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert {"PL", "DE", "FR", "NO"} <= codes
    assert "US" not in codes
