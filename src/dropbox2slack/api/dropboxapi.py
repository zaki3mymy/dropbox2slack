import json
import os

import requests

CONTENT_TYPE_JSON = "application/json"


def get_latest_cursor(path: str) -> dict:
    """Get latest cursor.

    Args:
        path (str): folder path

    Returns:
        dict: {
            "cursor": cursor value
        }
    """
    DROPBOX_TOKEN = os.environ["DROPBOX_TOKEN"]

    url = "https://api.dropboxapi.com/2/files/list_folder/get_latest_cursor"
    headers = {
        "Content-Type": CONTENT_TYPE_JSON,
        "Authorization": "Bearer {}".format(DROPBOX_TOKEN),
    }
    data = {"path": path, "recursive": True}
    response = requests.post(url, data=json.dumps(data), headers=headers).json()

    return response


def list_folder_continue(cursor: str) -> dict:
    """List folder.

    Args:
        cursor (str): cursor

    Returns:
        dict: {
            "cursor": next cursor,
            "entries": [
                {
                    ".tag": "folder" | "deleted",
                    "path_display": "/path/to/folder"
                }
            ]
        }
    """
    DROPBOX_TOKEN = os.environ["DROPBOX_TOKEN"]

    url = "https://api.dropboxapi.com/2/files/list_folder/continue"
    headers = {
        "Content-Type": CONTENT_TYPE_JSON,
        "Authorization": "Bearer {}".format(DROPBOX_TOKEN),
    }
    data = {"cursor": cursor}
    response = requests.post(url, data=json.dumps(data), headers=headers).json()

    return response


def list_shared_link(path: str) -> dict:
    """List shared link.

    Args:
        path (str): filepath

    Returns:
        dict: {
            "links": [
                {
                    "url": shared link
                },
            ]
        }
    """
    DROPBOX_TOKEN = os.environ["DROPBOX_TOKEN"]

    url = "https://api.dropboxapi.com/2/sharing/list_shared_links"
    headers = {
        "Content-Type": CONTENT_TYPE_JSON,
        "Authorization": "Bearer {}".format(DROPBOX_TOKEN),
    }
    data = {"path": path}
    response = requests.post(url, data=json.dumps(data), headers=headers).json()

    return response


def modify_shared_link(shared_link_url: str) -> dict:
    """Modify shared link for sharing team member.

    Args:
        shared_link_url (str): shared link url

    Returns:
        dict: modified result
    """
    DROPBOX_TOKEN = os.environ["DROPBOX_TOKEN"]

    url = "https://api.dropboxapi.com/2/sharing/modify_shared_link_settings"
    headers = {
        "Content-Type": CONTENT_TYPE_JSON,
        "Authorization": "Bearer {}".format(DROPBOX_TOKEN),
    }
    data = {
        "url": shared_link_url,
        "settings": {"audience": "team", "access": "viewer", "allow_download": True},
    }
    response = requests.post(url, data=json.dumps(data), headers=headers).json()

    return response


def create_shared_link(path: str) -> dict:
    """Create shared link.

    Args:
        path (str): filepath

    Returns:
        dict: {
            "url": shared link
        }
    """
    DROPBOX_TOKEN = os.environ["DROPBOX_TOKEN"]

    url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
    headers = {
        "Content-Type": CONTENT_TYPE_JSON,
        "Authorization": "Bearer {}".format(DROPBOX_TOKEN),
    }
    data = {
        "path": path,
        "settings": {"audience": "public", "access": "viewer", "allow_download": True},
    }
    response = requests.post(url, data=json.dumps(data), headers=headers).json()

    return response
