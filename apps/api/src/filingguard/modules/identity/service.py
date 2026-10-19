import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from filingguard.db.repository import AnalysisRepository
from filingguard.modules.identity.hashing import DUMMY_SECRET_HASH, hash_secret, verify_secret
from filingguard.modules.identity.schemas import IdentityClaimed, IdentitySessionIssued


class IdentityClaimConflict(ValueError):
    """Username taken or owner_hash already bound."""


class IdentityLoginFailed(LookupError):
    """Missing identity and wrong secret are indistinguishable."""


def claim_owner(repository: AnalysisRepository, owner_hash: str, username: str, secret: str):
    existing = repository.get_local_identity_by_owner(owner_hash)
    if existing is not None:
        if existing.username == username and verify_secret(secret, existing.secret_hash):
            return IdentityClaimed(username=existing.username)
        raise IdentityClaimConflict("Identity already claimed")
    if repository.get_local_identity_by_username(username) is not None:
        raise IdentityClaimConflict("Identity already claimed")
    try:
        row = repository.add_local_identity(owner_hash, username, hash_secret(secret))
    except ValueError as error:
        raise IdentityClaimConflict("Identity already claimed") from error
    return IdentityClaimed(username=row.username)


def login_owner(repository: AnalysisRepository, username: str, secret: str):
    identity = repository.get_local_identity_by_username(username)
    if identity is None:
        verify_secret(secret, DUMMY_SECRET_HASH)
        raise IdentityLoginFailed("Identity unavailable")
    if not verify_secret(secret, identity.secret_hash):
        raise IdentityLoginFailed("Identity unavailable")
    token = secrets.token_urlsafe(32)
    expiry = datetime.now(UTC) + timedelta(minutes=55)
    repository.issue_identity_session(
        sha256(token.encode()).hexdigest(), identity.owner_hash, expiry
    )
    return IdentitySessionIssued(token=token, expires_at=expiry, username=identity.username)


def current_identity(repository: AnalysisRepository, owner_hash: str):
    row = repository.get_local_identity_by_owner(owner_hash)
    if row is None:
        raise IdentityLoginFailed("Identity unavailable")
    return IdentityClaimed(username=row.username)


def migrate_owner_analyses(
    repository: AnalysisRepository,
    from_owner_hash: str,
    username: str,
    secret: str,
):
    session = login_owner(repository, username, secret)
    identity = repository.get_local_identity_by_username(username)
    if identity is None:
        raise IdentityLoginFailed("Identity unavailable")
    count = repository.migrate_owner(from_owner_hash, identity.owner_hash)
    return count, session

