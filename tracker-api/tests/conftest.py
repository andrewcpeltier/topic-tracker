from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.sources import POLITE_DELAY


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr(settings, "llm_stub", True)
    monkeypatch.setattr(settings, "fetch_interval_minutes", 0)
    for name in list(POLITE_DELAY):
        monkeypatch.setitem(POLITE_DELAY, name, 0.0)


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as c:
        yield c
