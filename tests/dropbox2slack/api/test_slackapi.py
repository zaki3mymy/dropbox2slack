import json
import os

import httpretty
import pytest
from httpretty import HTTPretty
from pydantic import ValidationError

import dropbox2slack.api.slackapi as slackapi


@pytest.fixture(autouse=True)
def mock_http_request():
    with httpretty.enabled(allow_net_connect=False):
        yield


def test_generate_messages_store_one_channel_one_file():
    # prepare
    store = slackapi.ChangedFileStore()
    store.add("channel1", "/path/to/file1", "https://file1.com")

    # execute
    act = slackapi.generage_messages_store(store)

    # verify
    exp = {"channel1": ["<https://file1.com|/path/to/file1>"]}
    assert exp == act.files_by_channel


def test_generate_messages_store_one_channel_two_files():
    # prepare
    store = slackapi.ChangedFileStore()
    store.add("channel1", "/path/to/file1", "https://file1.com")
    store.add("channel1", "/path/to/file2", "https://file2.com")

    # execute
    act = slackapi.generage_messages_store(store)

    # verify
    exp = {
        "channel1": [
            "<https://file1.com|/path/to/file1>",
            "<https://file2.com|/path/to/file2>",
        ],
    }
    assert exp == act.files_by_channel


def test_generate_messages_store_two_channels_one_file():
    # prepare
    store = slackapi.ChangedFileStore()
    store.add("channel1", "/path/to/file1", "https://file1.com")
    store.add("channel2", "/path/to/file2", "https://file2.com")

    # execute
    act = slackapi.generage_messages_store(store)

    # verify
    exp = {
        "channel1": [
            "<https://file1.com|/path/to/file1>",
        ],
        "channel2": [
            "<https://file2.com|/path/to/file2>",
        ],
    }
    assert exp == act.files_by_channel


def test_generate_messages_store_two_channels_two_files():
    # prepare
    store = slackapi.ChangedFileStore()
    store.add("channel1", "/path/to/file1", "https://file1.com")
    store.add("channel2", "/path/to/file2", "https://file2.com")
    store.add("channel1", "/path/to/file11", "https://file11.com")
    store.add("channel2", "/path/to/file22", "https://file22.com")

    # execute
    act = slackapi.generage_messages_store(store)

    # verify
    exp = {
        "channel1": [
            "<https://file1.com|/path/to/file1>",
            "<https://file11.com|/path/to/file11>",
        ],
        "channel2": [
            "<https://file2.com|/path/to/file2>",
            "<https://file22.com|/path/to/file22>",
        ],
    }
    assert exp == act.files_by_channel


def test_invalid_shared_link():
    # prepare
    store = slackapi.ChangedFileStore()

    # execute / verify
    with pytest.raises(ValidationError):
        store.add("channel1", "/path/to/file1", "invalid link")


def test_generate_messages_items_add_once():
    # prepare
    store = slackapi.SlackMessageStore()
    store.add("channel1", "link1")

    # execute / verify
    for channel, data in store.generate_messages_items():
        assert "channel1" == channel
        assert "channel1" == data["channel"]
        assert "link1" == data["attachments"][0]["fields"][0]["value"]


def test_generate_messages_items_add_twice():
    # prepare
    store = slackapi.SlackMessageStore()
    store.add("channel1", "link1")
    store.add("channel1", "link2")

    # execute / verify
    for channel, data in store.generate_messages_items():
        assert "channel1" == channel
        assert "channel1" == data["channel"]
        assert "link1\nlink2" == data["attachments"][0]["fields"][0]["value"]


def test_generate_messages_items_add_twice_other_channel():
    # prepare
    store = slackapi.SlackMessageStore()
    store.add("channel1", "link1")
    store.add("channel2", "link2")

    # execute
    act = list(store.generate_messages_items())

    # verifyF
    assert "channel1" == act[0][0]
    assert "link1" == act[0][1]["attachments"][0]["fields"][0]["value"]
    assert "channel2" == act[1][0]
    assert "link2" == act[1][1]["attachments"][0]["fields"][0]["value"]


def test_send_messages():
    # prepare
    res_body = {}
    httpretty.register_uri(
        httpretty.POST,
        os.environ["SLACK_WEBHOOK_URL"],
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )

    store = slackapi.SlackMessageStore()
    store.add("channel1", "link1")

    # execute
    slackapi.send_messages(store)

    # verify


def test_send_messages_channel_does_not_exist():
    # prepare
    res_body = {}
    httpretty.register_uri(
        httpretty.POST,
        os.environ["SLACK_WEBHOOK_URL"],
        responses=[HTTPretty.Response(json.dumps(res_body), status=404)],
    )

    store = slackapi.SlackMessageStore()
    store.add("channel1", "link1")

    # execute
    slackapi.send_messages(store)

    # verify
