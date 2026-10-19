from datetime import datetime
from typing import Annotated

from pydantic import Field, field_validator

from filingguard.modules.analyses.schemas import Contract

USERNAME_PATTERN = r"^[a-z][a-z0-9_]{2,31}$"


class IdentityCredentials(Contract):
    username: Annotated[str, Field(min_length=3, max_length=32, pattern=USERNAME_PATTERN)]
    secret: Annotated[str, Field(min_length=12, max_length=128)]

    @field_validator("username", mode="before")
    @classmethod
    def lowercase_username(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

    @field_validator("secret")
    @classmethod
    def reject_blank_secret(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Secret cannot be blank or padded")
        return value


class IdentityClaimRequest(IdentityCredentials):
    pass


class IdentityLoginRequest(IdentityCredentials):
    pass


class IdentityClaimed(Contract):
    username: str
    bound: bool = True


class IdentitySessionIssued(Contract):
    token: str
    expires_at: datetime
    username: str
