import json

import httpretty
import pytest
from httpretty import HTTPretty

import dropbox2slack.api.dropboxapi as dropboxapi


@pytest.fixture(autouse=True)
def mock_http_request():
    with httpretty.enabled(allow_net_connect=False):
        yield


def test_get_latest_cursor():
    # prepare
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/files/list_folder/get_latest_cursor",
        responses=[HTTPretty.Response('"cursor"')],
    )

    # execute
    path = "//path/to/folder"
    actual = dropboxapi.get_latest_cursor(path)

    # verify
    print(actual)
    assert "cursor" == actual


def test_list_folder_continue():
    # prepare
    res_body = {
        "cursor": "UT-cursor",
        "entries": [
            {".tag": "folder", "path_display": "/path/to/folder"},
            {".tag": "deleted", "path_display": "/path/to/folder2"},
        ],
    }
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/files/list_folder/continue",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )

    # execute
    cursor = "prev_cursor"
    actual = dropboxapi.list_folder_continue(cursor)

    assert res_body == actual


def test_list_shared_link():
    # prepare
    res_body = {
        "links": [
            {
                "url": "https://sharedlink.com/1",
            },
            {
                "url": "https://sharedlink.com/2",
            },
        ]
    }
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/sharing/list_shared_links",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )

    # execute
    filepath = "/path/to/file"
    actual = dropboxapi.list_shared_link(filepath)

    assert res_body == actual


def test_modify_shared_link():
    # prepare
    res_body = {
        "url": "https://sharedlink.com",
    }
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/sharing/modify_shared_link_settings",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )

    # execute
    link = "https://post.sharedlink.com"
    actual = dropboxapi.modify_shared_link(link)

    assert res_body == actual


def test_create_shared_link():
    # prepare
    res_body = {
        "url": "https://sharedlink.com",
    }
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )

    # execute
    link = "https://post.sharedlink.com"
    actual = dropboxapi.create_shared_link(link)

    assert res_body == actual
