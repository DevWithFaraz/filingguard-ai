import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from filingguard.integrations.storage import service
from filingguard.integrations.storage.managed import RecoverableTemporaryStorage
from filingguard.integrations.storage.service import StorageError, StoredPDFNotFound

PDF = Path(__file__).resolve().parents[4] / "data/demo/curated-v1/filing.pdf"


def test_managed_round_trip_and_shutdown_purge(tmp_path):
    root = tmp_path / "private"
    with RecoverableTemporaryStorage(root) as storage:
        file = storage.store(PDF.read_bytes())
        assert storage.read(file.file_id) == PDF.read_bytes()
        receipt = json.loads((root / f"{file.file_id}.json").read_text())
        assert receipt["file_id"] == file.file_id
        assert "document" not in receipt
    assert {path.name for path in root.iterdir()} == {".owner.json", ".lease"}
    storage.close()


def test_process_lease_rejects_concurrent_instance(tmp_path):
    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        with pytest.raises(StorageError):
            RecoverableTemporaryStorage(tmp_path / "private")
        file = storage.store(PDF.read_bytes())
        assert storage.read(file.file_id) == PDF.read_bytes()


def test_actual_abrupt_exit_recovers_registry_and_deletes_file(tmp_path):
    root = tmp_path / "private"
    code = (
        "import os, sys; from pathlib import Path; "
        "from filingguard.integrations.storage.managed import RecoverableTemporaryStorage; "
        "storage=RecoverableTemporaryStorage(Path(sys.argv[1])); "
        "storage.store(Path(sys.argv[2]).read_bytes()); os._exit(0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(root), str(PDF)], capture_output=True, timeout=30
    )
    assert result.returncode == 0
    file_id = next(root.glob("*.pdf")).stem
    with RecoverableTemporaryStorage(root) as storage:
        assert storage.read(file_id) == PDF.read_bytes()
        assert storage.delete(file_id)
        assert not storage.delete(file_id)
        assert not (root / f"{file_id}.json").exists()


def test_expired_receipt_does_not_extend_retention_on_restart(tmp_path, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(service.time, "time", lambda: now[0])
    root = tmp_path / "private"
    storage = RecoverableTemporaryStorage(root, retention_seconds=10)
    file = storage.store(PDF.read_bytes())
    storage.close(purge=False)
    now[0] = 1011.0
    with RecoverableTemporaryStorage(root, retention_seconds=10) as resumed:
        with pytest.raises(StoredPDFNotFound):
            resumed.read(file.file_id)
        assert not (root / f"{file.file_id}.pdf").exists()


def test_crash_leftovers_are_removed_only_inside_owned_flat_namespace(tmp_path):
    root = tmp_path / "private"
    storage = RecoverableTemporaryStorage(root)
    file = storage.store(PDF.read_bytes())
    storage.close(purge=False)
    (root / f"{file.file_id}.pdf").unlink()
    orphan = root / f"{uuid4()}.pdf"
    orphan.write_bytes(PDF.read_bytes())
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(PDF.read_bytes())
    with RecoverableTemporaryStorage(root):
        assert not orphan.exists()
        assert not (root / f"{file.file_id}.json").exists()
        assert outside.read_bytes() == PDF.read_bytes()


def test_unrecognized_existing_directory_is_never_claimed(tmp_path):
    root = tmp_path / "foreign"
    root.mkdir()
    foreign = root / "important.txt"
    foreign.write_text("Keep this")
    with pytest.raises(StorageError):
        RecoverableTemporaryStorage(root)
    assert foreign.read_text() == "Keep this"
    assert not (root / ".lease").exists()


@pytest.mark.parametrize("kind", ["receipt", "content", "foreign", "hardlink"])
def test_untrusted_restored_material_is_rejected_without_deletion(tmp_path, kind):
    root = tmp_path / "private"
    storage = RecoverableTemporaryStorage(root)
    file = storage.store(PDF.read_bytes())
    storage.close(purge=False)
    path = root / f"{file.file_id}.pdf"
    if kind == "receipt":
        (root / f"{file.file_id}.json").write_text('{"invalid":true}')
    elif kind == "content":
        data = path.read_bytes()
        path.write_bytes(b"x" + data[1:])
    elif kind == "foreign":
        (root / "foreign.txt").write_text("Keep this")
    else:
        os.link(path, tmp_path / "alias.pdf")
    with pytest.raises(StorageError):
        RecoverableTemporaryStorage(root)
    assert path.exists()


def test_failed_sidecar_deletion_can_be_retried_after_pdf_is_gone(tmp_path, monkeypatch):
    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        file = storage.store(PDF.read_bytes())
        original = Path.unlink
        blocked = [True]

        def unlink(path, *args, **kwargs):
            if path.name == f"{file.file_id}.json" and blocked[0]:
                raise OSError("Synthetic disk error")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", unlink)
        with pytest.raises(StorageError):
            storage.delete(file.file_id)
        assert file.file_id in storage._entries
        blocked[0] = False
        assert storage.delete(file.file_id)
        assert not storage._entries


@pytest.mark.parametrize("operation", ["expiry", "shutdown"])
def test_one_failed_file_does_not_block_other_cleanup(tmp_path, monkeypatch, operation):
    root = tmp_path / "private"
    storage = RecoverableTemporaryStorage(root)
    first = storage.store(PDF.read_bytes())
    second = storage.store(PDF.read_bytes())
    original = storage.delete

    def fail_first(file_id):
        if file_id == first.file_id:
            raise StorageError()
        return original(file_id)

    monkeypatch.setattr(storage, "delete", fail_first)
    if operation == "expiry":
        monkeypatch.setattr(service.time, "monotonic", lambda: float("inf"))
        cleanup = storage.cleanup_expired
    else:
        cleanup = storage.close
    with pytest.raises(StorageError):
        cleanup()
    assert (root / f"{first.file_id}.pdf").exists()
    assert not (root / f"{second.file_id}.pdf").exists()
    monkeypatch.setattr(storage, "delete", original)
    storage.close()
    with RecoverableTemporaryStorage(root):
        pass
    assert not list(root.glob("*.pdf"))


def test_registry_capacity_is_enforced_before_file_write(tmp_path, monkeypatch):
    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        with monkeypatch.context() as patch:
            patch.setattr(storage, "_entries", {str(uuid4()): None for _ in range(1000)})
            with pytest.raises(StorageError):
                storage.store(PDF.read_bytes())
        assert not list(storage._root.glob("*.pdf"))
