import json
import os
import uuid
from collections import namedtuple

import boto3
import httpretty
import pytest
from httpretty import HTTPretty
from moto import mock_dynamodb
from util.models import CursorModel

from dropbox2slack.lambda_function import lambda_handler


@pytest.fixture(autouse=True)
def mock_http_request():
    with httpretty.enabled(allow_net_connect=False):
        # mock get_latest_cursor
        httpretty.register_uri(
            "POST",
            "https://api.dropboxapi.com/2/files/list_folder/get_latest_cursor",
            responses=[HTTPretty.Response(json.dumps({"cursor": "cursor-value"}))],
        )

        # mock list_folder_continue
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

        yield


@pytest.fixture(autouse=True)
def dynamodb():
    CursorModel.Meta.table_name = os.environ["TABLE_NAME"]

    with mock_dynamodb():
        client = boto3.client("dynamodb")
        client.create_table(
            TableName=os.environ["TABLE_NAME"],
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
        )

        yield client


@pytest.fixture
def lambda_context():
    lambda_context = {
        "function_name": "dropbox2slack",
        "memory_limit_in_mb": 128,
        "invoked_function_arn": "arn:aws:lambda:ap-northeast-1:123456789012:function:dropbox2slack",
        "aws_request_id": str(uuid.uuid4()),
    }

    return namedtuple("LambdaContext", lambda_context.keys())(*lambda_context.values())


def test_webhook_no_cursor(lambda_context, dynamodb):
    """cursor が保存されていない場合"""
    # prepare
    event = {
        "path": "/",
        "httpMethod": "POST",
    }

    # execute
    response = lambda_handler(event, lambda_context)

    # verify
    assert 200 == response["statusCode"]

    # verify request
    req_list = httpretty.latest_requests()
    assert "get_latest_cursor" in req_list[0].url
    assert (
        json.dumps({"path": os.environ["DROPBOX_TARGET_DIR"], "recursive": True})
        == req_list[0].body.decode()
    )
    assert "list_folder/continue" in req_list[2].url
    assert json.dumps({"cursor": "cursor-value"}) == req_list[2].body.decode()

    # verify saved cursor
    item = {"id": {"S": "cursor"}}
    act = dynamodb.get_item(TableName=os.environ["TABLE_NAME"], Key=item)
    exp = {"id": {"S": "cursor"}, "cursor": {"S": "UT-cursor"}}
    assert exp == act["Item"]


def test_webhook_no_entries(lambda_context, dynamodb):
    """entries がない場合"""
    # prepare
    event = {
        "path": "/",
        "httpMethod": "POST",
    }
    # mock list_folder_continue
    res_body = {
        "cursor": "UT-cursor",
        "entries": [],
    }
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/files/list_folder/continue",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )

    # execute
    response = lambda_handler(event, lambda_context)

    # verify
    assert 200 == response["statusCode"]

    # verify saved cursor
    item = {"id": {"S": "cursor"}}
    act = dynamodb.get_item(TableName=os.environ["TABLE_NAME"], Key=item)
    exp = {"id": {"S": "cursor"}, "cursor": {"S": "UT-cursor"}}
    assert exp == act["Item"]


def test_webhook_one_entry_has_shared_link(lambda_context, dynamodb):
    """one entry"""
    # prepare
    event = {
        "path": "/",
        "httpMethod": "POST",
    }
    # mock list_folder_continue
    res_body = {
        "cursor": "UT-cursor",
        "entries": [
            {
                ".tag": "file",
                "path_display": f"{os.environ['DROPBOX_TARGET_DIR']}/channel1/file",
            },
        ],
    }
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/files/list_folder/continue",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )
    # mock list_shared_link
    res_body = {
        "links": [
            {"url": "https://shared.link.com"},
        ]
    }
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/sharing/list_shared_links",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )
    # mock modify_shared_link
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/sharing/modify_shared_link_settings",
    )
    # mock slackapi.send_message
    httpretty.register_uri(
        httpretty.POST,
        os.environ["SLACK_WEBHOOK_URL"],
        responses=[HTTPretty.Response("", status=200)],
    )

    # execute
    response = lambda_handler(event, lambda_context)

    # verify
    assert 200 == response["statusCode"]
    # verify saved cursor
    item = {"id": {"S": "cursor"}}
    act = dynamodb.get_item(TableName=os.environ["TABLE_NAME"], Key=item)
    exp = {"id": {"S": "cursor"}, "cursor": {"S": "UT-cursor"}}
    assert exp == act["Item"]
    # verify send_message
    req = httpretty.last_request()
    assert os.environ["SLACK_WEBHOOK_URL"] == req.url
    exp_body = {
        "channel": "channel1",
        "attachments": [
            {
                "fallback": "Dropboxが更新されました。",
                "color": "#0062ff",
                "fields": [
                    {
                        "title": "以下のファイルが更新されました。",
                        "value": "<https://shared.link.com|/target/channel1/file>",
                    }
                ],
            }
        ],
    }
    assert json.dumps(exp_body) == req.body.decode()


def test_webhook_one_entry_has_no_shared_link(lambda_context, dynamodb):
    """one entry"""
    # prepare
    event = {
        "path": "/",
        "httpMethod": "POST",
    }
    # mock list_folder_continue
    res_body = {
        "cursor": "UT-cursor",
        "entries": [
            {
                ".tag": "file",
                "path_display": f"{os.environ['DROPBOX_TARGET_DIR']}/channel1/file",
            },
        ],
    }
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/files/list_folder/continue",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )
    # mock list_shared_link
    res_body = {"links": []}
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/sharing/list_shared_links",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )
    # mock create_shared_link
    res_body = {"url": "https://created.shared.link"}
    httpretty.register_uri(
        httpretty.POST,
        "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
        responses=[HTTPretty.Response(json.dumps(res_body))],
    )
    # mock slackapi.send_message
    httpretty.register_uri(
        httpretty.POST,
        os.environ["SLACK_WEBHOOK_URL"],
        responses=[HTTPretty.Response("", status=200)],
    )

    # execute
    response = lambda_handler(event, lambda_context)

    # verify
    assert 200 == response["statusCode"]
    # verify saved cursor
    item = {"id": {"S": "cursor"}}
    act = dynamodb.get_item(TableName=os.environ["TABLE_NAME"], Key=item)
    exp = {"id": {"S": "cursor"}, "cursor": {"S": "UT-cursor"}}
    assert exp == act["Item"]
    # verify send_message
    req = httpretty.last_request()
    assert os.environ["SLACK_WEBHOOK_URL"] == req.url
    exp_body = {
        "channel": "channel1",
        "attachments": [
            {
                "fallback": "Dropboxが更新されました。",
                "color": "#0062ff",
                "fields": [
                    {
                        "title": "以下のファイルが更新されました。",
                        "value": "<https://created.shared.link|/target/channel1/file>",
                    }
                ],
            }
        ],
    }
    assert json.dumps(exp_body) == req.body.decode()
