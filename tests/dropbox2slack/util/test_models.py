import uuid

import boto3
import pytest
from moto import mock_dynamodb

from dropbox2slack.util.models import get_cursor, save_cursor, CursorModel


@pytest.fixture(autouse=True)
def dynamodb():
    mock = mock_dynamodb()
    mock.start()

    client = boto3.client("dynamodb")
    client.create_table(
        TableName=CursorModel.Meta.table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
    )

    yield client

    mock.stop()


def test_get_cursor(dynamodb):
    # prepare
    exp = str(uuid.uuid4())
    item = {
        "id": {"S": "cursor"},
        "cursor": {"S": exp},
    }
    dynamodb.put_item(TableName=CursorModel.Meta.table_name, Item=item)

    # execute
    actual = get_cursor()
    assert exp == actual


def test_save_cursor(dynamodb):
    # prepare
    cursor = str(uuid.uuid4())

    # execute
    save_cursor(cursor)

    # verify
    item = {"id": {"S": "cursor"}}
    act = dynamodb.get_item(TableName=CursorModel.Meta.table_name, Key=item)

    exp = {"id": {"S": "cursor"}, "cursor": {"S": cursor}}
    assert exp == act["Item"]


def test_update_cursor(dynamodb):
    # prepare
    item = {
        "id": {"S": "cursor"},
        "cursor": {"S": "UT-cursor"},
    }
    dynamodb.put_item(TableName=CursorModel.Meta.table_name, Item=item)
    cursor = str(uuid.uuid4())

    # execute
    save_cursor(cursor)

    # verify
    item = {"id": {"S": "cursor"}}
    act = dynamodb.get_item(TableName=CursorModel.Meta.table_name, Key=item)

    exp = {"id": {"S": "cursor"}, "cursor": {"S": cursor}}
    assert exp == act["Item"]
