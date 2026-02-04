"""Slack Lists API client implementation."""

import asyncio
import logging
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from slack_lists_mcp.config import get_settings
from slack_lists_mcp.models import ErrorResponse

logger = logging.getLogger(__name__)

# Errors that should trigger a retry
RETRYABLE_ERRORS = frozenset({
    "rate_limited",
    "service_unavailable",
    "internal_error",
    "request_timeout",
})

# Human-readable error messages for common Slack API errors
ERROR_MESSAGES = {
    "invalid_arguments": "Invalid parameters provided. Check field formats and required values.",
    "invalid_request": "Malformed request or missing required parameters.",
    "list_not_found": "List not found. The list may have been deleted or you don't have access.",
    "item_not_found": "Item not found in the list. It may have been deleted.",
    "not_found": "Resource not found. The requested item, list, or resource doesn't exist.",
    "access_denied": "Access denied. You don't have permission to perform this action.",
    "rate_limited": "Rate limited. Too many requests - please wait and retry.",
    "ratelimited": "Rate limited. Too many requests - please wait and retry.",
    "too_many_requests": "Too many requests. Please slow down and retry.",
    "not_authed": "Authentication failed. Check your Slack bot token.",
    "invalid_auth": "Invalid authentication. The token may be revoked or invalid.",
    "account_inactive": "The Slack account is inactive or deleted.",
    "missing_scope": "Missing required OAuth scope. Check bot permissions.",
    "channel_not_found": "Channel not found or bot doesn't have access.",
    "user_not_found": "User not found in the workspace.",
    "cant_update_message": "Cannot update this item. It may be locked or archived.",
    "is_archived": "Cannot modify archived list or item.",
    "restricted_action": "This action is restricted by workspace settings.",
    "team_added_to_org": "This workspace was added to an Enterprise Grid organization.",
    "ekm_access_denied": "Access denied by Enterprise Key Management.",
    "invalid_cursor": "Invalid pagination cursor. Start from the beginning.",
    "fatal_error": "A fatal server error occurred. Please try again later.",
    "invalid_blocks": "Invalid Block Kit formatting in text fields. Check rich_text structure.",
    "failed_to_parse_block_kit": "Block Kit parsing error. Ensure rich_text follows Block Kit format.",
}


