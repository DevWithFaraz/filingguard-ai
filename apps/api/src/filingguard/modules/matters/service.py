"""Business logic for saved legal matters."""

from uuid import UUID

from filingguard.db.repository import AnalysisRepository
from filingguard.modules.matters.schemas import (
    MatterAnalysisItem,
    MatterCreate,
    MatterDetail,
    MatterSummary,
)


class MatterConflict(ValueError):
    """Matter name collision for owner."""


def create_matter(
    repository: AnalysisRepository, owner_hash: str, payload: MatterCreate
) -> MatterSummary:
    try:
        matter = repository.create_matter(
            owner_hash=owner_hash,
            name=payload.name,
            case_number=payload.case_number,
            client_id=payload.client_id,
            description=payload.description,
        )
        return MatterSummary(
            id=matter.id,
            name=matter.name,
            case_number=matter.case_number,
            client_id=matter.client_id,
            description=matter.description,
            created_at=matter.created_at,
            updated_at=matter.updated_at,
        )
    except ValueError as error:
        raise MatterConflict(str(error)) from error


def list_matters(repository: AnalysisRepository, owner_hash: str) -> list[MatterSummary]:
    rows = repository.list_matters(owner_hash)
    return [
        MatterSummary(
            id=row.id,
            name=row.name,
            case_number=row.case_number,
            client_id=row.client_id,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


def get_matter(repository: AnalysisRepository, owner_hash: str, matter_id: UUID) -> MatterDetail:
    matter, analyses = repository.get_matter(owner_hash, matter_id)
    return MatterDetail(
        id=matter.id,
        name=matter.name,
        case_number=matter.case_number,
        client_id=matter.client_id,
        description=matter.description,
        created_at=matter.created_at,
        updated_at=matter.updated_at,
        analyses=[
            MatterAnalysisItem(
                analysis_id=a.id,
                document_name=a.document_name,
                mode=a.mode,
                status=a.status,
                created_at=a.created_at,
            )
            for a in analyses
        ],
    )


def assign_analysis_matter(
    repository: AnalysisRepository,
    owner_hash: str,
    analysis_id: UUID,
    matter_id: UUID | None,
) -> None:
    repository.assign_matter(owner_hash, analysis_id, matter_id)


def delete_matter(repository: AnalysisRepository, owner_hash: str, matter_id: UUID) -> None:
    repository.delete_matter(owner_hash, matter_id)
