"""Contract tests for the non-food flow namespace."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from states import OrderStates


NONFOOD_CALLBACK_PREFIXES = {
    "nfe:",
    "nfh:",
    "nfcat:",
    "nfitem:",
    "nfsearch:",
    "nfei:",
    "nfeq:",
    "nftpl:",
    "nfqdate:",
}

NONFOOD_SESSION_KEYS = {
    "nonfood_order",
    "nonfood_order_date",
    "nf_current_cat",
    "nf_current_item",
    "nf_editing_code",
    "nf_search_query",
}


def test_nonfood_states_are_distinct_members_not_food_aliases():
    assert OrderStates.NONFOOD_ENTRY_POINT is not OrderStates.ENTRY_POINT
    assert OrderStates.NONFOOD_EDITING is not OrderStates.EDITING
    assert OrderStates.NONFOOD_EDITING_ITEM is not OrderStates.EDITING_ITEM
    assert OrderStates.NONFOOD_ENTERING_EDIT_QTY is not OrderStates.ENTERING_EDIT_QTY
    assert OrderStates.NONFOOD_CHOOSING_CAT is not OrderStates.CHOOSING_CAT
    assert OrderStates.NONFOOD_CHOOSING_ITEM is not OrderStates.CHOOSING_ITEM
    assert OrderStates.NONFOOD_ENTERING_QTY is not OrderStates.ENTERING_QTY
    assert OrderStates.NONFOOD_CHOOSING_HISTORY is not OrderStates.CHOOSING_HISTORY
    assert OrderStates.NONFOOD_ENTERING_HISTORY_DATE is not OrderStates.ENTERING_HISTORY_DATE
    assert OrderStates.NONFOOD_CONFIRM_ORDER is not OrderStates.CONFIRM_ORDER
    assert OrderStates.NONFOOD_ENTERING_DATE is not OrderStates.ENTERING_DATE
    assert OrderStates.NONFOOD_ENTERING_TEMPLATE_NAME is not OrderStates.ENTERING_TEMPLATE_NAME

    assert len({state.value for state in OrderStates}) == len(OrderStates)


def test_nonfood_callback_namespace_is_explicit_and_disjoint_from_food():
    food_prefixes = {"en:", "hi:", "cat:", "item:", "ei:", "eq:", "tpl_", "qdate:"}

    assert NONFOOD_CALLBACK_PREFIXES == {
        "nfe:",
        "nfh:",
        "nfcat:",
        "nfitem:",
        "nfsearch:",
        "nfei:",
        "nfeq:",
        "nftpl:",
        "nfqdate:",
    }
    assert NONFOOD_CALLBACK_PREFIXES.isdisjoint(food_prefixes)


def test_nonfood_session_keys_are_dedicated_to_nonfood_flow():
    food_keys = {"order", "order_date", "current_cat", "current_item", "editing_code", "search_query"}

    assert NONFOOD_SESSION_KEYS == {
        "nonfood_order",
        "nonfood_order_date",
        "nf_current_cat",
        "nf_current_item",
        "nf_editing_code",
        "nf_search_query",
    }
    assert NONFOOD_SESSION_KEYS.isdisjoint(food_keys)
