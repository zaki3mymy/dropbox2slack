import pytest


@pytest.fixture(autouse=True)
def setenv(monkeypatch):
    monkeypatch.setenv("DROPBOX_TOKEN", "DUMMYTOKEN")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/xxxxxxxx")
