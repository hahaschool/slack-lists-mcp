"""Tests for field normalization functionality."""

from unittest.mock import MagicMock, patch

import pytest

from slack_lists_mcp.slack_client import SlackListsClient


@pytest.fixture
def mock_slack_client():
    """Create a mock Slack client."""
    with patch("slack_lists_mcp.slack_client.WebClient") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_field_normalization_for_add_item(mock_slack_client):
    """Test field normalization when adding items."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    # Test with plain text that should be converted to rich_text
    # and select field as a single value that should be wrapped in array
    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "text": "Plain text task",  # Should be converted to rich_text
            },
            {
                "column_id": "Col456",
                "select": "OptABC",  # Should be wrapped in array
            },
            {
                "column_id": "Col789",
                "user": "U123",  # Should be wrapped in array
            },
        ],
    )

    assert result["id"] == "Rec123"

    # Verify the API was called with normalized fields
    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    # Check text was converted to rich_text
    assert "rich_text" in normalized_fields[0]
    assert "text" not in normalized_fields[0]
    assert (
        normalized_fields[0]["rich_text"][0]["elements"][0]["elements"][0]["text"]
        == "Plain text task"
    )

    # Check select was wrapped in array
    assert isinstance(normalized_fields[1]["select"], list)
    assert normalized_fields[1]["select"] == ["OptABC"]

    # Check user was wrapped in array
    assert isinstance(normalized_fields[2]["user"], list)
    assert normalized_fields[2]["user"] == ["U123"]


@pytest.mark.asyncio
async def test_field_normalization_for_update_item(mock_slack_client):
    """Test field normalization when updating items."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    # Test with plain text and single select value
    result = await client.update_item(
        list_id="F123",
        cells=[
            {
                "row_id": "Rec123",
                "column_id": "Col123",
                "text": "Updated text",  # Should be converted to rich_text
            },
            {
                "row_id": "Rec123",
                "column_id": "Col456",
                "select": "OptXYZ",  # Should be wrapped in array
            },
        ],
    )

    assert result["success"] is True

    # Verify the API was called with normalized cells
    actual_call = mock_slack_client.api_call.call_args
    normalized_cells = actual_call[1]["json"]["cells"]

    # Check text was converted to rich_text
    assert "rich_text" in normalized_cells[0]
    assert "text" not in normalized_cells[0]
    assert (
        normalized_cells[0]["rich_text"][0]["elements"][0]["elements"][0]["text"]
        == "Updated text"
    )

    # Check select was wrapped in array
    assert isinstance(normalized_cells[1]["select"], list)
    assert normalized_cells[1]["select"] == ["OptXYZ"]


@pytest.mark.asyncio
async def test_field_normalization_preserves_arrays(mock_slack_client):
    """Test that normalization doesn't modify fields already in correct format."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    # Test with fields already in correct format
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
                                "elements": [
                                    {"type": "text", "text": "Already formatted"}
                                ],
                            }
                        ],
                    }
                ],
            },
            {
                "column_id": "Col456",
                "select": ["OptABC", "OptDEF"],  # Already an array
            },
            {
                "column_id": "Col789",
                "user": ["U123", "U456"],  # Already an array
            },
        ],
    )

    assert result["id"] == "Rec123"

    # Verify the API was called with fields unchanged
    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    # Rich text should remain unchanged
    assert (
        normalized_fields[0]["rich_text"][0]["elements"][0]["elements"][0]["text"]
        == "Already formatted"
    )

    # Arrays should remain as arrays
    assert normalized_fields[1]["select"] == ["OptABC", "OptDEF"]
    assert normalized_fields[2]["user"] == ["U123", "U456"]


@pytest.mark.asyncio
async def test_field_normalization_handles_checkbox(mock_slack_client):
    """Test that checkbox fields are not modified."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "checkbox": True,  # Boolean values should remain as-is
            },
            {
                "column_id": "Col456",
                "checkbox": False,
            },
        ],
    )

    assert result["id"] == "Rec123"

    # Verify checkbox fields remain as boolean
    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    assert normalized_fields[0]["checkbox"] is True
    assert normalized_fields[1]["checkbox"] is False


@pytest.mark.asyncio
async def test_message_field_url_string_wrapped(mock_slack_client):
    """Test that a single message URL string is wrapped in an array."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "message": "https://team.slack.com/archives/C03HDDKH82J/p1770618111689629",
            },
        ],
    )

    assert result["id"] == "Rec123"

    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    assert isinstance(normalized_fields[0]["message"], list)
    assert normalized_fields[0]["message"] == [
        "https://team.slack.com/archives/C03HDDKH82J/p1770618111689629"
    ]


@pytest.mark.asyncio
async def test_message_field_structured_to_url(mock_slack_client):
    """Test that structured message objects are converted to permalink URLs."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client
    # Pre-set workspace URL to avoid auth.test call
    client._workspace_url = "https://myteam.slack.com"

    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "message": {"channel_id": "C03HDDKH82J", "ts": "1770618111.689629"},
            },
        ],
    )

    assert result["id"] == "Rec123"

    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    assert isinstance(normalized_fields[0]["message"], list)
    assert normalized_fields[0]["message"] == [
        "https://myteam.slack.com/archives/C03HDDKH82J/p1770618111689629"
    ]


@pytest.mark.asyncio
async def test_message_field_array_mixed_conversion(mock_slack_client):
    """Test that mixed arrays of URLs and structured objects are all converted."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client
    client._workspace_url = "https://myteam.slack.com"

    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "message": [
                    "https://myteam.slack.com/archives/C111/p1234567890123456",
                    {"channel_id": "C222", "ts": "9876543210.654321"},
                ],
            },
        ],
    )

    assert result["id"] == "Rec123"

    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    assert normalized_fields[0]["message"] == [
        "https://myteam.slack.com/archives/C111/p1234567890123456",
        "https://myteam.slack.com/archives/C222/p9876543210654321",
    ]


@pytest.mark.asyncio
async def test_message_field_url_array_preserved(mock_slack_client):
    """Test that a correctly formatted URL array is preserved as-is."""
    mock_slack_client.api_call = MagicMock(
        return_value={"ok": True, "item": {"id": "Rec123"}},
    )

    client = SlackListsClient()
    client.client = mock_slack_client

    url = "https://team.slack.com/archives/C03HDDKH82J/p1770618111689629"
    result = await client.add_item(
        list_id="F123",
        initial_fields=[
            {
                "column_id": "Col123",
                "message": [url],
            },
        ],
    )

    assert result["id"] == "Rec123"

    actual_call = mock_slack_client.api_call.call_args
    normalized_fields = actual_call[1]["json"]["initial_fields"]

    assert normalized_fields[0]["message"] == [url]
