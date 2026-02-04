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


@pytest.mark.asyncio
async def test_create_list_with_todo_mode(mock_slack_client):
    """Test creating a list with todo mode enabled."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "list": {
                "id": "F123",
                "name": "My Tasks",
            },
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.create_list(
        name="My Tasks",
        todo_mode=True,
    )

    assert result["id"] == "F123"
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.create",
        json={
            "name": "My Tasks",
            "todo_mode": True,
        },
    )


@pytest.mark.asyncio
async def test_create_list_with_schema(mock_slack_client):
    """Test creating a list with custom schema."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "list": {
                "id": "F123",
                "name": "Custom List",
            },
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    schema = [
        {"key": "task", "name": "Task", "type": "text", "is_primary_column": True},
        {"key": "status", "name": "Status", "type": "select"},
    ]

    result = await client.create_list(
        name="Custom List",
        schema=schema,
    )

    assert result["id"] == "F123"
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.create",
        json={
            "name": "Custom List",
            "schema": schema,
        },
    )


@pytest.mark.asyncio
async def test_create_list_copy_from_existing(mock_slack_client):
    """Test duplicating an existing list."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "list": {
                "id": "F456",
                "name": "Copied List",
            },
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.create_list(
        copy_from_list_id="F123",
        include_copied_list_records=True,
    )

    assert result["id"] == "F456"
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.create",
        json={
            "copy_from_list_id": "F123",
            "include_copied_list_records": True,
        },
    )


@pytest.mark.asyncio
async def test_set_access_for_users(mock_slack_client):
    """Test setting access for users."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.set_access(
        list_id="F123",
        access_level="write",
        user_ids=["U123", "U456"],
    )

    assert result["success"] is True
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.access.set",
        json={
            "list_id": "F123",
            "access_level": "write",
            "user_ids": ["U123", "U456"],
        },
    )


@pytest.mark.asyncio
async def test_set_access_for_channels(mock_slack_client):
    """Test setting access for channels."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.set_access(
        list_id="F123",
        access_level="read",
        channel_ids=["C123"],
    )

    assert result["success"] is True
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.access.set",
        json={
            "list_id": "F123",
            "access_level": "read",
            "channel_ids": ["C123"],
        },
    )


@pytest.mark.asyncio
async def test_set_access_validation_errors(mock_slack_client):
    """Test set_access validation errors."""
    client = SlackListsClient()
    client.client = mock_slack_client

    # Neither user_ids nor channel_ids provided
    with pytest.raises(ValueError) as exc_info:
        await client.set_access(list_id="F123", access_level="read")
    assert "Either user_ids or channel_ids must be provided" in str(exc_info.value)

    # Both user_ids and channel_ids provided
    with pytest.raises(ValueError) as exc_info:
        await client.set_access(
            list_id="F123",
            access_level="read",
            user_ids=["U123"],
            channel_ids=["C123"],
        )
    assert "Cannot specify both user_ids and channel_ids" in str(exc_info.value)

    # Invalid access level
    with pytest.raises(ValueError) as exc_info:
        await client.set_access(
            list_id="F123",
            access_level="invalid",
            user_ids=["U123"],
        )
    assert "access_level must be" in str(exc_info.value)

    # Owner access with channels
    with pytest.raises(ValueError) as exc_info:
        await client.set_access(
            list_id="F123",
            access_level="owner",
            channel_ids=["C123"],
        )
    assert "'owner' access level only works with user_ids" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_access_for_users(mock_slack_client):
    """Test deleting access for users."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.delete_access(
        list_id="F123",
        user_ids=["U123", "U456"],
    )

    assert result["success"] is True
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.access.delete",
        json={
            "list_id": "F123",
            "user_ids": ["U123", "U456"],
        },
    )


@pytest.mark.asyncio
async def test_delete_access_validation_errors(mock_slack_client):
    """Test delete_access validation errors."""
    client = SlackListsClient()
    client.client = mock_slack_client

    # Neither user_ids nor channel_ids provided
    with pytest.raises(ValueError) as exc_info:
        await client.delete_access(list_id="F123")
    assert "Either user_ids or channel_ids must be provided" in str(exc_info.value)

    # Both user_ids and channel_ids provided
    with pytest.raises(ValueError) as exc_info:
        await client.delete_access(
            list_id="F123",
            user_ids=["U123"],
            channel_ids=["C123"],
        )
    assert "Cannot specify both user_ids and channel_ids" in str(exc_info.value)


@pytest.mark.asyncio
async def test_start_export(mock_slack_client):
    """Test starting a list export job."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "job_id": "LeF123456",
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.start_export(
        list_id="F123",
        include_archived=True,
    )

    assert result["job_id"] == "LeF123456"
    assert result["status"] == "started"
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.download.start",
        json={
            "list_id": "F123",
            "include_archived": True,
        },
    )


@pytest.mark.asyncio
async def test_get_export_url_completed(mock_slack_client):
    """Test getting export URL when job is completed."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "download_url": "https://files.slack.com/download/...",
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.get_export_url(
        list_id="F123",
        job_id="LeF123456",
    )

    assert result["download_url"] == "https://files.slack.com/download/..."
    assert result["status"] == "completed"
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.download.get",
        json={
            "list_id": "F123",
            "job_id": "LeF123456",
        },
    )


@pytest.mark.asyncio
async def test_get_export_url_processing(mock_slack_client):
    """Test getting export URL when job is still processing."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "download_url": None,
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.get_export_url(
        list_id="F123",
        job_id="LeF123456",
    )

    assert result["download_url"] is None
    assert result["status"] == "processing"


@pytest.mark.asyncio
async def test_update_list(mock_slack_client):
    """Test updating list properties."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.update_list(
        list_id="F123",
        name="New Name",
        description="New description",
        todo_mode=True,
    )

    assert result["success"] is True
    call_args = mock_slack_client.api_call.call_args
    assert call_args[1]["api_method"] == "slackLists.update"
    assert call_args[1]["json"]["id"] == "F123"
    assert call_args[1]["json"]["name"] == "New Name"
    assert call_args[1]["json"]["todo_mode"] is True


