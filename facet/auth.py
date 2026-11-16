"""HTTP Basic authentication for the CET API.

Test users are read from the CET_API_USERS environment variable (or from a
local .env file) as a JSON object of username to password, for example:

    CET_API_USERS='{"alice": "pw1", "bob": "pw2"}'

If CET_API_USERS is not set, no one can log in.
"""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CET_", env_file=".env", extra="ignore"
    )

    api_users: dict[str, str] = {}


settings = AuthSettings()
security = HTTPBasic()


def require_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    """Return the username if the request's Basic credentials are valid, else 401."""
    expected = settings.api_users.get(credentials.username)
    password_ok = expected is not None and secrets.compare_digest(
        credentials.password.encode(), expected.encode()
    )
    if not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
