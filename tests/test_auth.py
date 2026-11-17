"""Registration, login and profile endpoints."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.core.dates import years_since


def birth_date_years_ago(years: int) -> str:
    """ISO date of birth exactly `years` years ago, safe around 29 February."""
    today = date.today()
    try:
        return today.replace(year=today.year - years).isoformat()
    except ValueError:
        return today.replace(year=today.year - years, day=28).isoformat()


def test_register_returns_token_and_profile(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "anna@example.com",
            "password": "SuperSecret123",
            "full_name": "Anna Nowak",
            "date_of_birth": "1996-03-15",
            "country": "de",
            "company_country": "PL",
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
    assert user["company_country"] == "PL"
    assert user["city"] == "Munich"
    assert user["date_of_birth"] == "1996-03-15"
    # age is derived from the stored date, never sent by the client
    assert user["age"] == years_since(date(1996, 3, 15))
    assert user["id"] > 0
    assert "password" not in user
    assert "hashed_password" not in user


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "SuperSecret123",
        "full_name": "Jan Kowalski",
        "date_of_birth": "1986-07-01",
        "country": "PL",
        "company_country": "PL",
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
            "date_of_birth": birth_date_years_ago(17),
            "country": "PL",
            "company_country": "PL",
            "city": "Krakow",
        },
    )
    assert response.status_code == 422
    assert "at least 18" in response.text


def test_register_rejects_future_date_of_birth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "future@example.com",
            "password": "SuperSecret123",
            "full_name": "Not Born Yet",
            "date_of_birth": (date.today() + timedelta(days=1)).isoformat(),
            "country": "PL",
            "company_country": "PL",
            "city": "Krakow",
        },
    )
    assert response.status_code == 422
    assert "future" in response.text


def test_register_rejects_unsupported_country(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "far@example.com",
            "password": "SuperSecret123",
            "full_name": "Far Away",
            "date_of_birth": "1990-02-02",
            "country": "US",
            "company_country": "PL",
            "city": "Austin",
        },
    )
    assert response.status_code == 422
    assert "unsupported country code" in response.text


def test_register_rejects_unsupported_company_country(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "offshore@example.com",
            "password": "SuperSecret123",
            "full_name": "Off Shore",
            "date_of_birth": "1990-02-02",
            "country": "PL",
            "company_country": "PA",
            "city": "Warsaw",
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
            "date_of_birth": "1990-02-02",
            "country": "PL",
            "company_country": "PL",
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
    assert response.json()["date_of_birth"] == "1985-04-12"


def test_update_profile(client: TestClient, driver: dict) -> None:
    new_birth_date = birth_date_years_ago(40)

    response = client.patch(
        "/api/v1/users/me",
        headers=driver["headers"],
        json={
            "full_name": "Jan Maria Kowalski",
            "date_of_birth": new_birth_date,
            "city": "Poznan",
            "country": "cz",
            "company_country": "sk",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["full_name"] == "Jan Maria Kowalski"
    assert body["date_of_birth"] == new_birth_date
    assert body["age"] == 40
    assert body["city"] == "Poznan"
    assert body["country"] == "CZ"
    assert body["company_country"] == "SK"

    # partial update leaves other fields alone
    client.patch("/api/v1/users/me", headers=driver["headers"], json={"city": "Gdynia"})
    refreshed = client.get("/api/v1/users/me", headers=driver["headers"]).json()
    assert refreshed["city"] == "Gdynia"
    assert refreshed["full_name"] == "Jan Maria Kowalski"
    assert refreshed["date_of_birth"] == new_birth_date


def test_update_profile_rejects_underage_date_of_birth(client: TestClient, driver: dict) -> None:
    response = client.patch(
        "/api/v1/users/me",
        headers=driver["headers"],
        json={"date_of_birth": birth_date_years_ago(12)},
    )
    assert response.status_code == 422
    assert "at least 18" in response.text