@pytest.mark.asyncio
async def test_update_list_validation_error(mock_slack_client):
    """Test update_list requires at least one field."""
    client = SlackListsClient()
    client.client = mock_slack_client

    with pytest.raises(ValueError) as exc_info:
        await client.update_list(list_id="F123")
    assert "At least one of name, description, or todo_mode must be provided" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_add_item_with_duplication(mock_slack_client):
    """Test adding an item by duplicating an existing one."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "item": {
                "id": "Rec456",
                "list_id": "F123",
            },
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.add_item(
        list_id="F123",
        duplicated_item_id="Rec123",
    )

    assert result["id"] == "Rec456"
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.items.create",
        json={
            "list_id": "F123",
            "duplicated_item_id": "Rec123",
        },
    )


@pytest.mark.asyncio
async def test_add_item_with_parent(mock_slack_client):
    """Test adding an item as a subtask."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "item": {
                "id": "Rec456",
                "list_id": "F123",
            },
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.add_item(
        list_id="F123",
        initial_fields=[{"column_id": "Col123", "text": "Subtask"}],
        parent_item_id="Rec123",
    )

    assert result["id"] == "Rec456"
    call_args = mock_slack_client.api_call.call_args
    assert call_args[1]["json"]["parent_item_id"] == "Rec123"


@pytest.mark.asyncio
async def test_add_item_validation_errors(mock_slack_client):
    """Test add_item validation errors."""
    client = SlackListsClient()
    client.client = mock_slack_client

    # Neither initial_fields nor duplicated_item_id provided
    with pytest.raises(ValueError) as exc_info:
        await client.add_item(list_id="F123")
    assert "Either initial_fields or duplicated_item_id must be provided" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_delete_items_batch(mock_slack_client):
    """Test deleting multiple items at once."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.delete_items(
        list_id="F123",
        item_ids=["Rec1", "Rec2", "Rec3"],
    )

    assert result["deleted"] is True
    assert result["count"] == 3
    mock_slack_client.api_call.assert_called_once_with(
        api_method="slackLists.items.deleteMultiple",
        json={
            "list_id": "F123",
            "ids": ["Rec1", "Rec2", "Rec3"],
        },
    )


@pytest.mark.asyncio
async def test_delete_items_validation_error(mock_slack_client):
    """Test delete_items requires at least one item."""
    client = SlackListsClient()
    client.client = mock_slack_client

    with pytest.raises(ValueError) as exc_info:
        await client.delete_items(list_id="F123", item_ids=[])
    assert "At least one item ID must be provided" in str(exc_info.value)


@pytest.mark.asyncio
async def test_link_field_normalization():
    """Test link field normalization."""
    client = SlackListsClient()

    # Test string URL normalization
    fields = [{"column_id": "Col1", "link": "https://example.com"}]
    normalized = client._normalize_fields(fields)
    assert normalized[0]["link"] == [{"original_url": "https://example.com"}]

    # Test dict normalization
    fields = [{"column_id": "Col1", "link": {"original_url": "https://example.com"}}]
    normalized = client._normalize_fields(fields)
    assert normalized[0]["link"] == [{"original_url": "https://example.com"}]

    # Test mixed list normalization
    fields = [
        {
            "column_id": "Col1",
            "link": [
                "https://example1.com",
                {"original_url": "https://example2.com"},
            ],
        }
    ]
    normalized = client._normalize_fields(fields)
    assert normalized[0]["link"] == [
        {"original_url": "https://example1.com"},
        {"original_url": "https://example2.com"},
    ]


@pytest.mark.asyncio
async def test_iter_all_items_single_page(mock_slack_client):
    """Test iterating items when all fit in one page."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "items": [
                {"id": "Rec1", "fields": []},
                {"id": "Rec2", "fields": []},
            ],
            "response_metadata": {"next_cursor": ""},
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    items = [item async for item in client.iter_all_items("F123")]

    assert len(items) == 2
    assert items[0]["id"] == "Rec1"
    assert items[1]["id"] == "Rec2"
    mock_slack_client.api_call.assert_called_once()


@pytest.mark.asyncio
async def test_iter_all_items_multiple_pages(mock_slack_client):
    """Test iterating items across multiple pages."""
    # Setup mock to return two pages
    mock_slack_client.api_call = MagicMock(
        side_effect=[
            {
                "ok": True,
                "items": [{"id": "Rec1"}, {"id": "Rec2"}],
                "response_metadata": {"next_cursor": "cursor_page_2"},
            },
            {
                "ok": True,
                "items": [{"id": "Rec3"}, {"id": "Rec4"}],
                "response_metadata": {"next_cursor": ""},
            },
        ],
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    items = [item async for item in client.iter_all_items("F123", limit=2)]

    assert len(items) == 4
    assert [item["id"] for item in items] == ["Rec1", "Rec2", "Rec3", "Rec4"]
    assert mock_slack_client.api_call.call_count == 2


@pytest.mark.asyncio
async def test_iter_all_items_empty_list(mock_slack_client):
    """Test iterating an empty list."""
    mock_slack_client.api_call = MagicMock(
        return_value={
            "ok": True,
            "items": [],
            "response_metadata": {"next_cursor": ""},
        },
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    items = [item async for item in client.iter_all_items("F123")]

    assert len(items) == 0
    mock_slack_client.api_call.assert_called_once()
