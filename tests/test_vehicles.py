"""Vehicle profile CRUD, catalogue validation and ownership rules."""

from __future__ import annotations

from fastapi.testclient import TestClient

VEHICLE = {
    "make": "man",
    "model": "tgx",
    "modification": "18.440",
    "model_year": 2021,
    "vin": "WMA06XZZ0LM123456",
    "plate": "wgm 12345",
    "registration_country": "pl",
    "vehicle_type": "articulated_truck",
    "body_type": "curtain_side",
    "payload_kg": 24000,
    "volume_m3": 92.5,
    "max_range_km": 1200,
    "cargo_shape": "box",
    "cargo_length_m": 13.6,
    "cargo_width_m": 2.45,
    "cargo_height_m": 2.7,
}


def test_create_vehicle_normalises_input(client: TestClient, driver: dict) -> None:
    response = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["plate"] == "WGM 12345"
    assert body["registration_country"] == "PL"
    assert body["vin"] == "WMA06XZZ0LM123456"
    assert body["payload_kg"] == 24000
    assert body["vehicle_type"] == "articulated_truck"
    assert body["owner_id"] == driver["user"]["id"]


def test_read_resolves_catalog_names(client: TestClient, driver: dict) -> None:
    body = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).json()

    assert body["make_name"] == "MAN"
    assert body["model_name"] == "TGX"
    assert body["display_name"] == "MAN TGX 18.440, 2021"


def test_display_name_without_modification(client: TestClient, driver: dict) -> None:
    payload = {**VEHICLE, "modification": None, "make": "fiat", "model": "doblo",
               "vehicle_type": "van", "model_year": 2019}
    body = client.post("/api/v1/vehicles", headers=driver["headers"], json=payload).json()

    assert body["display_name"] == "Fiat Doblò, 2019"


def test_list_starts_empty(client: TestClient, driver: dict) -> None:
    response = client.get("/api/v1/vehicles", headers=driver["headers"])

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_list_returns_created_vehicles(client: TestClient, driver: dict) -> None:
    client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE)
    client.post(
        "/api/v1/vehicles",
        headers=driver["headers"],
        json={
            **VEHICLE,
            "plate": "GD 999",
            "vin": None,
            "make": "ford",
            "model": "transit",
            "modification": "Custom",
            "model_year": 2018,
            "vehicle_type": "van",
            "payload_kg": 1200,
        },
    )

    response = client.get("/api/v1/vehicles", headers=driver["headers"])

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["display_name"] for item in body["items"]] == [
        "MAN TGX 18.440, 2021",
        "Ford Transit Custom, 2018",
    ]


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
    assert body["model"] == "tgx"  # untouched


def test_update_vehicle_can_move_it_to_another_catalog_model(
    client: TestClient, driver: dict
) -> None:
    created = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).json()

    response = client.patch(
        f"/api/v1/vehicles/{created['id']}",
        headers=driver["headers"],
        json={"model": "tgs", "model_year": 2015},
    )

    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == "MAN TGS 18.440, 2015"


def test_update_vehicle_rejects_model_of_another_make(client: TestClient, driver: dict) -> None:
    created = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).json()

    response = client.patch(
        f"/api/v1/vehicles/{created['id']}",
        headers=driver["headers"],
        json={"make": "scania"},  # model stays "tgx", which Scania does not have
    )

    assert response.status_code == 422


def test_delete_vehicle(client: TestClient, driver: dict) -> None:
    created = client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).json()

    assert (
        client.delete(f"/api/v1/vehicles/{created['id']}", headers=driver["headers"]).status_code
        == 204
    )
    assert (
        client.get(f"/api/v1/vehicles/{created['id']}", headers=driver["headers"]).status_code
        == 404
    )
    assert client.get("/api/v1/vehicles", headers=driver["headers"]).json()["total"] == 0


def test_duplicate_plate_for_same_owner_conflicts(client: TestClient, driver: dict) -> None:
    assert client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).status_code == 201

    second = client.post(
        "/api/v1/vehicles", headers=driver["headers"], json={**VEHICLE, "vin": None}
    )

    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]
    assert "plate" in second.json()["detail"]


