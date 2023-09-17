from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    ProxyEventType,
    Response,
)
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

logger = Logger()


@app.get("/")
def verify():
    challenge = app.current_event.get_query_string_value("challenge")
    if not challenge:
        logger.error("There is no 'challenge' parameter.")
        return Response(400)
    headers = {
        "Content-Type": "text/plain",
        "X-Content-Type-Options": ["nosniff"],
    }
    return Response(200, headers=headers, body=challenge)


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext):
    return app.resolve(event, context)
