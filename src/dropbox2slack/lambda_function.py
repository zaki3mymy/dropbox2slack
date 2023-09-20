import os

import api.dropboxapi as dropboxapi
import api.slackapi as slackapi
import util.models as models
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


@app.post("/")
def webhook():
    DROPBOX_TARGET_DIR = os.environ["DROPBOX_TARGET_DIR"]
    try:
        cursor = models.get_cursor()
    except models.CursorModel.DoesNotExist:  # type: ignore
        res = dropboxapi.get_latest_cursor(DROPBOX_TARGET_DIR)
        cursor = res["cursor"]

    res = dropboxapi.list_folder_continue(cursor)
    models.save_cursor(res["cursor"])

    if len(res["entries"]) == 0:
        # no change
        logger.info("no change in {}".format(DROPBOX_TARGET_DIR))
        return Response(200, body="no change")

    store = slackapi.ChangedFileStore()
    for entry in res["entries"]:
        logger.info(f"entry: {entry}")
        if entry[".tag"] in ("folder", "deleted"):
            # process only files
            continue

        # path_display = "/path/to/folder/<channel name>/<filename>""
        filepath = entry["path_display"]
        channel = filepath.replace(DROPBOX_TARGET_DIR + "/", "").split("/")[0]

        try:
            res = dropboxapi.list_shared_link(filepath)
            links = res["links"]
            if len(links) != 0:
                logger.debug("modify_shared_link")
                url = links[0]["url"]
                dropboxapi.modify_shared_link(url)
            else:
                logger.debug("create_shared_link")
                res = dropboxapi.create_shared_link(filepath)
                logger.debug("Response of create shared link...: {}".format(res))
                url = res["url"]

            store.add(channel, filepath, url)
        except Exception as e:
            logger.exception("shared link error!", e)

    logger.info("send messages...")
    msg_store = slackapi.generage_messages_store(store)
    slackapi.send_messages(msg_store)


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: APIGatewayProxyEvent, context: LambdaContext):
    return app.resolve(event, context)
