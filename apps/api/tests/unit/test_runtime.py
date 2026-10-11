import asyncio
import logging
from types import SimpleNamespace

import pytest

from filingguard.core.config import Settings
from filingguard.core.runtime import AnalysisRuntime, application_lifespan, run_cleanup
from filingguard.integrations.storage.managed import RecoverableTemporaryStorage
from filingguard.integrations.storage.service import PrivateTemporaryStorage, StorageError
from filingguard.main import create_app


def test_shell_lifecycle_owns_storage_and_does_not_connect_to_database(client, monkeypatch):
    runtime = client.app.state.analysis_runtime
    assert runtime.lifecycle is None
    assert client.get("/api/v1/health").status_code == 200
    with pytest.raises(ValueError, match="configured"):
        runtime.get_lifecycle()


@pytest.mark.asyncio
async def test_lifespan_closes_temporary_files_and_waits_for_sweeper():
    app = create_app()
    context = application_lifespan(Settings())(app)
    async with context:
        root = app.state.analysis_runtime.storage._root
        assert root.is_dir()
    assert not root.exists()


@pytest.mark.asyncio
async def test_configured_recoverable_root_is_owned_and_released_on_database_failure(
    tmp_path, monkeypatch
):
    def unavailable():
        raise RuntimeError("Synthetic database outage")

    monkeypatch.setattr("filingguard.core.runtime.create_db_engine", unavailable)
    app = create_app()
    settings = Settings(private_storage_directory=tmp_path / "private")
    async with application_lifespan(settings)(app):
        runtime = app.state.analysis_runtime
        assert isinstance(runtime.storage, RecoverableTemporaryStorage)
        assert runtime.lifecycle is None
    with RecoverableTemporaryStorage(tmp_path / "private"):
        pass


def test_managed_sweeper_initializes_lifecycle_without_new_intake(tmp_path, monkeypatch):
    calls = []

    class Lifecycle:
        def cleanup(self):
            calls.append("cleanup")
            return SimpleNamespace(failures=0)

    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        runtime = AnalysisRuntime(storage)
        monkeypatch.setattr(runtime, "get_lifecycle", lambda: Lifecycle())
        runtime.sweep()
        assert calls == ["cleanup"]
        assert not runtime.cleanup_failed


def test_database_failure_does_not_block_file_expiry(tmp_path, monkeypatch):
    calls = []

    def unavailable():
        raise RuntimeError("Synthetic database outage")

    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        runtime = AnalysisRuntime(storage)
        monkeypatch.setattr(runtime, "get_lifecycle", unavailable)
        monkeypatch.setattr(storage, "cleanup_expired", lambda: calls.append("files"))
        with pytest.raises(RuntimeError):
            runtime.sweep()
        assert calls == ["files", "files"]
        assert runtime.cleanup_failed


def test_file_failure_does_not_block_database_cleanup(tmp_path, monkeypatch):
    calls = []

    class Lifecycle:
        def cleanup(self):
            calls.append("database")
            return SimpleNamespace(failures=0)

    def unavailable():
        raise StorageError()

    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        runtime = AnalysisRuntime(storage)
        monkeypatch.setattr(runtime, "get_lifecycle", lambda: Lifecycle())
        monkeypatch.setattr(storage, "cleanup_expired", unavailable)
        runtime.sweep()
        assert calls == ["database"]
        assert runtime.cleanup_failed


@pytest.mark.asyncio
async def test_cleanup_loop_retries_safely_and_stops_without_leaking_messages(caplog):
    stop = asyncio.Event()

    class FakeRuntime:
        cleanup_failed = False
        calls = 0

        def sweep(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("SYNTHETIC_PRIVATE_SENTINEL")
            self.cleanup_failed = False

    runtime = FakeRuntime()
    with caplog.at_level(logging.WARNING):
        task = asyncio.create_task(run_cleanup(runtime, stop, 0.01))
        try:
            for _ in range(100):
                await asyncio.sleep(0.01)
                if runtime.calls >= 2:
                    break
            assert runtime.calls >= 2
            assert not runtime.cleanup_failed
        finally:
            stop.set()
            await task
    assert "retry scheduled" in caplog.text
    assert "SYNTHETIC_PRIVATE_SENTINEL" not in caplog.text


def test_failed_database_recovery_disposes_engine_and_can_retry(tmp_path, monkeypatch):
    class Engine:
        disposed = False

        def dispose(self):
            self.disposed = True

    engine = Engine()
    monkeypatch.setattr("filingguard.core.runtime.create_db_engine", lambda: engine)
    monkeypatch.setattr("filingguard.core.runtime.create_session_factory", lambda _: object())

    def fail(_):
        raise RuntimeError("Synthetic missing schema")

    monkeypatch.setattr("filingguard.core.runtime.AnalysisLifecycle.recover", fail)
    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        runtime = AnalysisRuntime(storage)
        with pytest.raises(RuntimeError):
            runtime.get_lifecycle()
        assert engine.disposed
        assert runtime.lifecycle is None


def test_default_storage_cannot_enable_private_intake():
    with PrivateTemporaryStorage() as storage:
        with pytest.raises(ValueError):
            AnalysisRuntime(storage).get_lifecycle()
