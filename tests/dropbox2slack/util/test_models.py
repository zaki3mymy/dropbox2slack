import uuid
import os

import boto3
import pytest
from moto import mock_dynamodb

from dropbox2slack.util.models import CursorModel, get_cursor, save_cursor


@pytest.fixture(autouse=True)
def dynamodb():
    # NOTE: Since it is static, it will be loaded at the start of the test.
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


def test_get_cursor(dynamodb):
    # prepare
    exp = str(uuid.uuid4())
    item = {
        "id": {"S": "cursor"},
        "cursor": {"S": exp},
    }
    dynamodb.put_item(TableName=os.environ["TABLE_NAME"], Item=item)

    # execute
    actual = get_cursor()

    # verify
    assert exp == actual


def test_get_cursor_no_record():
    # prepare

    # execute / verify
    with pytest.raises(CursorModel.DoesNotExist):
        get_cursor()


def test_save_cursor(dynamodb):
    # prepare
    cursor = str(uuid.uuid4())

    # execute
    save_cursor(cursor)

    # verify
    item = {"id": {"S": "cursor"}}
    act = dynamodb.get_item(TableName=os.environ["TABLE_NAME"], Key=item)

    exp = {"id": {"S": "cursor"}, "cursor": {"S": cursor}}
    assert exp == act["Item"]


def test_update_cursor(dynamodb):
    # prepare
    item = {
        "id": {"S": "cursor"},
        "cursor": {"S": "UT-cursor"},
    }
    dynamodb.put_item(TableName=os.environ["TABLE_NAME"], Item=item)
    cursor = str(uuid.uuid4())

    # execute
    save_cursor(cursor)

    # verify
    item = {"id": {"S": "cursor"}}
    act = dynamodb.get_item(TableName=os.environ["TABLE_NAME"], Key=item)

    exp = {"id": {"S": "cursor"}, "cursor": {"S": cursor}}
    assert exp == act["Item"]
