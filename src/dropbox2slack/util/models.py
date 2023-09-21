import os

from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model

CURSOR_ID = "cursor"


class CursorModel(Model):
    class Meta:
        table_name = os.environ.get("TABLE_NAME")
        region = "ap-northeast-1"

    id = UnicodeAttribute(hash_key=True)
    cursor = UnicodeAttribute(range_key=True)


def get_cursor() -> str:
    """Get cursor string.

    Returns:
        str: cursor
    """
    cursor = CursorModel.get(CURSOR_ID)
    return cursor.cursor


def save_cursor(cursor: str):
    """Save cursor

    Args:
        cursor (str): cursor
    """
    cursor_model = CursorModel(CURSOR_ID, cursor)
    cursor_model.save()
