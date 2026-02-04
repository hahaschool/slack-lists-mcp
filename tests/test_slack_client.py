"""Tests for the SlackListsClient."""

from unittest.mock import MagicMock, patch

import pytest
from slack_sdk.errors import SlackApiError

from slack_lists_mcp.slack_client import SlackListsClient


@pytest.fixture
def mock_slack_client():
    """Create a mock Slack client."""
    with patch("slack_lists_mcp.slack_client.WebClient") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_client_initialization(mock_slack_client):
    """Test SlackListsClient initialization."""
    with patch.dict("os.environ", {"SLACK_BOT_TOKEN": "test-token"}):
        client = SlackListsClient()
        assert client.client is not None


@pytest.mark.asyncio
async def test_add_item(mock_slack_client):
    """Test adding an item to a list."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "item": {
                "id": "Rec123",
                "list_id": "F123",
                "fields": [
                    {"column_id": "Col123", "text": "Test Item"},
                ],
            },
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "rich_text": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [{"type": "text", "text": "Test Item"}],
                            },
                        ],
                    },
                ],
            },
        ],
    )

    assert result["id"] == "Rec123"
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.items.create",
        json={
            "list_id": "F123",
            "initial_fields": [
                {
                    "column_id": "Col123",
                    "rich_text": [
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [{"type": "text", "text": "Test Item"}],
                                },
                            ],
                        },
                    ],
                },
            ],
        },
    )


@pytest.mark.asyncio
async def test_update_item(mock_slack_client):
    """Test updating items in a list."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.update_item(
        list_id="F123",
        cells=[
            {
                "row_id": "Rec123",
                "column_id": "Col123",
                "text": "Updated Item",
            },
        ],
    )

    assert result["success"] is True
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.items.update",
        json={
            "list_id": "F123",
            "cells": [
                {
                    "row_id": "Rec123",
                    "column_id": "Col123",
                    "rich_text": [
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {"type": "text", "text": "Updated Item"}
                                    ],
                                }
                            ],
                        }
                    ],
                },
            ],
        },
    )


@pytest.mark.asyncio
async def test_delete_item(mock_slack_client):
    """Test deleting an item from a list."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.delete_item(
        list_id="F123",
        item_id="Rec123",
    )

    assert result["deleted"] is True
    assert result["item_id"] == "Rec123"
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.items.delete",
        json={"list_id": "F123", "id": "Rec123"},
    )


@pytest.mark.asyncio
async def test_get_item(mock_slack_client):
    """Test getting a specific item."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "record": {
                "id": "Rec123",
                "fields": [
                    {"column_id": "Col123", "text": "Test Item"},
                ],
            },
            "list": {"list_metadata": {"schema": []}},
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.get_item(
        list_id="F123",
        item_id="Rec123",
    )

    # get_item returns item (from record), list, and subtasks
    assert "item" in result
    assert result["item"]["id"] == "Rec123"
    # include_is_subscribed is not included when False
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.items.info",
        json={"list_id": "F123", "id": "Rec123"},
    )


@pytest.mark.asyncio
async def test_list_items_without_filters(mock_slack_client):
    """Test listing items without filters."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "items": [
                {"id": "Rec1", "fields": []},
                {"id": "Rec2", "fields": []},
            ],
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.list_items(
        list_id="F123",
        limit=100,
    )

    assert len(result["items"]) == 2
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.items.list",
        json={"list_id": "F123", "limit": 100},
    )


@pytest.mark.asyncio
async def test_list_items_with_filters(mock_slack_client):
    """Test listing items with client-side filters."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "items": [
                {
                    "id": "Rec1",
                    "fields": [
                        {"key": "name", "text": "Test Item"},
                        {"key": "status", "select": ["active"]},
                    ],
                },
                {
                    "id": "Rec2",
                    "fields": [
                        {"key": "name", "text": "Another Item"},
                        {"key": "status", "select": ["inactive"]},
                    ],
                },
            ],
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.list_items(
        list_id="F123",
        limit=100,
        filters={"name": {"contains": "Test"}},
    )

    # Only the first item should match the filter
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == "Rec1"

    # Should request more items when filtering
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.items.list",
        json={"list_id": "F123", "limit": 300},  # 3x the requested limit
    )


