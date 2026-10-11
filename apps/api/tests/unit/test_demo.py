import hashlib
import json
from pathlib import Path

import pytest

from filingguard.modules.analyses.demo import DemoUnavailable, load_demo


@pytest.fixture
def fixture_root(tmp_path):
    document, authority = "Fictional motion", "Fictional source"
    (tmp_path / "filing.txt").write_text(document, encoding="utf-8")
    (tmp_path / "source.txt").write_text(authority, encoding="utf-8")
    manifest = {
        "fixture_id": "test-only",
        "mode": "synthetic",
        "validation_status": "human_reviewed",
        "filing_path": "filing.txt",
        "authority_path": "source.txt",
        "document_sha256": hashlib.sha256(document.encode()).hexdigest(),
        "source_sha256": hashlib.sha256(authority.encode()).hexdigest(),
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def test_recognized_fixture_with_explicit_mode(fixture_root):
    fixture = load_demo(fixture_root, "test-only", mode="demo", input_text="Fictional motion")
    assert fixture.provenance == "synthetic"
    assert fixture.matches("Fictional motion")
    assert not fixture.matches("Fictional motion changed")


@pytest.mark.parametrize("mode", ["live", "synthetic", "", None])
def test_live_never_admits_fixture(fixture_root, mode):
    with pytest.raises(DemoUnavailable):
        load_demo(fixture_root, "test-only", mode=mode)


def test_unrecognized_input_and_id_rejected(fixture_root):
    with pytest.raises(DemoUnavailable):
        load_demo(fixture_root, "test-only", mode="demo", input_text="Different filing")
    with pytest.raises(DemoUnavailable):
        load_demo(fixture_root, "../../secret", mode="demo")


def test_changed_material_rejected(fixture_root):
    (fixture_root / "source.txt").write_text("Changed source", encoding="utf-8")
    with pytest.raises(DemoUnavailable, match="integrity"):
        load_demo(fixture_root, "test-only", mode="demo")


@pytest.mark.parametrize(
    "patch",
    [
        {"source_sha256": None},
        {"validation_status": "not_run"},
        {"mode": "live"},
        {"filing_path": "../outside.txt"},
        {"filing_path": "C:/outside.txt"},
        {"filing_path": None},
    ],
)
def test_invalid_manifest_rejected(fixture_root, patch):
    path = fixture_root / "manifest.json"
    manifest = json.loads(path.read_text("utf-8"))
    manifest.update(patch)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DemoUnavailable):
        load_demo(fixture_root, "test-only", mode="demo")


def test_current_project_starter_stays_disabled():
    root = Path(__file__).resolve().parents[4] / "data" / "demo"
    with pytest.raises(DemoUnavailable, match="human review"):
        load_demo(root, "synthetic-starter-v1", mode="demo")
