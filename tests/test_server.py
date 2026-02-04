"""Tests for the Slack Lists MCP server."""

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from slack_lists_mcp.server import mcp


@pytest.mark.asyncio
async def test_server_initialization():
    """Test that the server initializes correctly."""
    assert mcp is not None
    assert mcp.name == "Slack Lists MCP Server"


@pytest.mark.asyncio
async def test_get_list_structure_tool():
    """Test the get_list_structure tool."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        # Mock the response
        mock_client.list_items = AsyncMock(
            return_value={
                "items": [{"id": "test_item"}],
            },
        )
        mock_client.get_item = AsyncMock(
            return_value={
                "list": {
                    "list_metadata": {
                        "schema": [
                            {
                                "id": "Col123",
                                "name": "Name",
                                "key": "name",
                                "type": "text",
                                "is_primary_column": True,
                            },
                        ],
                        "views": [],
                    },
                },
                "record": {},
            },
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_list_structure",
                {"list_id": "test_list"},
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            assert "structure" in result_data
            assert result_data["structure"]["list_id"] == "test_list"


@pytest.mark.asyncio
async def test_add_list_item_tool():
    """Test the add_list_item tool with correct initial_fields."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.add_item = AsyncMock(
            return_value={
                "id": "test_item_id",
                "fields": [
                    {
                        "column_id": "Col123",
                        "text": "Test Item",
                    },
                ],
            },
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "add_list_item",
                {
                    "list_id": "test_list",
                    "initial_fields": [
                        {
                            "column_id": "Col123",
                            "rich_text": [
                                {
                                    "type": "rich_text",
                                    "elements": [
                                        {
                                            "type": "rich_text_section",
                                            "elements": [
                                                {"type": "text", "text": "Test Item"},
                                            ],
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            assert "item" in result_data
            mock_client.add_item.assert_called_once()


@pytest.mark.asyncio
async def test_update_list_item_tool():
    """Test the update_list_item tool."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.update_item = AsyncMock(return_value={"success": True})

        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_list_item",
                {
                    "list_id": "test_list",
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
                                                {
                                                    "type": "text",
                                                    "text": "Updated Item",
                                                },
                                            ],
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            mock_client.update_item.assert_called_once()


@pytest.mark.asyncio
async def test_delete_list_item_tool():
    """Test the delete_list_item tool."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.delete_item = AsyncMock(return_value=True)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "delete_list_item",
                {
                    "list_id": "test_list",
                    "item_id": "test_item",
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            assert result_data["deleted"] is True
            mock_client.delete_item.assert_called_once()


@pytest.mark.asyncio
async def test_get_list_item_tool():
    """Test the get_list_item tool."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.get_item = AsyncMock(
            return_value={
                "record": {
                    "id": "test_item",
                    "fields": [
                        {"column_id": "Col123", "text": "Test Item"},
                    ],
                },
                "list": {"list_metadata": {"schema": []}},
                "subtasks": [],
            },
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_list_item",
                {
                    "list_id": "test_list",
                    "item_id": "test_item",
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            assert "item" in result_data
            mock_client.get_item.assert_called_once()


@pytest.mark.asyncio
async def test_list_items_tool():
    """Test the list_items tool without filters."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.list_items = AsyncMock(
            return_value={
                "items": [
                    {"id": "item1", "fields": []},
                    {"id": "item2", "fields": []},
                ],
                "has_more": False,
                "next_cursor": None,
                "total": 2,
            },
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_items",
                {"list_id": "test_list"},
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            assert len(result_data["items"]) == 2
            mock_client.list_items.assert_called_once()


@pytest.mark.asyncio
async def test_list_items_with_filters():
    """Test the list_items tool with filters."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.list_items = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": "item1",
                        "fields": [
                            {"key": "name", "text": "Test Task"},
                        ],
                    },
                ],
                "has_more": False,
                "next_cursor": None,
                "total": 1,
            },
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_items",
                {
                    "list_id": "test_list",
                    "filters": {"name": {"contains": "Test"}},
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            # Check that filters were passed to the client
            mock_client.list_items.assert_called_once_with(
                list_id="test_list",
                limit=20,
                cursor=None,
                archived=None,
                filters={"name": {"contains": "Test"}},
            )


@pytest.mark.asyncio
async def test_list_items_with_pagination():
    """Test the list_items tool with pagination parameters."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.list_items = AsyncMock(
            return_value={
                "items": [],
                "has_more": True,
                "next_cursor": "next_page_token",
                "total": 100,
            },
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_items",
                {
                    "list_id": "test_list",
                    "limit": 10,
                    "cursor": "page_token",
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            assert result_data["has_more"] is True
            assert result_data["next_cursor"] == "next_page_token"
            mock_client.list_items.assert_called_once_with(
                list_id="test_list",
                limit=10,
                cursor="page_token",
                archived=None,
                filters=None,
            )


@pytest.mark.asyncio
async def test_list_items_with_archived():
    """Test the list_items tool with archived parameter."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.list_items = AsyncMock(
            return_value={
                "items": [],
                "has_more": False,
                "next_cursor": None,
                "total": 0,
            },
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_items",
                {
                    "list_id": "test_list",
                    "archived": True,
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            mock_client.list_items.assert_called_once_with(
                list_id="test_list",
                limit=20,
                cursor=None,
                archived=True,
                filters=None,
            )


@pytest.mark.asyncio
async def test_get_list_info_tool():
    """Test the get_list_info tool."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.get_list = AsyncMock(
            return_value={
                "id": "test_list",
                "name": "Test List",
                "title": "Test List Title",
                "list_metadata": {
                    "schema": [],
                    "views": [],
                },
            },
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_list_info",
                {"list_id": "test_list"},
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is True
            assert "list" in result_data
            assert result_data["list"]["id"] == "test_list"
            mock_client.get_list.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in tools."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.add_item = AsyncMock(
            side_effect=Exception("API Error"),
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "add_list_item",
                {
                    "list_id": "test_list",
                    "initial_fields": [
                        {"column_id": "Col123", "text": "Test"},
                    ],
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is False
            assert "error" in result_data
            assert "API Error" in result_data["error"]


@pytest.mark.asyncio
async def test_add_list_item_schema_error_handling():
    """Test that schema documentation is suggested on format errors."""
    with patch("slack_lists_mcp.server.slack_client") as mock_client:
        mock_client.add_item = AsyncMock(
            side_effect=Exception(
                "Invalid field format: column_id 'Col123' expects rich_text format",
            ),
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "add_list_item",
                {
                    "list_id": "test_list",
                    "initial_fields": [
                        {"column_id": "Col123", "text": "Test"},
                    ],
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is False
            assert "error" in result_data
            assert "hint" in result_data
            assert "get_list_structure" in result_data["hint"]
            assert "column IDs" in result_data["hint"]


@pytest.mark.asyncio
async def test_slack_api_documentation_prompt():
    """Test the slack-api-documentation prompt."""
    async with Client(mcp) as client:
        result = await client.get_prompt("slack-api-documentation")

        assert result is not None
        assert len(result.messages) > 0

        # Check that the guide contains important information
        guide_text = result.messages[0].content.text
        assert "slackLists.items.create" in guide_text
        assert "initial_fields" in guide_text
        assert "column_id" in guide_text
        assert "rich_text" in guide_text
        assert "user" in guide_text


@pytest.mark.asyncio
async def test_default_list_id_from_env():
    """Test that tools use DEFAULT_LIST_ID from environment when list_id is not provided."""
    with patch("slack_lists_mcp.server.settings") as mock_settings:
        mock_settings.default_list_id = "default_list_123"

        with patch("slack_lists_mcp.server.slack_client") as mock_client:
            mock_client.add_item = AsyncMock(
                return_value={"id": "test_item", "fields": []},
            )

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "add_list_item",
                    {
                        "initial_fields": [
                            {"column_id": "Col123", "text": "Test Item"},
                        ],
                    },
                )

                assert result is not None
                result_data = result.data
                assert result_data["success"] is True
                # Verify that the default list ID was used
                mock_client.add_item.assert_called_once_with(
                    list_id="default_list_123",
                    initial_fields=[{"column_id": "Col123", "text": "Test Item"}],
                    duplicated_item_id=None,
                )


@pytest.mark.asyncio
async def test_missing_list_id_error():
    """Test error when list_id is not provided and DEFAULT_LIST_ID is not set."""
    with patch("slack_lists_mcp.server.settings") as mock_settings:
        mock_settings.default_list_id = None

        async with Client(mcp) as client:
            result = await client.call_tool(
                "add_list_item",
                {
                    "initial_fields": [
                        {"column_id": "Col123", "text": "Test Item"},
                    ],
                },
            )

            assert result is not None
            result_data = result.data
            assert result_data["success"] is False
            assert "list_id is required" in result_data["error"]
            assert "DEFAULT_LIST_ID environment variable" in result_data["error"]


@pytest.mark.asyncio
async def test_list_id_parameter_override():
    """Test that explicitly provided list_id overrides DEFAULT_LIST_ID."""
    with patch("slack_lists_mcp.server.settings") as mock_settings:
        mock_settings.default_list_id = "default_list_123"

        with patch("slack_lists_mcp.server.slack_client") as mock_client:
            mock_client.add_item = AsyncMock(
                return_value={"id": "test_item", "fields": []},
            )

            async with Client(mcp) as client:
                result = await client.call_tool(
                    "add_list_item",
                    {
                        "list_id": "explicit_list_456",
                        "initial_fields": [
                            {"column_id": "Col123", "text": "Test Item"},
                        ],
                    },
                )

                assert result is not None
                result_data = result.data
                assert result_data["success"] is True
                # Verify that the explicit list ID was used, not the default
                mock_client.add_item.assert_called_once_with(
                    list_id="explicit_list_456",
                    initial_fields=[{"column_id": "Col123", "text": "Test Item"}],
                    duplicated_item_id=None,
                )
