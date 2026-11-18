"""Tests for HTTP Basic authentication on the CET API.

Run from facet/:  venv/bin/pytest
"""

import auth
import pytest
from fastapi.testclient import TestClient
from main import app

TEST_USERS = {"test-user": "test-password"}
ENDPOINT = "/25.1/test_version"


@pytest.fixture
def client(monkeypatch):
    # Use a fixed user list so the tests don't depend on .env or CET_API_USERS.
    monkeypatch.setattr(auth.settings, "api_users", TEST_USERS)
    return TestClient(app)


def test_valid_credentials_return_200(client):
    response = client.get(ENDPOINT, auth=("test-user", "test-password"))

    assert response.status_code == 200
    assert response.json() == {"message": "25.1"}


def test_no_credentials_return_401(client):
    response = client.get(ENDPOINT)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Basic"


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("test-user", "wrong-password"),
        ("unknown-user", "test-password"),
        ("", ""),
    ],
    ids=["wrong-password", "unknown-user", "empty"],
)
def test_bad_credentials_return_401(client, username, password):
    response = client.get(ENDPOINT, auth=(username, password))

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Basic"