class SlackListsClient:
    """Client for interacting with Slack Lists API."""

    def __init__(self, token: str | None = None):
        """Initialize the Slack Lists client.

        Args:
            token: Slack bot token. If not provided, will use from settings.

        """
        settings = get_settings()
        self.token = token or settings.slack_bot_token_value
        self.client = WebClient(
            token=self.token,
            timeout=settings.slack_api_timeout,
        )
        self.retry_count = settings.slack_retry_count

    def _handle_api_error(self, e: SlackApiError) -> ErrorResponse:
        """Handle Slack API errors consistently.

        Args:
            e: The SlackApiError exception

        Returns:
            ErrorResponse model with error details

        """
        error_code = e.response.get("error", "Unknown error")
        # Use human-readable message if available, otherwise use error code
        error_msg = ERROR_MESSAGES.get(error_code, error_code)
        error_details = {
            "response": e.response,
            "error_code": error_code,
            "status_code": e.response.status_code
            if hasattr(e.response, "status_code")
            else None,
            "headers": dict(e.response.headers)
            if hasattr(e.response, "headers")
            else None,
        }
        logger.error(f"Slack API error: {error_code} - {error_msg}")
        return ErrorResponse(
            error=error_msg,
            error_code=error_code,
            details=error_details,
        )

    async def _call_with_retry(
        self,
        api_method: str,
        json: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an API call with retry logic for transient errors.

        Args:
            api_method: The Slack API method to call
            json: The request payload

        Returns:
            The API response

        Raises:
            SlackApiError: If the API call fails after all retries

        """
        last_exception = None
        base_delay = 1.0  # Start with 1 second delay

        for attempt in range(self.retry_count + 1):
            try:
                response = self.client.api_call(
                    api_method=api_method,
                    json=json,
                )
                return response

            except SlackApiError as e:
                error_code = e.response.get("error", "")

                # Check if this is a retryable error
                if error_code in RETRYABLE_ERRORS and attempt < self.retry_count:
                    # Calculate delay with exponential backoff
                    delay = base_delay * (2 ** attempt)

                    # For rate limiting, check if Retry-After header is provided
                    if error_code == "rate_limited":
                        retry_after = e.response.headers.get("Retry-After")
                        if retry_after:
                            delay = max(delay, float(retry_after))

                    logger.warning(
                        f"Retryable error '{error_code}' on attempt {attempt + 1}/{self.retry_count + 1}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    last_exception = e
                    continue

                # Non-retryable error or out of retries
                raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected retry loop exit")

    def _normalize_fields(self, fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize field formats for better API usability.

        Handles common format issues:
        - Wraps all array field values in arrays if not already (select, user, date, number, etc.)
        - Converts text to rich_text format

        Args:
            fields: List of field dictionaries to normalize

        Returns:
            Normalized field list

        """
        # All field types that expect array values per Slack API documentation
        array_field_types = [
            "select",
            "user",
            "date",
            "number",
            "email",
            "phone",
            "attachment",
            "message",
            "rating",
            "timestamp",
            "channel",
            "reference",
            "vote",
            "canvas",
        ]

        normalized = []
        for field in fields:
            # Create a copy to avoid mutating the original
            normalized_field = field.copy()

            # Handle all array field types - wrap single values in array
            for field_type in array_field_types:
                if field_type in normalized_field and not isinstance(
                    normalized_field[field_type],
                    list,
                ):
                    normalized_field[field_type] = [normalized_field[field_type]]

            # Handle text fields by converting to rich_text if needed
            if "text" in normalized_field and "rich_text" not in normalized_field:
                # Convert plain text to rich_text format
                text_value = normalized_field.pop("text")
                normalized_field["rich_text"] = [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [{"type": "text", "text": str(text_value)}],
                            },
                        ],
                    },
                ]

            # Handle link fields - wrap strings in proper link object format
            if "link" in normalized_field:
                link_value = normalized_field["link"]
                # If it's a string URL, convert to link object
                if isinstance(link_value, str):
                    normalized_field["link"] = [{"original_url": link_value}]
                # If it's a single dict, wrap in array
                elif isinstance(link_value, dict):
                    normalized_field["link"] = [link_value]
                # If it's a list, ensure each element is properly formatted
                elif isinstance(link_value, list):
                    formatted_links = []
                    for item in link_value:
                        if isinstance(item, str):
                            formatted_links.append({"original_url": item})
                        else:
                            formatted_links.append(item)
                    normalized_field["link"] = formatted_links

            normalized.append(normalized_field)

        return normalized

    async def add_item(
        self,
        list_id: str,
        initial_fields: list[dict[str, Any]] | None = None,
        duplicated_item_id: str | None = None,
        parent_item_id: str | None = None,
    ) -> dict[str, Any]:
        """Add a new item to a list.

        Use get_list_structure first to understand the column IDs and types.

        Args:
            list_id: The ID of the list
            initial_fields: List of field dictionaries with column_id and appropriate value format.
                           Each field should have:
                           - column_id: The column ID
                           - One of: rich_text, user, date, select, checkbox, number, email, phone, etc.
            duplicated_item_id: ID of an existing item to duplicate. When provided, creates a
                               copy of the specified item. initial_fields can be omitted.
            parent_item_id: ID of a parent item to create a subtask under. When provided,
                           the new item becomes a subtask of the specified parent.

        Returns:
            The created item data

        Example:
            # Create new item with fields
            initial_fields = [
                {
                    "column_id": "Col123",
                    "rich_text": [{
                        "type": "rich_text",
                        "elements": [{
                            "type": "rich_text_section",
                            "elements": [{"type": "text", "text": "My Task"}]
                        }]
                    }]
                },
                {
                    "column_id": "Col456",
                    "user": ["U123456"]  # user fields expect an array
                }
            ]

            # Or duplicate an existing item
            duplicated_item_id = "Rec12345678"

            # Or create a subtask under a parent item
            parent_item_id = "Rec87654321"

        """
        try:
            # Either initial_fields or duplicated_item_id must be provided
            if not initial_fields and not duplicated_item_id:
                raise ValueError(
                    "Either initial_fields or duplicated_item_id must be provided",
                )

            # Build request payload
            request_data: dict[str, Any] = {"list_id": list_id}

            # Add parent_item_id if creating a subtask
            if parent_item_id:
                request_data["parent_item_id"] = parent_item_id

            # Handle duplication case
            if duplicated_item_id:
                request_data["duplicated_item_id"] = duplicated_item_id
                logger.debug(f"Duplicating item {duplicated_item_id} in list {list_id}")
            else:
                # Validate and normalize fields only when not duplicating
                for field in initial_fields or []:
                    if "column_id" not in field:
                        raise ValueError("Each field must have a 'column_id'")
                    # All supported field types per Slack API documentation
                    supported_field_types = [
                        "text",  # Converted to rich_text by _normalize_fields
                        "rich_text",  # Rich text blocks
                        "user",  # Array of user IDs
                        "select",  # Array of option IDs
                        "checkbox",  # Boolean
                        "date",  # Array of date strings (YYYY-MM-DD)
                        "number",  # Array of numbers
                        "email",  # Array of email addresses
                        "phone",  # Array of phone numbers
                        "attachment",  # Array of file IDs
                        "link",  # Array of link objects
                        "message",  # Array of Slack message permalinks
                        "rating",  # Array of numeric ratings
                        "timestamp",  # Array of Unix timestamps
                        "channel",  # Array of channel IDs
                        "reference",  # Array of file references
                    ]
                    if not any(key in field for key in supported_field_types):
                        raise ValueError(
                            f"Field with column_id '{field.get('column_id')}' must have a value. "
                            f"Supported types: {', '.join(supported_field_types)}",
                        )

                # Normalize field formats for better usability
                normalized_fields = self._normalize_fields(initial_fields or [])
                request_data["initial_fields"] = normalized_fields
                logger.debug(
                    f"Creating item with {len(normalized_fields)} fields in list {list_id}",
                )

            response = await self._call_with_retry(
                api_method="slackLists.items.create",
                json=request_data,
            )

            if response.get("ok"):
                return response.get("item", {})
            raise SlackApiError(
                message="Failed to add item",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to add item: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error adding item: {e}")
            raise

    async def update_item(
        self,
        list_id: str,
        cells: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Update items in a list, or create new items via row_id_to_create.

        Use get_list_structure first to understand the column IDs and types.

        Args:
            list_id: The ID of the list
            cells: List of cell dictionaries. Each cell must have:
                   - row_id: The item/row ID to update (for existing rows)
                   - OR row_id_to_create: true (to create a new row)
                   - column_id: The column ID
                   - One of: rich_text, user, date, select, checkbox, number, email, phone, etc.

        Returns:
            Success indicator

        Example:
            # Update existing items
            cells = [
                {
                    "row_id": "Rec123",
                    "column_id": "Col123",
                    "rich_text": [{
                        "type": "rich_text",
                        "elements": [{
                            "type": "rich_text_section",
                            "elements": [{"type": "text", "text": "Updated Task"}]
                        }]
                    }]
                },
                {
                    "row_id": "Rec123",
                    "column_id": "Col456",
                    "checkbox": True
                }
            ]

            # Create new items using row_id_to_create
            cells = [
                {
                    "row_id_to_create": True,
                    "column_id": "Col123",
                    "text": "New Task Name"
                },
                {
                    "row_id_to_create": True,
                    "column_id": "Col456",
                    "select": ["OptABC123"]
                }
            ]

        """
        try:
            if not cells:
                raise ValueError("At least one cell must be provided")

            # Validate that each cell has either row_id or row_id_to_create
            for cell in cells:
                if "row_id" not in cell and not cell.get("row_id_to_create"):
                    raise ValueError(
                        "Each cell must have either 'row_id' or 'row_id_to_create: true'"
                    )

            # Normalize field formats for better usability
            normalized_cells = self._normalize_fields(cells)

            logger.info(
                f"Updating {len(normalized_cells)} cells in list {list_id}",
            )
            response = await self._call_with_retry(
                api_method="slackLists.items.update",
                json={
                    "list_id": list_id,
                    "cells": normalized_cells,
                },
            )

            if response.get("ok"):
                return {"success": True}
            raise SlackApiError(
                message="Failed to update items",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to update items: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error updating items: {e}")
            raise

    async def delete_item(
        self,
        list_id: str,
        item_id: str,
    ) -> dict[str, Any]:
        """Delete an item from a list.

        Args:
            list_id: The ID of the list
            item_id: The ID of the item to delete

        Returns:
            Confirmation of deletion

        """
        try:
            response = await self._call_with_retry(
                api_method="slackLists.items.delete",
                json={
                    "list_id": list_id,
                    "id": item_id,  # API expects 'id' not 'item_id'
                },
            )

            if response.get("ok"):
                return {"deleted": True, "item_id": item_id}
            raise SlackApiError(
                message="Failed to delete item",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to delete item: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error deleting item: {e}")
            raise

    async def delete_items(
        self,
        list_id: str,
        item_ids: list[str],
    ) -> dict[str, Any]:
        """Delete multiple items from a list.

        Args:
            list_id: The ID of the list
            item_ids: List of item IDs to delete

        Returns:
            Confirmation of deletion with count

        """
        try:
            if not item_ids:
                raise ValueError("At least one item ID must be provided")

            response = await self._call_with_retry(
                api_method="slackLists.items.deleteMultiple",
                json={
                    "list_id": list_id,
                    "ids": item_ids,
                },
            )

            if response.get("ok"):
                return {"deleted": True, "count": len(item_ids), "item_ids": item_ids}
            raise SlackApiError(
                message="Failed to delete items",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to delete items: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error deleting items: {e}")
            raise

    async def get_item(
        self,
        list_id: str,
        item_id: str,
        include_is_subscribed: bool = False,
    ) -> dict[str, Any]:
        """Get a specific item from a list.

        Args:
            list_id: The ID of the list
            item_id: The ID of the item
            include_is_subscribed: Whether to include subscription status

        Returns:
            The item data including list metadata and subtasks if present

        """
        try:
            params = {
                "list_id": list_id,
                "id": item_id,  # API expects 'id' not 'item_id'
            }

            if include_is_subscribed:
                params["include_is_subscribed"] = include_is_subscribed

            response = await self._call_with_retry(
                api_method="slackLists.items.info",
                json=params,
            )

            if response.get("ok"):
                # API returns 'record' not 'item'
                return {
                    "item": response.get("record", {}),
                    "list": response.get("list", {}),
                    "subtasks": response.get("subtasks", []),
                }
            raise SlackApiError(
                message="Failed to get item",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to get item: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error getting item: {e}")
            raise

    async def list_items(
        self,
        list_id: str,
        limit: int = 20,
        cursor: str | None = None,
        archived: bool | None = None,
        filters: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """List items in a list with optional filtering.

        Args:
            list_id: The ID of the list
            limit: Maximum number of items to return (default: 100)
            cursor: Pagination cursor for next page
            archived: Whether to return archived items (True) or normal items (False/None)
            filters: Dictionary of column filters. Keys are column IDs or keys, values are filter conditions.
                    Example: {
                        "name": {"contains": "タスク"},
                        "Col09HEURLL6A": {"equals": "OptRCQF2AM6"},  # ステータス
                        "todo_completed": {"equals": True},
                        "Col09H0PTP23Z": {"in": ["U123", "U456"]},  # 担当者リスト
                    }
                    Supported operators: equals, not_equals, contains, not_contains, in, not_in

        Returns:
            Dictionary with items and pagination info

        """
        try:
            # API parameters (only supported ones)
            params = {
                "list_id": list_id,
                "limit": limit * 3 if filters else limit,  # Get more items if filtering
            }

            if cursor:
                params["cursor"] = cursor
            if archived is not None:
                params["archived"] = archived

            response = await self._call_with_retry(
                api_method="slackLists.items.list",
                json=params,
            )

            if response.get("ok"):
                items = response.get("items", [])

                # Apply client-side filters if provided
                if filters:
                    filtered_items = []
                    for item in items:
                        if self._matches_filters(item, filters):
                            filtered_items.append(item)
                            if len(filtered_items) >= limit:
                                break
                    items = filtered_items

                # Extract pagination info from response_metadata (Slack API standard)
                response_metadata = response.get("response_metadata", {})
                next_cursor = response_metadata.get("next_cursor", "")
                # has_more is determined by whether next_cursor is non-empty
                has_more = bool(next_cursor)

                return {
                    "items": items,
                    "has_more": has_more,
                    "next_cursor": next_cursor if next_cursor else None,
                    "total": len(items),
                }

            raise SlackApiError(
                message="Failed to list items",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to list items: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error listing items: {e}")
            raise

    async def iter_all_items(
        self,
        list_id: str,
        limit: int = 100,
        archived: bool | None = None,
        filters: dict[str, dict[str, Any]] | None = None,
    ):
        """Iterate through all items in a list with automatic pagination.

        This is an async generator that automatically handles pagination,
        yielding items one at a time until all items have been retrieved.

        Args:
            list_id: The ID of the list
            limit: Number of items per page (default: 100)
            archived: Whether to return archived items (True) or normal items (False/None)
            filters: Dictionary of column filters (same as list_items)

        Yields:
            Individual item dictionaries

        Example:
            async for item in client.iter_all_items("F123"):
                print(item["id"])

            # With filters
            async for item in client.iter_all_items(
                "F123",
                filters={"status": {"equals": "active"}}
            ):
                process_item(item)

            # Collect all items into a list
            all_items = [item async for item in client.iter_all_items("F123")]

        """
        cursor = None

        while True:
            result = await self.list_items(
                list_id=list_id,
                limit=limit,
                cursor=cursor,
                archived=archived,
                filters=filters,
            )

            for item in result.get("items", []):
                yield item

            if not result.get("has_more"):
                break

            cursor = result.get("next_cursor")
            if not cursor:
                break

    def _matches_filters(
        self,
        item: dict[str, Any],
        filters: dict[str, dict[str, Any]],
    ) -> bool:
        """Check if an item matches all filter conditions.

        Args:
            item: The item to check
            filters: Filter conditions

        Returns:
            True if item matches all filters, False otherwise

        """
        fields = item.get("fields", [])

        for filter_key, filter_condition in filters.items():
            matched = False

            # Find matching field
            for field in fields:
                # Match by column_id or key
                if (
                    field.get("column_id") == filter_key
                    or field.get("key") == filter_key
                ):
                    field_value = self._extract_field_value(field)

                    # Apply filter condition
                    if self._apply_filter_condition(field_value, filter_condition):
                        matched = True
                        break

            # If no field matched this filter, item doesn't match
            if not matched:
                return False

        return True

    def _extract_field_value(self, field: dict[str, Any]) -> Any:
        """Extract the actual value from a field.

        Args:
            field: Field dictionary

        Returns:
            The extracted value

        """
        # Priority order for value extraction
        if "checkbox" in field:
            return field["checkbox"]
        if "select" in field:
            return field["select"]
        if "user" in field:
            return field["user"]
        if "date" in field:
            return field["date"]
        if "text" in field:
            return field["text"]
        if "number" in field:
            return field["number"]
        if "email" in field:
            return field["email"]
        if "phone" in field:
            return field["phone"]
        if "attachment" in field:
            return field["attachment"]
        if "link" in field:
            return field["link"]
        if "message" in field:
            return field["message"]
        if "rating" in field:
            return field["rating"]
        if "timestamp" in field:
            return field["timestamp"]
        if "channel" in field:
            return field["channel"]
        if "reference" in field:
            return field["reference"]
        if "vote" in field:
            return field["vote"]
        if "canvas" in field:
            return field["canvas"]
        if "rich_text" in field:
            return field["rich_text"]
        if "value" in field:
            return field["value"]
        return None

    def _apply_filter_condition(self, value: Any, condition: dict[str, Any]) -> bool:
        """Apply a filter condition to a value.

        Args:
            value: The value to check
            condition: Filter condition with operator and expected value

        Returns:
            True if value matches condition

        """
        for operator, expected in condition.items():
            if operator == "equals":
                if not self._values_equal(value, expected):
                    return False
            elif operator == "not_equals":
                if self._values_equal(value, expected):
                    return False
            elif operator == "contains":
                if not self._value_contains(value, expected):
                    return False
            elif operator == "not_contains":
                if self._value_contains(value, expected):
                    return False
            elif operator == "in":
                if not self._value_in_list(value, expected):
                    return False
            elif operator == "not_in":
                if self._value_in_list(value, expected):
                    return False

        return True

    def _values_equal(self, value: Any, expected: Any) -> bool:
        """Check if values are equal."""
        if isinstance(value, list) and len(value) == 1:
            return value[0] == expected
        return value == expected

    def _value_contains(self, value: Any, search: str) -> bool:
        """Check if value contains search string."""
        if value is None:
            return False
        if isinstance(value, str):
            return search.lower() in value.lower()
        if isinstance(value, list):
            return any(search.lower() in str(v).lower() for v in value)
        return search.lower() in str(value).lower()

    def _value_in_list(self, value: Any, expected_list: list) -> bool:
        """Check if value is in expected list."""
        if isinstance(value, list):
            return any(v in expected_list for v in value)
        return value in expected_list

    async def get_list(self, list_id: str) -> dict[str, Any]:
        """Get information about a list.

        Note: There's no direct slackLists.info API, so we use items.list with limit=1
        to get list metadata from the first item's response.

        Args:
            list_id: The ID of the list

        Returns:
            The list information

        """
        try:
            # Use list_items to get basic list info
            response = await self._call_with_retry(
                api_method="slackLists.items.list",
                json={"list_id": list_id, "limit": 1},
            )

            if response.get("ok"):
                # If we have items, try to get more detailed info
                items = response.get("items", [])
                if items:
                    # Get first item info which includes list metadata
                    item_response = await self._call_with_retry(
                        api_method="slackLists.items.info",
                        json={
                            "list_id": list_id,
                            "id": items[0]["id"],
                        },
                    )
                    if item_response.get("ok"):
                        return item_response.get("list", {})

                # No items or couldn't get item info, return basic info
                return {
                    "id": list_id,
                    "item_count": len(items),
                    "message": "List metadata not available. List may be empty.",
                }

            raise SlackApiError(
                message="Failed to get list",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to get list: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error getting list: {e}")
            raise

    async def create_list(
        self,
        name: str | None = None,
        description: str | None = None,
        todo_mode: bool | None = None,
        schema: list[dict[str, Any]] | None = None,
        copy_from_list_id: str | None = None,
        include_copied_list_records: bool | None = None,
    ) -> dict[str, Any]:
        """Create a new list.

        Args:
            name: Name of the list
            description: Optional description (converted to rich text blocks)
            todo_mode: When True, creates list with Completed, Assignee, and Due Date
                      columns for task tracking
            schema: Column definitions for the list structure. Each column should have:
                   - key: Column identifier string
                   - name: Display name for the column
                   - type: Column type (text, number, select, date, user, checkbox, etc.)
                   - is_primary_column: (optional) Set True for primary text column
                   - options: (optional) Column configuration (choices for select, etc.)
            copy_from_list_id: ID of an existing list to duplicate
            include_copied_list_records: When True and copying from another list,
                                        includes the records from that list

        Returns:
            The created list data

        Example:
            # Create a simple list with todo mode
            create_list(name="My Tasks", todo_mode=True)

            # Create a list with custom schema
            create_list(
                name="Project Tracker",
                schema=[
                    {"key": "task_name", "name": "Task", "type": "text", "is_primary_column": True},
                    {"key": "status", "name": "Status", "type": "select", "options": {
                        "choices": [
                            {"key": "todo", "value": "To Do", "color": "gray"},
                            {"key": "in_progress", "value": "In Progress", "color": "blue"},
                            {"key": "done", "value": "Done", "color": "green"}
                        ]
                    }},
                    {"key": "assignee", "name": "Assignee", "type": "user"},
                    {"key": "due", "name": "Due Date", "type": "date"}
                ]
            )

            # Duplicate an existing list with its records
            create_list(copy_from_list_id="F1234567890", include_copied_list_records=True)

        """
        try:
            list_data: dict[str, Any] = {}

            if name:
                list_data["name"] = name
            if description:
                # Convert plain text to description_blocks format
                list_data["description_blocks"] = [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [{"type": "text", "text": description}],
                            },
                        ],
                    },
                ]
            if todo_mode is not None:
                list_data["todo_mode"] = todo_mode
            if schema is not None:
                list_data["schema"] = schema
            if copy_from_list_id:
                list_data["copy_from_list_id"] = copy_from_list_id
            if include_copied_list_records is not None:
                list_data["include_copied_list_records"] = include_copied_list_records

            response = await self._call_with_retry(
                api_method="slackLists.create",
                json=list_data,
            )

            if response.get("ok"):
                return response.get("list", {})
            raise SlackApiError(
                message="Failed to create list",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to create list: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error creating list: {e}")
            raise

    async def set_access(
        self,
        list_id: str,
        access_level: str,
        user_ids: list[str] | None = None,
        channel_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Set access level for users or channels on a list.

        Args:
            list_id: The ID of the list
            access_level: Permission level - 'read', 'write', or 'owner' (users only)
            user_ids: List of user IDs to grant access (cannot use with channel_ids)
            channel_ids: List of channel IDs to grant access (cannot use with user_ids)

        Returns:
            Success indicator

        Note:
            - Cannot specify both user_ids and channel_ids in the same call
            - 'owner' access level only works with user_ids
            - Only the current owner can designate another user as owner

        """
        try:
            if not user_ids and not channel_ids:
                raise ValueError("Either user_ids or channel_ids must be provided")
            if user_ids and channel_ids:
                raise ValueError("Cannot specify both user_ids and channel_ids")
            if access_level not in ("read", "write", "owner"):
                raise ValueError("access_level must be 'read', 'write', or 'owner'")
            if access_level == "owner" and channel_ids:
                raise ValueError("'owner' access level only works with user_ids")

            request_data: dict[str, Any] = {
                "list_id": list_id,
                "access_level": access_level,
            }

            if user_ids:
                request_data["user_ids"] = user_ids
            if channel_ids:
                request_data["channel_ids"] = channel_ids

            response = await self._call_with_retry(
                api_method="slackLists.access.set",
                json=request_data,
            )

            if response.get("ok"):
                return {"success": True}
            raise SlackApiError(
                message="Failed to set access",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to set access: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error setting access: {e}")
            raise

    async def delete_access(
        self,
        list_id: str,
        user_ids: list[str] | None = None,
        channel_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Revoke access for users or channels from a list.

        Args:
            list_id: The ID of the list
            user_ids: List of user IDs to revoke access (cannot use with channel_ids)
            channel_ids: List of channel IDs to revoke access (cannot use with user_ids)

        Returns:
            Success indicator

        Note:
            Cannot specify both user_ids and channel_ids in the same call.

        """
        try:
            if not user_ids and not channel_ids:
                raise ValueError("Either user_ids or channel_ids must be provided")
            if user_ids and channel_ids:
                raise ValueError("Cannot specify both user_ids and channel_ids")

            request_data: dict[str, Any] = {"list_id": list_id}

            if user_ids:
                request_data["user_ids"] = user_ids
            if channel_ids:
                request_data["channel_ids"] = channel_ids

            response = await self._call_with_retry(
                api_method="slackLists.access.delete",
                json=request_data,
            )

            if response.get("ok"):
                return {"success": True}
            raise SlackApiError(
                message="Failed to delete access",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to delete access: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error deleting access: {e}")
            raise

    async def start_export(
        self,
        list_id: str,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        """Start an async export job for a list.

        Args:
            list_id: The ID of the list to export
            include_archived: Whether to include archived items in the export

        Returns:
            Job information including job_id for polling

        Note:
            After starting an export, use get_export_url with the job_id
            to retrieve the download URL once the job completes.

        """
        try:
            request_data: dict[str, Any] = {"list_id": list_id}

            if include_archived:
                request_data["include_archived"] = include_archived

            response = await self._call_with_retry(
                api_method="slackLists.download.start",
                json=request_data,
            )

            if response.get("ok"):
                return {
                    "job_id": response.get("job_id"),
                    "list_id": list_id,
                    "status": "started",
                }
            raise SlackApiError(
                message="Failed to start export",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to start export: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error starting export: {e}")
            raise

    async def get_export_url(
        self,
        list_id: str,
        job_id: str,
    ) -> dict[str, Any]:
        """Get the download URL for a completed export job.

        Args:
            list_id: The ID of the list
            job_id: The job ID from start_export

        Returns:
            Download URL and status information

        Note:
            The export job may still be processing. If so, retry after a short delay.

        """
        try:
            response = await self._call_with_retry(
                api_method="slackLists.download.get",
                json={
                    "list_id": list_id,
                    "job_id": job_id,
                },
            )

            if response.get("ok"):
                return {
                    "download_url": response.get("download_url"),
                    "job_id": job_id,
                    "list_id": list_id,
                    "status": "completed" if response.get("download_url") else "processing",
                }
            raise SlackApiError(
                message="Failed to get export URL",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to get export URL: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error getting export URL: {e}")
            raise

    async def wait_for_export(
        self,
        list_id: str,
        job_id: str,
        timeout: int = 60,
        poll_interval: float = 2.0,
    ) -> dict[str, Any]:
        """Wait for an export job to complete and return the download URL.

        This method polls the export status until it's ready or times out.

        Args:
            list_id: The ID of the list
            job_id: The job ID from start_export
            timeout: Maximum time to wait in seconds (default: 60)
            poll_interval: Time between status checks in seconds (default: 2.0)

        Returns:
            Export result with download_url if successful

        Raises:
            TimeoutError: If the export doesn't complete within the timeout
            Exception: If the export fails

        Example:
            # Start export and wait for completion
            start_result = await client.start_export(list_id="F123")
            export = await client.wait_for_export(
                list_id="F123",
                job_id=start_result["job_id"],
                timeout=120  # Wait up to 2 minutes
            )
            print(export["download_url"])

        """
        import time

        start_time = time.time()

        while True:
            result = await self.get_export_url(list_id=list_id, job_id=job_id)

            if result.get("status") == "completed" and result.get("download_url"):
                return result

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(
                    f"Export job {job_id} did not complete within {timeout} seconds. "
                    f"Last status: {result.get('status')}"
                )

            # Wait before next poll
            await asyncio.sleep(poll_interval)

    async def update_list(
        self,
        list_id: str,
        name: str | None = None,
        description: str | None = None,
        todo_mode: bool | None = None,
    ) -> dict[str, Any]:
        """Update a list's properties.

        Args:
            list_id: The ID of the list to update
            name: New name for the list
            description: New description for the list
            todo_mode: Enable/disable todo mode (adds Completed, Assignee, Due date columns)

        Returns:
            Success indicator

        """
        try:
            update_data: dict[str, Any] = {"id": list_id}

            if name is not None:
                update_data["name"] = name
            if description is not None:
                # Convert plain text to description_blocks format
                update_data["description_blocks"] = [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [{"type": "text", "text": description}],
                            },
                        ],
                    },
                ]
            if todo_mode is not None:
                update_data["todo_mode"] = todo_mode

            # Check if any update fields provided
            if len(update_data) == 1:  # Only has 'id'
                raise ValueError(
                    "At least one of name, description, or todo_mode must be provided",
                )

            response = await self._call_with_retry(
                api_method="slackLists.update",
                json=update_data,
            )

            if response.get("ok"):
                return {"success": True}
            raise SlackApiError(
                message="Failed to update list",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to update list: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error updating list: {e}")
            raise

    async def delete_list(
        self,
        list_id: str,
    ) -> dict[str, Any]:
        """Delete an entire list.

        WARNING: This permanently deletes the list and all its items.
        This action cannot be undone.

        Args:
            list_id: The ID of the list to delete

        Returns:
            Confirmation of deletion

        """
        try:
            response = await self._call_with_retry(
                api_method="slackLists.delete",
                json={"id": list_id},
            )

            if response.get("ok"):
                return {"deleted": True, "list_id": list_id}
            raise SlackApiError(
                message="Failed to delete list",
                response=response,
            )

        except SlackApiError as e:
            error_response = self._handle_api_error(e)
            raise Exception(f"Failed to delete list: {error_response.error}")
        except Exception as e:
            logger.error(f"Unexpected error deleting list: {e}")
            raise


# Create a singleton instance
slack_client = SlackListsClient()
