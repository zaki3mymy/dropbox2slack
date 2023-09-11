import pytest


@pytest.fixture(autouse=True)
def setenv(monkeypatch):
    monkeypatch.setenv("DROPBOX_TOKEN", "DUMMYTOKEN")
