import uuid
from collections import namedtuple

import pytest

from dropbox2slack.lambda_function import lambda_handler


@pytest.fixture
def lambda_context():
    lambda_context = {
        "function_name": "dropbox2slack",
        "memory_limit_in_mb": 128,
        "invoked_function_arn": "arn:aws:lambda:ap-northeast-1:123456789012:function:dropbox2slack",
        "aws_request_id": str(uuid.uuid4()),
    }

    return namedtuple("LambdaContext", lambda_context.keys())(*lambda_context.values())


def test_verify_ok(lambda_context):
    # prepare
    event = {
        "path": "/",
        "httpMethod": "GET",
        "queryStringParameters": {"challenge": "challenge_value"},
    }

    # execute
    response = lambda_handler(event, lambda_context)

    # verify
    assert 200 == response["statusCode"]
    assert "challenge_value" == response["body"]


def test_verify_no_querystrings(lambda_context):
    # prepare
    event = {
        "path": "/",
        "httpMethod": "GET",
        # "queryStringParameters": {"challenge": "challenge_value"},
    }

    # execute
    response = lambda_handler(event, lambda_context)

    # verify
    print(response)
    assert 400 == response["statusCode"]
