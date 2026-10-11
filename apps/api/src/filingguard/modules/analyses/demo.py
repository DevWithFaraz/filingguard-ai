"""Fail-closed fixture admission; never a fallback for a failed live request."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


class DemoUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class DemoFixture:
    fixture_id: str
    document: str
    authority: str
    document_sha256: str
    source_sha256: str
    provenance: str

    def matches(self, text: str) -> bool:
        return hashlib.sha256(text.encode("utf-8")).hexdigest() == self.document_sha256


def _private_fixture_file(root: Path, value: str) -> Path:
    if not isinstance(value, str):
        raise DemoUnavailable("Fixture manifest is invalid")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise DemoUnavailable("Fixture path is invalid")
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise DemoUnavailable("Fixture path is invalid")
    if not path.is_file() or path.stat().st_size > 2_000_000:
        raise DemoUnavailable("Fixture material is unavailable")
    return path


def load_demo(
    root: Path, fixture_id: str, *, mode: str, input_text: str | None = None
) -> DemoFixture:
    """Root is a server-configured resource path, never a user-controlled pathname."""
    if mode != "demo":
        raise DemoUnavailable("Demo fixtures require explicit demo mode")
    try:
        manifest = json.loads(_private_fixture_file(root, "manifest.json").read_text("utf-8"))
        if not isinstance(manifest, dict) or manifest.get("fixture_id") != fixture_id:
            raise DemoUnavailable("Unknown demo fixture")
        if manifest.get("validation_status") != "human_reviewed":
            raise DemoUnavailable("Demo fixture awaits human review")
        if manifest.get("mode") not in {"synthetic", "cached_public"}:
            raise DemoUnavailable("Fixture provenance is invalid")
        document = _private_fixture_file(root, manifest["filing_path"]).read_text("utf-8")
        authority = _private_fixture_file(root, manifest["authority_path"]).read_text("utf-8")
        document_hash = hashlib.sha256(document.encode("utf-8")).hexdigest()
        source_hash = hashlib.sha256(authority.encode("utf-8")).hexdigest()
        if document_hash != manifest.get("document_sha256") or source_hash != manifest.get(
            "source_sha256"
        ):
            raise DemoUnavailable("Demo fixture integrity check failed")
        fixture = DemoFixture(
            fixture_id, document, authority, document_hash, source_hash, manifest["mode"]
        )
        if input_text is not None and not fixture.matches(input_text):
            raise DemoUnavailable("Input does not match the selected demo")
        return fixture
    except DemoUnavailable:
        raise
    except (OSError, ValueError, KeyError, TypeError) as from_error:
        raise DemoUnavailable("Demo fixture is unavailable") from from_error
