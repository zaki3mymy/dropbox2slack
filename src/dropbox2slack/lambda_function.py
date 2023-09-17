import json

def verify(event):
    challenge = event["queryStringParameters"]["challenge"]
    headers = {
        "Content-Type": "text/plain",
        "X-Content-Type-Options": "nosniff",
    }
    return {"statusCode": 200, "headers": headers, "body": challenge}

def lambda_handler(event, context):
    if event["httpMethod"] == "GET":
        return verify(event)

    return {"statusCode": 200, "body": json.dumps("Hello from Lambda!")}
