"""Registration, login and profile endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_returns_token_and_profile(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "anna@example.com",
            "password": "SuperSecret123",
            "full_name": "Anna Nowak",
            "age": 29,
            "country": "de",
            "city": "  Munich ",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0
    user = body["user"]
    assert user["email"] == "anna@example.com"
    assert user["full_name"] == "Anna Nowak"
    # country is normalised to upper case, city whitespace collapsed
    assert user["country"] == "DE"
    assert user["city"] == "Munich"
    assert user["id"] > 0
    assert "password" not in user
    assert "hashed_password" not in user


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "SuperSecret123",
        "full_name": "Jan Kowalski",
        "age": 40,
        "country": "PL",
        "city": "Gdansk",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    payload["email"] = "DUP@example.com"  # uniqueness is case-insensitive
    second = client.post("/api/v1/auth/register", json=payload)

    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


def test_register_rejects_underage_driver(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "kid@example.com",
            "password": "SuperSecret123",
            "full_name": "Too Young",
            "age": 17,
            "country": "PL",
            "city": "Krakow",
        },
    )
    assert response.status_code == 422


def test_register_rejects_unsupported_country(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "far@example.com",
            "password": "SuperSecret123",
            "full_name": "Far Away",
            "age": 30,
            "country": "US",
            "city": "Austin",
        },
    )
    assert response.status_code == 422
    assert "unsupported country code" in response.text


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",
            "full_name": "Weak Pass",
            "age": 30,
            "country": "PL",
            "city": "Lodz",
        },
    )
    assert response.status_code == 422


def test_login_success(client: TestClient, driver: dict) -> None:
    response = client.post("/api/v1/auth/login", json=driver["credentials"])

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == driver["user"]["email"]


def test_login_rejects_wrong_password(client: TestClient, driver: dict) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": driver["credentials"]["email"], "password": "WrongPassword1"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": "ghost@example.com", "password": "SuperSecret123"}
    )
    assert response.status_code == 401
    # identical message to the wrong-password case: no account enumeration
    assert response.json()["detail"] == "Incorrect email or password"


def test_me_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/users/me").status_code == 401


def test_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_me_returns_current_profile(client: TestClient, driver: dict) -> None:
    response = client.get("/api/v1/users/me", headers=driver["headers"])

    assert response.status_code == 200
    assert response.json()["email"] == "driver@example.com"
    assert response.json()["country"] == "PL"


def test_update_profile(client: TestClient, driver: dict) -> None:
    response = client.patch(
        "/api/v1/users/me",
        headers=driver["headers"],
        json={"full_name": "Jan Maria Kowalski", "age": 35, "city": "Poznan", "country": "cz"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["full_name"] == "Jan Maria Kowalski"
    assert body["age"] == 35
    assert body["city"] == "Poznan"
    assert body["country"] == "CZ"

    # partial update leaves other fields alone
    client.patch("/api/v1/users/me", headers=driver["headers"], json={"age": 36})
    refreshed = client.get("/api/v1/users/me", headers=driver["headers"]).json()
    assert refreshed["age"] == 36
    assert refreshed["full_name"] == "Jan Maria Kowalski"


def test_update_profile_rejects_bad_age(client: TestClient, driver: dict) -> None:
    response = client.patch("/api/v1/users/me", headers=driver["headers"], json={"age": 150})
    assert response.status_code == 422