def test_duplicate_vin_for_same_owner_conflicts(client: TestClient, driver: dict) -> None:
    assert client.post("/api/v1/vehicles", headers=driver["headers"], json=VEHICLE).status_code == 201

    second = client.post(
        "/api/v1/vehicles", headers=driver["headers"], json={**VEHICLE, "plate": "GD 111"}
    )

    assert second.status_code == 409
    assert "VIN" in second.json()["detail"]


def test_same_plate_allowed_for_different_owners(client: TestClient, register) -> None:
    first = register(email="one@example.com")
    second = register(email="two@example.com")

    assert client.post("/api/v1/vehicles", headers=first["headers"], json=VEHICLE).status_code == 201
    assert client.post("/api/v1/vehicles", headers=second["headers"], json=VEHICLE).status_code == 201


def test_other_users_vehicle_is_invisible(client: TestClient, register) -> None:
    owner = register(email="owner@example.com")
    stranger = register(email="stranger@example.com")
    created = client.post("/api/v1/vehicles", headers=owner["headers"], json=VEHICLE).json()

    assert (
        client.get(f"/api/v1/vehicles/{created['id']}", headers=stranger["headers"]).status_code
        == 404
    )
    assert client.get("/api/v1/vehicles", headers=stranger["headers"]).json()["total"] == 0
    assert (
        client.delete(f"/api/v1/vehicles/{created['id']}", headers=stranger["headers"]).status_code
        == 404
    )


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


def test_create_vehicle_rejects_unknown_make(client: TestClient, driver: dict) -> None:
    response = client.post(
        "/api/v1/vehicles",
        headers=driver["headers"],
        json={**VEHICLE, "make": "logisistance"},
    )
    assert response.status_code == 422


def test_create_vehicle_rejects_model_of_another_make(client: TestClient, driver: dict) -> None:
    response = client.post(
        "/api/v1/vehicles",
        headers=driver["headers"],
        json={**VEHICLE, "make": "daf"},
    )
    assert response.status_code == 422


def test_create_vehicle_rejects_broken_vin(client: TestClient, driver: dict) -> None:
    for vin in ("WMA06XZZ0LM12345", "WMA06XZZ0LM12345I", "WMA06XZZ0LM12345O"):
        response = client.post(
            "/api/v1/vehicles", headers=driver["headers"], json={**VEHICLE, "vin": vin}
        )
        assert response.status_code == 422, vin


def test_create_vehicle_rejects_non_latin_text(client: TestClient, driver: dict) -> None:
    for field, value in (("modification", "Тягач"), ("plate", "А123ВС77")):
        response = client.post(
            "/api/v1/vehicles", headers=driver["headers"], json={**VEHICLE, field: value}
        )
        assert response.status_code == 422, field


def test_create_vehicle_rejects_unsupported_country(client: TestClient, driver: dict) -> None:
    response = client.post(
        "/api/v1/vehicles",
        headers=driver["headers"],
        json={**VEHICLE, "registration_country": "US"},
    )
    assert response.status_code == 422


def test_create_vehicle_rejects_out_of_range_year(client: TestClient, driver: dict) -> None:
    for year in (1979, 2100):
        response = client.post(
            "/api/v1/vehicles", headers=driver["headers"], json={**VEHICLE, "model_year": year}
        )
        assert response.status_code == 422, year


def test_reference_countries_available(client: TestClient) -> None:
    response = client.get("/api/v1/reference/countries")

    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert {"PL", "DE", "FR", "NO"} <= codes
    assert "US" not in codes


def test_reference_vehicle_catalog_available(client: TestClient) -> None:
    response = client.get("/api/v1/reference/vehicle-catalog")

    assert response.status_code == 200
    body = response.json()
    assert "VehiclesDB" in body["source"]  # the CC BY attribution travels with the data
    assert len(body["makes"]) > 150

    makes = {make["code"]: make for make in body["makes"]}
    assert makes["man"]["core"] is True
    assert {"tgx", "tgs", "tgl", "tgm"} <= {model["code"] for model in makes["man"]["models"]}
    # Non-core makes stay available, otherwise a driver of an unusual truck cannot register it.
    assert makes["man"]["name"] == "MAN"
    assert any(make["core"] is False for make in body["makes"])


def test_reference_vehicle_options_include_cargo_shapes(client: TestClient) -> None:
    body = client.get("/api/v1/reference/vehicle-options").json()

    assert {item["value"] for item in body["cargo_shapes"]} == {"box", "irregular"}
