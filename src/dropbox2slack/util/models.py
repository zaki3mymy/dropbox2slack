from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute


CURSOR_ID = "cursor"


class CursorModel(Model):
    class Meta:
        table_name = "dropboxapi-table"
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
    cursor = CursorModel(CURSOR_ID, cursor)
    cursor.save()
