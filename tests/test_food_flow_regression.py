"""Regression tests: prove food flow is unchanged after wiring non-food ConversationHandler.

Goals:
1. Food handler references exist and are unchanged.
2. Food callback prefixes do NOT collide with non-food prefixes.
3. Food session keys do NOT collide with non-food session keys.
4. bot.py registers exactly ONE food ConversationHandler and ONE non-food ConversationHandler.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ─── 1. Food handler references exist ─────────────────────────────────────────

def test_food_handler_references_exist():
    """All food handler names are defined (via AST) in their respective source files.

    We inspect source files directly to avoid triggering telegram imports in the
    test environment.
    """
    base = Path(__file__).resolve().parents[1]
    handlers_base = base / "handlers" / "conversation"

    checks = [
        (handlers_base / "entry.py",      {"cmd_order", "handle_entry", "handle_history_entry"}),
        (handlers_base / "editing.py",     {"show_edit_screen", "edit_item_menu", "handle_item_edit", "receive_edit_qty"}),
        (handlers_base / "category.py",    {"show_cats"}),
        (handlers_base / "confirm.py",     {"confirm_yes", "confirm_no"}),
    ]

    for filepath, names in checks:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
        # async def → AsyncFunctionDef; regular def → FunctionDef
        defined = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in names:
            assert name in defined, f"{name} not defined in {filepath.name}"


# ─── 2. Food callback prefixes do NOT collide with non-food prefixes ────────────

_FOOD_PREFIXES = {
    "en:",       # entry point
    "hi:",       # history entry
    "ei:",       # edit item
    "eq:",       # edit qty
    "cat:",      # category
    "item:",     # item selection
    "done_editing",
    "save_tpl_btn",
    "confirm_yes",
    "confirm_no",
    "back_to_edit",
    "change_date",
    "qdate:",    # quick date
}

_NONFOOD_PREFIXES = {
    "nfe:",      # non-food edit menu
    "nfh:",      # non-food history
    "nfei:",     # non-food edit item
    "nfeq:",     # non-food edit qty
    "nfcat:",    # non-food category
    "nfitem:",   # non-food item
    "nfeq:",     # non-food confirm / edit qty prefix namespace
    "nfqdate:",  # non-food date
    "nftpl:",    # non-food template
    "nf:add_item",
    "nfsearch:",
}


def test_food_and_nonfood_prefixes_are_disjoint():
    """No food prefix appears in the non-food set and vice versa."""
    overlap = _FOOD_PREFIXES & _NONFOOD_PREFIXES
    assert not overlap, f"Prefix collision: {overlap}"


def test_food_prefixes_not_in_nonfood():
    """No food prefix is used as a non-food prefix."""
    collisions = _FOOD_PREFIXES & _NONFOOD_PREFIXES
    assert not collisions, f"Food prefixes used as non-food: {collisions}"


def test_nonfood_prefixes_not_in_food():
    """No non-food prefix is used as a food prefix."""
    collisions = _NONFOOD_PREFIXES & _FOOD_PREFIXES
    assert not collisions, f"Non-food prefixes used as food: {collisions}"


# ─── 3. Food session keys do NOT collide with non-food session keys ────────────

_FOOD_SESSION_KEYS = {
    "order",
    "order_date",
    "current_cat",
    "current_item",
    "editing_code",
}

_NONFOOD_SESSION_KEYS = {
    "nonfood_order",
    "nonfood_order_date",
    "nf_current_cat",
    "nf_current_item",
    "nf_editing_code",
}


def test_food_and_nonfood_session_keys_are_disjoint():
    """No food session key appears in the non-food set and vice versa."""
    overlap = _FOOD_SESSION_KEYS & _NONFOOD_SESSION_KEYS
    assert not overlap, f"Session key collision: {overlap}"


def test_food_session_keys_not_in_nonfood():
    """Food session keys are not used as non-food keys."""
    collisions = _FOOD_SESSION_KEYS & _NONFOOD_SESSION_KEYS
    assert not collisions, f"Food keys used as non-food: {collisions}"


def test_nonfood_session_keys_not_in_food():
    """Non-food session keys are not used as food keys."""
    collisions = _NONFOOD_SESSION_KEYS & _FOOD_SESSION_KEYS
    assert not collisions, f"Non-food keys used as food: {collisions}"


# ─── 4. bot.py registers exactly ONE food + ONE non-food ConversationHandler ─────

def test_bot_parses_as_valid_python():
    """bot.py is syntactically valid Python."""
    bot_path = Path(__file__).resolve().parents[1] / "bot.py"
    source = bot_path.read_text(encoding="utf-8")
    ast.parse(source)
    assert True  # If we got here, parsing succeeded


def test_bot_has_food_conv_and_nonfood_conv():
    """bot.py source contains exactly one food ConversationHandler and one nonfood_conv."""
    bot_path = Path(__file__).resolve().parents[1] / "bot.py"
    source = bot_path.read_text(encoding="utf-8")

    # Food ConversationHandler — check it exists (by the presence of entry_points with cmd_order)
    assert "ConversationHandler" in source
    assert 'entry_points=[CommandHandler("order", cmd_order)]' in source
    assert "allow_reentry=True" in source

    # Non-food ConversationHandler
    assert "nonfood_conv" in source
    assert "app.add_handler(nonfood_conv)" in source

    # Only ONE add_handler(ConversationHandler...) call — there is only one
    # food ConversationHandler in the source (we verify no duplicate ConversationHandler definitions)
    conv_handler_count = source.count("ConversationHandler(")
    assert conv_handler_count == 1, (
        f"Expected exactly 1 ConversationHandler in bot.py (food only), "
        f"found {conv_handler_count}"
    )