@pytest.mark.asyncio
async def test_filter_matching_logic():
    """Test the filter matching logic directly."""
    client = SlackListsClient()

    # Test equals operator
    item = {
        "fields": [
            {"key": "status", "select": ["active"]},
            {"key": "name", "text": "Test Item"},
        ],
    }

    assert client._matches_filters(item, {"status": {"equals": "active"}}) is True
    assert client._matches_filters(item, {"status": {"equals": "inactive"}}) is False

    # Test contains operator
    assert client._matches_filters(item, {"name": {"contains": "Test"}}) is True
    assert (
        client._matches_filters(item, {"name": {"contains": "test"}}) is True
    )  # Case-insensitive
    assert client._matches_filters(item, {"name": {"contains": "Other"}}) is False

    # Test not_equals operator
    assert client._matches_filters(item, {"status": {"not_equals": "inactive"}}) is True
    assert client._matches_filters(item, {"status": {"not_equals": "active"}}) is False

    # Test not_contains operator
    assert client._matches_filters(item, {"name": {"not_contains": "Other"}}) is True
    assert client._matches_filters(item, {"name": {"not_contains": "Test"}}) is False

    # Test in operator
    assert (
        client._matches_filters(item, {"status": {"in": ["active", "pending"]}}) is True
    )
    assert (
        client._matches_filters(item, {"status": {"in": ["inactive", "pending"]}})
        is False
    )

    # Test not_in operator
    assert (
        client._matches_filters(item, {"status": {"not_in": ["inactive", "pending"]}})
        is True
    )
    assert (
        client._matches_filters(item, {"status": {"not_in": ["active", "pending"]}})
        is False
    )

    # Test multiple filters (AND logic)
    assert (
        client._matches_filters(
            item,
            {
                "status": {"equals": "active"},
                "name": {"contains": "Test"},
            },
        )
        is True
    )

    assert (
        client._matches_filters(
            item,
            {
                "status": {"equals": "active"},
                "name": {"contains": "Other"},
            },
        )
        is False
    )


@pytest.mark.asyncio
async def test_field_value_extraction():
    """Test the field value extraction logic."""
    client = SlackListsClient()

    # Test checkbox field
    field = {"checkbox": True}
    assert client._extract_field_value(field) is True

    # Test select field
    field = {"select": ["option1"]}
    assert client._extract_field_value(field) == ["option1"]

    # Test user field
    field = {"user": ["U123"]}
    assert client._extract_field_value(field) == ["U123"]

    # Test date field
    field = {"date": ["2024-01-01"]}
    assert client._extract_field_value(field) == ["2024-01-01"]

    # Test text field
    field = {"text": "Test Text"}
    assert client._extract_field_value(field) == "Test Text"

    # Test number field
    field = {"number": [42]}
    assert client._extract_field_value(field) == [42]

    # Test email field
    field = {"email": ["test@example.com"]}
    assert client._extract_field_value(field) == ["test@example.com"]

    # Test phone field
    field = {"phone": ["+1234567890"]}
    assert client._extract_field_value(field) == ["+1234567890"]

    # Test fallback to value field
    field = {"value": "fallback"}
    assert client._extract_field_value(field) == "fallback"

    # Test empty field
    field = {}
    assert client._extract_field_value(field) is None


@pytest.mark.asyncio
async def test_get_list(mock_slack_client):
    """Test getting list information."""
    mock_slack_client.api_call = MagicMock(
        side_effect=[
            # First call: items.list
            {
                "ok": True,
                "items": [{"id": "Rec1"}],
            },
            # Second call: items.info
            {
                "ok": True,
                "list": {
                    "id": "F123",
                    "name": "Test List",
                    "title": "Test List Title",
                },
            },
        ],
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.get_list(list_id="F123")

    assert result["id"] == "F123"
    assert result["name"] == "Test List"
    assert mock_slack_client.api_call.call_count == 2


@pytest.mark.asyncio
async def test_get_list_empty(mock_slack_client):
    """Test getting list information when list is empty."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "items": [],
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.get_list(list_id="F123")

    assert result["id"] == "F123"
    assert "message" in result
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.items.list",
        json={"list_id": "F123", "limit": 1},
    )


@pytest.mark.asyncio
async def test_error_handling(mock_slack_client):
    """Test error handling for API failures."""
    mock_response = MagicMock()
    # Create proper response data
    mock_response.data = {
        "ok": False,
        "error": "list_not_found",
        "error_message": "List not found",
    }
    # Ensure get() returns actual string values, not MagicMock
    mock_response.get = lambda key, default=None: {
        "error": "list_not_found",
        "error_message": "List not found",
        "ok": False,
    }.get(key, default)

    mock_slack_client.api_call = MagicMock(
        side_effect=SlackApiError(
            message="The request to the Slack API failed.",
            response=mock_response,
        ),
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    with pytest.raises(Exception) as exc_info:
        await client.add_item(
            list_id="F123",
            initial_fields=[{"column_id": "Col123", "text": "Test"}],
        )

    # Check for human-readable error message
    assert "List not found" in str(exc_info.value)
