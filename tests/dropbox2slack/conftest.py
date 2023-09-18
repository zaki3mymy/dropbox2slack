import pytest


@pytest.fixture(autouse=True)
def setenv(monkeypatch):
    monkeypatch.setenv("TABLE_NAME", "dummy-table")
    monkeypatch.setenv("DROPBOX_TOKEN", "DUMMYTOKEN")
    monkeypatch.setenv("DROPBOX_TARGET_DIR", "/target")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/xxxxxxxx")
