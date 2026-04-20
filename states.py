"""Conversation states enum."""
from enum import Enum


class OrderStates(Enum):
    """States for the order conversation flow."""
    ENTRY_POINT = 1
    EDITING = 2
    EDITING_ITEM = 3
    ENTERING_EDIT_QTY = 4
    CHOOSING_CAT = 5
    CHOOSING_ITEM = 6
    ENTERING_QTY = 7
    CHOOSING_HISTORY = 8
    ENTERING_HISTORY_DATE = 9
    CONFIRM_ORDER = 10
    ENTERING_DATE = 11
    ENTERING_TEMPLATE_NAME = 12
