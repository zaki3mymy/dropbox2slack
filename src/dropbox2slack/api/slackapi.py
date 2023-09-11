import json
import os
import re
from collections import defaultdict
from http import HTTPStatus
from typing import ItemsView, Iterator, List, Tuple

import requests
from aws_lambda_powertools import Logger
from pydantic import BaseModel, field_validator

url_regex = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
re_url = re.compile(url_regex)

logger = Logger()


class _FileInfo(BaseModel):
    filepath: str
    shared_link: str

    @field_validator("shared_link")
    def is_shared_link_url(cls, v):
        if not re_url.match(v):
            raise ValueError
        return v

    def generate_filepath_with_link(self):
        # URL link of Slack API
        return "<{}|{}>".format(self.shared_link, self.filepath)


class ChangedFileStore:
    def __init__(self):
        # {
        #   channel: files list
        # }
        self.files_by_channel = defaultdict(list)

    def add(self, channel: str, filepath: str, shared_link: str) -> None:
        self.files_by_channel[channel].append(
            _FileInfo(filepath=filepath, shared_link=shared_link)
        )

    def items(self) -> ItemsView[str, List[_FileInfo]]:
        return self.files_by_channel.items()


class SlackMessageStore:
    def __init__(self):
        self.files_by_channel = defaultdict(list)

    def add(self, channel, filepath_with_link) -> None:
        self.files_by_channel[channel].append(filepath_with_link)

    def generate_messages_items(self) -> Iterator[Tuple[str, dict]]:
        for channel, filelist in self.files_by_channel.items():
            fields = [{"title": "以下のファイルが更新されました。", "value": "\n".join(filelist)}]
            data = {
                "channel": channel,
                "attachments": [
                    {
                        "fallback": "Dropboxが更新されました。",
                        "color": "#0062ff",
                        "fields": fields,
                    }
                ],
            }
            yield channel, data


def generage_messages_store(store: ChangedFileStore) -> SlackMessageStore:
    msg_store = SlackMessageStore()
    for channel, file_info_list in store.items():
        for file_info in file_info_list:
            msg_store.add(channel, file_info.generate_filepath_with_link())
    return msg_store


def send_messages(store: SlackMessageStore):
    WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

    for channel, data in store.generate_messages_items():
        logger.info("send message to channel: %s", channel)
        msg = json.dumps(data)
        res = requests.post(WEBHOOK_URL, data=msg)
        if res.status_code == HTTPStatus.NOT_FOUND:
            # default channel is that configed Incoming Webhooks.
            logger.warning(
                'channel "%s" does not exist. send to default channel.', channel
            )
            del data["channel"]
            msg = json.dumps(data)
            res = requests.post(WEBHOOK_URL, data=msg)

        logger.info("send message response: %s", res)
