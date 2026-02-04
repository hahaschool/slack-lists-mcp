"""Slack Lists MCP Server Package."""

from slack_lists_mcp.__main__ import main
from slack_lists_mcp.builders import (
    ColumnBuilder,
    ItemBuilder,
    SchemaBuilder,
    SelectOption,
    batch_create_items,
)
from slack_lists_mcp.helpers import (
    AccessLevel,
    FieldType,
    extract_text,
    make_attachment,
    make_canvas,
    make_channel,
    make_checkbox,
    make_date,
    make_email,
    make_field,
    make_link,
    make_message,
    make_number,
    make_phone,
    make_rating,
    make_rich_text,
    make_select,
    make_timestamp,
    make_user,
    make_vote,
)
from slack_lists_mcp.server import mcp

__version__ = "0.1.0"
__all__ = [
    "main",
    "mcp",
    # Enums
    "FieldType",
    "AccessLevel",
    # Builders
    "SchemaBuilder",
    "ColumnBuilder",
    "SelectOption",
    "ItemBuilder",
    "batch_create_items",
    # Helper functions
    "make_rich_text",
    "make_link",
    "make_select",
    "make_user",
    "make_date",
    "make_number",
    "make_field",
    "make_checkbox",
    "make_rating",
    "make_timestamp",
    "make_channel",
    "make_email",
    "make_phone",
    "make_attachment",
    "make_message",
    "make_vote",
    "make_canvas",
    "extract_text",
]
