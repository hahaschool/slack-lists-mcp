"""FastMCP server for Slack Lists API operations."""

import logging
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

from slack_lists_mcp.config import get_settings
from slack_lists_mcp.slack_client import SlackListsClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Configure logging level from settings
logging.getLogger().setLevel(getattr(logging, settings.log_level.upper()))

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.mcp_server_name,
    version=settings.mcp_server_version,
)

# Initialize Slack client
slack_client = SlackListsClient()


@mcp.tool
async def add_list_item(
    initial_fields: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description=(
                "List of field dictionaries. Each field MUST have "
                "'column_id' and a value field. "
                "Supported value fields: 'text' (string), "
                "'user' (list of user IDs), "
                "'date' (list of date strings), "
                "'select' (list of option IDs), "
                "'checkbox' (boolean), 'number' (list of numbers), "
                "'message' (Slack permalink URL string or "
                "{'channel_id': 'C...', 'ts': '123.456'} object - "
                "auto-converted to URL), etc. "
                "Use get_list_structure to find correct column IDs. "
                "Example: [{'column_id': 'Col123', 'text': 'Task name'}, "
                "{'column_id': 'Col456', 'user': ['U123456']}, "
                "{'column_id': 'Col789', 'message': "
                "['https://team.slack.com/archives/C123/p1234567890']}]. "
                "Can be omitted when using duplicated_item_id."
            ),
        ),
    ] = None,
    duplicated_item_id: Annotated[
        str | None,
        Field(
            description=(
                "ID of an existing item to duplicate. When provided, creates a "
                "copy of the specified item. initial_fields can be omitted."
            ),
        ),
    ] = None,
    parent_item_id: Annotated[
        str | None,
        Field(
            description=(
                "ID of a parent item to create a subtask under. When provided, "
                "the new item becomes a subtask of the specified parent."
            ),
        ),
    ] = None,
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Add a new item to a Slack list.

    IMPORTANT: Use get_list_structure first to understand the correct column IDs and field formats.

    Args:
        initial_fields: List of field dictionaries. Each field needs:
                       - column_id: The column ID (get from get_list_structure)
                       - Value in appropriate format (text, rich_text, user, date, select, checkbox, etc.)
                       Can be omitted when using duplicated_item_id.
        duplicated_item_id: ID of an existing item to duplicate. Creates a copy of the item.
        parent_item_id: ID of a parent item to create a subtask under.
        list_id: The ID of the list (optional, uses DEFAULT_LIST_ID env var if not provided)
                 When DEFAULT_LIST_ID is set, you can omit this parameter entirely
        ctx: FastMCP context (automatically injected)

    Returns:
        The created item or error information

    Example:
        # Create new item with fields
        initial_fields = [
            {"column_id": "Col08N4PWM7PZ", "text": "Task name"},
            {"column_id": "Col08NWP011DF", "user": ["U123456"]}
        ]

        # Or duplicate an existing item
        duplicated_item_id = "Rec12345678"

        # Or create a subtask under a parent
        parent_item_id = "Rec87654321"

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        # Validate that either initial_fields or duplicated_item_id is provided
        if not initial_fields and not duplicated_item_id:
            return {
                "success": False,
                "error": "Either initial_fields or duplicated_item_id must be provided",
            }

        if ctx:
            if duplicated_item_id:
                await ctx.info(f"Duplicating item {duplicated_item_id} in list {list_id}")
            elif parent_item_id:
                await ctx.info(f"Creating subtask under {parent_item_id} in list {list_id}")
            else:
                await ctx.info(
                    f"Adding item to list {list_id} with {len(initial_fields or [])} fields",
                )

        result = await slack_client.add_item(
            list_id=list_id,
            initial_fields=initial_fields,
            duplicated_item_id=duplicated_item_id,
            parent_item_id=parent_item_id,
        )

        if ctx:
            await ctx.info(f"Successfully added item to list {list_id}")

        return {
            "success": True,
            "item": result,
        }

    except Exception as e:
        logger.error(f"Error adding item: {e}")
        if ctx:
            await ctx.error(f"Failed to add item: {e!s}")
        return {
            "success": False,
            "error": str(e),
            "hint": "Use get_list_structure first to understand the correct column IDs and field formats",
        }


@mcp.tool
async def update_list_item(
    cells: Annotated[
        list[dict[str, Any]],
        Field(
            description=(
                "List of cell dictionaries. Each cell MUST have either "
                "'row_id' (to update existing) OR 'row_id_to_create: true' (to create new), "
                "plus 'column_id' and a value field. "
                "Supported value fields: 'text' (string), "
                "'user' (list of user IDs), "
                "'date' (list of date strings), "
                "'select' (list of option IDs), "
                "'checkbox' (boolean), 'number' (list of numbers), "
                "'message' (Slack permalink URL string or "
                "{'channel_id': 'C...', 'ts': '123.456'} object - "
                "auto-converted to URL), etc. "
                "Use get_list_structure to find correct column IDs. "
                "Example update: [{'row_id': 'Rec123', 'column_id': 'Col123', 'text': 'Updated name'}]. "
                "Example create: [{'row_id_to_create': true, 'column_id': 'Col123', 'text': 'New item'}]"
            ),
            min_length=1,
        ),
    ],
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update items in a Slack list, or create new items via row_id_to_create.

    Use get_list_structure first to understand the column IDs and types.

    Args:
        cells: List of cell dictionaries. Each cell needs:
               - row_id: The item ID to update (for existing items)
               - OR row_id_to_create: true (to create a new item)
               - column_id: The column ID
               - Value in appropriate format (rich_text, user, date, select, checkbox, etc.)
        list_id: The ID of the list (optional, uses DEFAULT_LIST_ID env var if not provided)
                 When DEFAULT_LIST_ID is set, you can omit this parameter entirely
        ctx: FastMCP context (automatically injected)

    Returns:
        Success status or error information

    Example:
        # Update existing item
        cells = [{"row_id": "Rec123", "column_id": "Col456", "text": "Updated value"}]

        # Create new item via update endpoint
        cells = [{"row_id_to_create": true, "column_id": "Col456", "text": "New item"}]

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Updating items in list {list_id} with {len(cells)} cells")

        result = await slack_client.update_item(
            list_id=list_id,
            cells=cells,
        )

        if ctx:
            await ctx.info(f"Successfully updated items in list {list_id}")

        return result

    except Exception as e:
        logger.error(f"Error updating items: {e}")
        if ctx:
            await ctx.error(f"Failed to update items: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def delete_list_item(
    item_id: str,
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete an item from a Slack list.

    Args:
        item_id: The ID of the item to delete
        list_id: The ID of the list containing the item (optional, uses DEFAULT_LIST_ID env var if not provided)
        ctx: FastMCP context (automatically injected)

    Returns:
        Deletion confirmation or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Deleting item {item_id} from list {list_id}")

        await slack_client.delete_item(
            list_id=list_id,
            item_id=item_id,
        )

        if ctx:
            await ctx.info(f"Successfully deleted item {item_id}")

        return {
            "success": True,
            "deleted": True,
            "item_id": item_id,
            "list_id": list_id,
        }

    except Exception as e:
        logger.error(f"Error deleting list item: {e}")
        if ctx:
            await ctx.error(f"Failed to delete item: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def delete_list_items(
    item_ids: Annotated[
        list[str],
        Field(
            description="List of item IDs to delete",
            min_length=1,
        ),
    ],
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete multiple items from a Slack list.

    More efficient than calling delete_list_item multiple times.

    Args:
        item_ids: List of item IDs to delete
        list_id: The ID of the list containing the items (optional, uses DEFAULT_LIST_ID env var if not provided)
        ctx: FastMCP context (automatically injected)

    Returns:
        Deletion confirmation with count or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Deleting {len(item_ids)} items from list {list_id}")

        result = await slack_client.delete_items(
            list_id=list_id,
            item_ids=item_ids,
        )

        if ctx:
            await ctx.info(f"Successfully deleted {len(item_ids)} items")

        return {
            "success": True,
            "deleted": True,
            "count": len(item_ids),
            "item_ids": item_ids,
            "list_id": list_id,
        }

    except Exception as e:
        logger.error(f"Error deleting list items: {e}")
        if ctx:
            await ctx.error(f"Failed to delete items: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def get_list_item(
    item_id: str,
    list_id: str | None = None,
    ctx: Context = None,
    include_is_subscribed: bool = False,
) -> dict[str, Any]:
    """Get a specific item from a Slack list.

    Args:
        item_id: The ID of the item to retrieve
        list_id: The ID of the list containing the item (optional, uses DEFAULT_LIST_ID env var if not provided)
        include_is_subscribed: Whether to include subscription status
        ctx: FastMCP context (automatically injected)

    Returns:
        The item data including list metadata and subtasks or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Retrieving item {item_id} from list {list_id}")

        result = await slack_client.get_item(
            list_id=list_id,
            item_id=item_id,
            include_is_subscribed=include_is_subscribed,
        )

        if ctx:
            await ctx.info(f"Successfully retrieved item {item_id}")

        return {
            "success": True,
            "item": result.get("item", {}),
            "list_metadata": result.get("list", {}).get("list_metadata", {}),
            "subtasks": result.get("subtasks", []),
        }

    except Exception as e:
        logger.error(f"Error getting list item: {e}")
        if ctx:
            await ctx.error(f"Failed to get item: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def list_items(
    list_id: str | None = None,
    limit: int | None = 20,
    cursor: str | None = None,
    archived: bool | None = None,
    filters: dict[str, dict[str, Any]] | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """List all items in a Slack list with optional filtering.

    Args:
        list_id: The ID of the list to retrieve items from (optional, uses DEFAULT_LIST_ID env var if not provided)
        limit: Maximum number of items to return (default: 20)
        cursor: Pagination cursor for next page
        archived: Whether to return archived items (True) or normal items (False/None)
        filters: Column filters. Keys are column IDs or keys, values are filter conditions.
                Supported operators: equals, not_equals, contains, not_contains, in, not_in
        ctx: FastMCP context (automatically injected)

    Returns:
        List of items with pagination info or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            filter_desc = f" with {len(filters)} filters" if filters else ""
            await ctx.info(f"Listing items from list {list_id}{filter_desc}")

        response = await slack_client.list_items(
            list_id=list_id,
            limit=limit or 20,
            cursor=cursor,
            archived=archived,
            filters=filters,
        )

        if ctx:
            await ctx.info(
                f"Retrieved {len(response.get('items', []))} items from list {list_id}",
            )

        return {
            "success": True,
            "items": response.get("items", []),
            "has_more": response.get("has_more", False),
            "next_cursor": response.get("next_cursor"),
            "total": response.get("total"),
        }

    except Exception as e:
        logger.error(f"Error listing items: {e}")
        if ctx:
            await ctx.error(f"Failed to list items: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def get_list_info(
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get information about a Slack list.

    Args:
        list_id: The ID of the list (optional, uses DEFAULT_LIST_ID env var if not provided)
        ctx: FastMCP context (automatically injected)

    Returns:
        The list information or error information

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Retrieving information for list {list_id}")

        result = await slack_client.get_list(list_id=list_id)

        if ctx:
            await ctx.info("Successfully retrieved list information")

        return {
            "success": True,
            "list": result,
        }

    except Exception as e:
        logger.error(f"Error getting list info: {e}")
        if ctx:
            await ctx.error(f"Failed to get list info: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def get_list_structure(
    list_id: str | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Get the structure and column information of a Slack list.

    Args:
        list_id: The ID of the list (optional, uses DEFAULT_LIST_ID env var if not provided)
        ctx: FastMCP context (automatically injected)

    Returns:
        The list structure including columns and their configurations

    """
    try:
        # Use default list ID from environment if not provided
        if list_id is None:
            list_id = settings.default_list_id
            if list_id is None:
                return {
                    "success": False,
                    "error": "list_id is required. Either provide it as parameter or set DEFAULT_LIST_ID environment variable.",
                }

        if ctx:
            await ctx.info(f"Analyzing structure for list {list_id}")

        # Get list items to find any item ID, then use items.info to get schema
        items_response = await slack_client.list_items(
            list_id=list_id,
            limit=1,  # We just need one item to get the schema
        )

        # If we have any item, use items.info to get the full schema
        if items_response.get("items") and len(items_response["items"]) > 0:
            first_item = items_response["items"][0]
            item_id = first_item.get("id")

            # Get item info which includes list metadata with schema
            item_info_response = await slack_client.get_item(
                list_id=list_id,
                item_id=item_id,
            )

            # Extract schema from list metadata
            list_data = item_info_response.get("list", {})
            list_metadata = list_data.get("list_metadata", {})
            schema = list_metadata.get("schema", [])

            # Build column mapping from schema
            columns = {}
            for column in schema:
                col_id = column.get("id")
                if col_id:
                    columns[col_id] = {
                        "id": col_id,
                        "name": column.get("name"),
                        "key": column.get("key"),
                        "type": column.get("type"),
                        "is_primary": column.get("is_primary_column", False),
                        "options": column.get("options", {}),
                    }

            # Find the name/title column
            name_column = None
            for col_id, col_info in columns.items():
                if col_info.get("is_primary") or col_info.get("key") in [
                    "name",
                    "title",
                    "todo_name",
                ]:
                    name_column = col_id
                    break

            if ctx:
                await ctx.info(f"Found {len(columns)} columns in list schema")

            return {
                "success": True,
                "structure": {
                    "list_id": list_id,
                    "metadata": {
                        "name": list_data.get("name", "Unknown"),
                        "title": list_data.get("title", "Unknown"),
                        "description": list_metadata.get("description", ""),
                    },
                    "schema": schema,
                    "columns": columns,
                    "name_column": name_column,
                    "views": list_metadata.get("views", []),
                    "todo_mode": list_metadata.get("todo_mode", False),
                },
            }
        # No items in the list, try to get basic info
        if ctx:
            await ctx.info("List has no items, returning basic structure")

        return {
            "success": True,
            "structure": {
                "list_id": list_id,
                "message": "List is empty. Add items to see full structure.",
                "columns": {},
            },
        }

    except Exception as e:
        logger.error(f"Error getting list structure: {e}")
        if ctx:
            await ctx.error(f"Failed to get list structure: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def create_list(
    name: Annotated[
        str | None,
        Field(description="Name of the list to create"),
    ] = None,
    description: Annotated[
        str | None,
        Field(description="Optional description for the list"),
    ] = None,
    todo_mode: Annotated[
        bool | None,
        Field(
            description=(
                "When True, creates list with Completed, Assignee, and Due Date "
                "columns for task tracking"
            ),
        ),
    ] = None,
    schema: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description=(
                "Column definitions for the list. Each column should have: "
                "key (string), name (string), type (text/number/select/date/user/checkbox/etc.), "
                "is_primary_column (optional bool), options (optional dict for select choices, etc.). "
                "Example: [{'key': 'task', 'name': 'Task', 'type': 'text', 'is_primary_column': True}]"
            ),
        ),
    ] = None,
    copy_from_list_id: Annotated[
        str | None,
        Field(description="ID of an existing list to duplicate"),
    ] = None,
    include_copied_list_records: Annotated[
        bool | None,
        Field(description="When True and copying, includes records from the source list"),
    ] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Create a new Slack list.

    Args:
        name: Name of the list to create
        description: Optional description for the list
        todo_mode: When True, creates with Completed, Assignee, Due Date columns
        schema: Column definitions for custom list structure
        copy_from_list_id: ID of list to duplicate
        include_copied_list_records: Include records when copying
        ctx: FastMCP context (automatically injected)

    Returns:
        The created list data or error information

    Example:
        # Simple todo list
        create_list(name="My Tasks", todo_mode=True)

        # Custom schema
        create_list(
            name="Projects",
            schema=[
                {"key": "name", "name": "Name", "type": "text", "is_primary_column": True},
                {"key": "status", "name": "Status", "type": "select"}
            ]
        )

        # Duplicate existing list
        create_list(copy_from_list_id="F1234567890", include_copied_list_records=True)

    """
    try:
        if ctx:
            if copy_from_list_id:
                await ctx.info(f"Duplicating list {copy_from_list_id}")
            else:
                await ctx.info(f"Creating list '{name or 'Unnamed'}'")

        result = await slack_client.create_list(
            name=name,
            description=description,
            todo_mode=todo_mode,
            schema=schema,
            copy_from_list_id=copy_from_list_id,
            include_copied_list_records=include_copied_list_records,
        )

        if ctx:
            await ctx.info(f"Successfully created list: {result.get('id', 'unknown')}")

        return {
            "success": True,
            "list": result,
        }

    except Exception as e:
        logger.error(f"Error creating list: {e}")
        if ctx:
            await ctx.error(f"Failed to create list: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def update_list(
    list_id: Annotated[
        str,
        Field(description="The ID of the list to update"),
    ],
    name: Annotated[
        str | None,
        Field(description="New name for the list"),
    ] = None,
    description: Annotated[
        str | None,
        Field(description="New description for the list"),
    ] = None,
    todo_mode: Annotated[
        bool | None,
        Field(
            description="Enable/disable todo mode. When enabled, adds Completed, Assignee, and Due date columns.",
        ),
    ] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Update a Slack list's properties.

    Args:
        list_id: The ID of the list to update
        name: New name for the list
        description: New description for the list
        todo_mode: Enable/disable todo mode
        ctx: FastMCP context (automatically injected)

    Returns:
        Success status or error information

    """
    try:
        if name is None and description is None and todo_mode is None:
            return {
                "success": False,
                "error": "At least one of name, description, or todo_mode must be provided",
            }

        if ctx:
            await ctx.info(f"Updating list {list_id}")

        result = await slack_client.update_list(
            list_id=list_id,
            name=name,
            description=description,
            todo_mode=todo_mode,
        )

        if ctx:
            await ctx.info(f"Successfully updated list {list_id}")

        return {
            "success": True,
            "list_id": list_id,
        }

    except Exception as e:
        logger.error(f"Error updating list: {e}")
        if ctx:
            await ctx.error(f"Failed to update list: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def delete_list(
    list_id: Annotated[
        str,
        Field(description="The ID of the list to delete"),
    ],
    ctx: Context = None,
) -> dict[str, Any]:
    """Delete an entire Slack list.

    WARNING: This permanently deletes the list and all its items.
    This action cannot be undone.

    Args:
        list_id: The ID of the list to delete
        ctx: FastMCP context (automatically injected)

    Returns:
        Deletion confirmation or error information

    """
    try:
        if ctx:
            await ctx.warning(f"Deleting list {list_id} - this cannot be undone!")

        result = await slack_client.delete_list(list_id=list_id)

        if ctx:
            await ctx.info(f"Successfully deleted list {list_id}")

        return {
            "success": True,
            "deleted": True,
            "list_id": list_id,
        }

    except Exception as e:
        logger.error(f"Error deleting list: {e}")
        if ctx:
            await ctx.error(f"Failed to delete list: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def set_list_access(
    list_id: Annotated[
        str,
        Field(description="The ID of the list to set access for"),
    ],
    access_level: Annotated[
        str,
        Field(
            description="Permission level: 'read' (view only), 'write' (view and edit), or 'owner' (full control, users only)",
        ),
    ],
    user_ids: Annotated[
        list[str] | None,
        Field(description="List of user IDs to grant access (cannot use with channel_ids)"),
    ] = None,
    channel_ids: Annotated[
        list[str] | None,
        Field(description="List of channel IDs to grant access (cannot use with user_ids)"),
    ] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Set access level for users or channels on a Slack list.

    Args:
        list_id: The ID of the list
        access_level: Permission level - 'read', 'write', or 'owner'
        user_ids: User IDs to grant access (mutually exclusive with channel_ids)
        channel_ids: Channel IDs to grant access (mutually exclusive with user_ids)
        ctx: FastMCP context (automatically injected)

    Returns:
        Success status or error information

    Note:
        - Cannot specify both user_ids and channel_ids
        - 'owner' access only works with user_ids

    Example:
        # Grant read access to users
        set_list_access(list_id="F123", access_level="read", user_ids=["U123", "U456"])

        # Grant write access to a channel
        set_list_access(list_id="F123", access_level="write", channel_ids=["C123"])

    """
    try:
        if ctx:
            target = f"{len(user_ids)} users" if user_ids else f"{len(channel_ids)} channels"
            await ctx.info(f"Setting {access_level} access for {target} on list {list_id}")

        result = await slack_client.set_access(
            list_id=list_id,
            access_level=access_level,
            user_ids=user_ids,
            channel_ids=channel_ids,
        )

        if ctx:
            await ctx.info(f"Successfully set access on list {list_id}")

        return {
            "success": True,
            "list_id": list_id,
            "access_level": access_level,
        }

    except Exception as e:
        logger.error(f"Error setting list access: {e}")
        if ctx:
            await ctx.error(f"Failed to set access: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def delete_list_access(
    list_id: Annotated[
        str,
        Field(description="The ID of the list to revoke access from"),
    ],
    user_ids: Annotated[
        list[str] | None,
        Field(description="List of user IDs to revoke access (cannot use with channel_ids)"),
    ] = None,
    channel_ids: Annotated[
        list[str] | None,
        Field(description="List of channel IDs to revoke access (cannot use with user_ids)"),
    ] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """Revoke access for users or channels from a Slack list.

    Args:
        list_id: The ID of the list
        user_ids: User IDs to revoke access (mutually exclusive with channel_ids)
        channel_ids: Channel IDs to revoke access (mutually exclusive with user_ids)
        ctx: FastMCP context (automatically injected)

    Returns:
        Success status or error information

    Note:
        Cannot specify both user_ids and channel_ids in the same call.

    Example:
        # Revoke access from users
        delete_list_access(list_id="F123", user_ids=["U123", "U456"])

        # Revoke access from a channel
        delete_list_access(list_id="F123", channel_ids=["C123"])

    """
    try:
        if ctx:
            target = f"{len(user_ids)} users" if user_ids else f"{len(channel_ids)} channels"
            await ctx.info(f"Revoking access for {target} from list {list_id}")

        result = await slack_client.delete_access(
            list_id=list_id,
            user_ids=user_ids,
            channel_ids=channel_ids,
        )

        if ctx:
            await ctx.info(f"Successfully revoked access from list {list_id}")

        return {
            "success": True,
            "list_id": list_id,
        }

    except Exception as e:
        logger.error(f"Error deleting list access: {e}")
        if ctx:
            await ctx.error(f"Failed to delete access: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def start_list_export(
    list_id: Annotated[
        str,
        Field(description="The ID of the list to export"),
    ],
    include_archived: Annotated[
        bool,
        Field(description="Whether to include archived items in the export"),
    ] = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """Start an async export job for a Slack list.

    This initiates an export job that runs asynchronously. After calling this,
    use get_list_export_url with the returned job_id to retrieve the download URL.

    Args:
        list_id: The ID of the list to export
        include_archived: Include archived items in export (default: False)
        ctx: FastMCP context (automatically injected)

    Returns:
        Job information including job_id for polling

    Example:
        # Start export
        result = start_list_export(list_id="F123")
        job_id = result["job_id"]

        # Then poll for completion
        export = get_list_export_url(list_id="F123", job_id=job_id)

    """
    try:
        if ctx:
            await ctx.info(f"Starting export for list {list_id}")

        result = await slack_client.start_export(
            list_id=list_id,
            include_archived=include_archived,
        )

        if ctx:
            await ctx.info(f"Export job started: {result.get('job_id')}")

        return {
            "success": True,
            "job_id": result.get("job_id"),
            "list_id": list_id,
            "status": "started",
            "hint": "Use get_list_export_url with job_id to get the download URL",
        }

    except Exception as e:
        logger.error(f"Error starting list export: {e}")
        if ctx:
            await ctx.error(f"Failed to start export: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def get_list_export_url(
    list_id: Annotated[
        str,
        Field(description="The ID of the list"),
    ],
    job_id: Annotated[
        str,
        Field(description="The job ID from start_list_export"),
    ],
    ctx: Context = None,
) -> dict[str, Any]:
    """Get the download URL for a completed list export job.

    Args:
        list_id: The ID of the list
        job_id: The job ID returned from start_list_export
        ctx: FastMCP context (automatically injected)

    Returns:
        Download URL if ready, or processing status

    Note:
        If the job is still processing, retry after a short delay (e.g., 2-5 seconds).

    Example:
        result = get_list_export_url(list_id="F123", job_id="LeF123...")
        if result["status"] == "completed":
            download_url = result["download_url"]

    """
    try:
        if ctx:
            await ctx.info(f"Getting export URL for job {job_id}")

        result = await slack_client.get_export_url(
            list_id=list_id,
            job_id=job_id,
        )

        if ctx:
            await ctx.info(f"Export status: {result.get('status')}")

        return {
            "success": True,
            "download_url": result.get("download_url"),
            "job_id": job_id,
            "list_id": list_id,
            "status": result.get("status"),
        }

    except Exception as e:
        logger.error(f"Error getting export URL: {e}")
        if ctx:
            await ctx.error(f"Failed to get export URL: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool
async def wait_for_export(
    list_id: Annotated[
        str,
        Field(description="The ID of the list"),
    ],
    job_id: Annotated[
        str,
        Field(description="The job ID from start_list_export"),
    ],
    timeout: Annotated[
        int,
        Field(
            description="Maximum time to wait in seconds (default: 60)",
            ge=1,
            le=300,
        ),
    ] = 60,
    ctx: Context = None,
) -> dict[str, Any]:
    """Wait for an export job to complete and return the download URL.

    This tool polls the export status until it's ready or times out.
    Use this instead of manually polling get_list_export_url.

    Args:
        list_id: The ID of the list
        job_id: The job ID from start_list_export
        timeout: Maximum time to wait in seconds (default: 60, max: 300)
        ctx: FastMCP context (automatically injected)

    Returns:
        Export result with download_url if successful

    Example:
        # Start export
        start_result = start_list_export(list_id="F123")
        job_id = start_result["job_id"]

        # Wait for completion (blocks until ready)
        export = wait_for_export(list_id="F123", job_id=job_id, timeout=120)
        download_url = export["download_url"]

    """
    try:
        if ctx:
            await ctx.info(f"Waiting for export job {job_id} to complete...")

        result = await slack_client.wait_for_export(
            list_id=list_id,
            job_id=job_id,
            timeout=timeout,
        )

        if ctx:
            await ctx.info(f"Export completed: {result.get('download_url')}")

        return {
            "success": True,
            "download_url": result.get("download_url"),
            "job_id": job_id,
            "list_id": list_id,
            "status": "completed",
        }

    except TimeoutError as e:
        logger.warning(f"Export timeout: {e}")
        if ctx:
            await ctx.warning(f"Export timed out: {e!s}")
        return {
            "success": False,
            "error": str(e),
            "status": "timeout",
            "job_id": job_id,
            "list_id": list_id,
        }
    except Exception as e:
        logger.error(f"Error waiting for export: {e}")
        if ctx:
            await ctx.error(f"Failed to wait for export: {e!s}")
        return {
            "success": False,
            "error": str(e),
        }


# Add a resource to show server information
@mcp.resource("resource://server/info")
def get_server_info() -> dict[str, Any]:
    """Provide server configuration and status information."""
    return {
        "name": settings.mcp_server_name,
        "version": settings.mcp_server_version,
        "debug_mode": settings.debug_mode,
        "log_level": settings.log_level,
        "slack_api_timeout": settings.slack_api_timeout,
        "slack_retry_count": settings.slack_retry_count,
        "status": "running",
        "tools": [
            "add_list_item",
            "update_list_item",
            "delete_list_item",
            "delete_list_items",
            "get_list_item",
            "list_items",
            "get_list_info",
            "get_list_structure",
            "create_list",
            "update_list",
            "delete_list",
            "set_list_access",
            "delete_list_access",
            "start_list_export",
            "get_list_export_url",
            "wait_for_export",
        ],
    }


# Add a prompt template for Slack API documentation
@mcp.prompt("slack-api-documentation")
def slack_api_documentation() -> str:
    """Provide formatted Slack API documentation for system prompt usage."""
    return """
# slackLists.items.create method

## 概要
This method is used to create a new item, also known as a record, in an existing List.

## Usage info
This method is used to create a new item, also known as a record, in an existing List.
The item will be created with the field values specified in the initial_fields parameter. Each field corresponds to a column in the List and must reference a valid column_id.

## Sample requests data

### Creating items

#### Basic item creation
Provide field values using the initial_fields parameter:
```json
{
  "list_id": "F1234ABCD",
  "initial_fields": [
    {
      "column_id": "Col10000000",
      "rich_text": [
        {
          "type": "rich_text",
          "elements": [
            {
              "type": "rich_text_section",
              "elements": [
                {
                  "type": "text",
                  "text": "Complete project documentation"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

#### Duplicating items
Create a copy of an existing item by specifying the duplicated_item_id:
```json
{
  "list_id": "F1234ABCD",
  "duplicated_item_id": "Rec12345678"
}
```

#### Creating subtasks
Create a subtask by specifying the parent_item_id:
```json
{
  "list_id": "F1234ABCD",
  "parent_item_id": "Rec12345678",
  "initial_fields": [
    {
      "column_id": "Col10000000",
      "select": ["OptHIGH123"]
    }
  ]
}
```

### Field types
The initial_fields parameter supports all column types available in Lists. The supported field formats are as follows:

#### Text field (rich_text)
```json
{
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
              "text": "Your text content"
            }
          ]
        }
      ]
    }
  ]
}
```

#### User field
```json
{
  "column_id": "Col123",
  "user": ["U1234567", "U2345678"]
}
```

#### Date field
```json
{
  "column_id": "Col123",
  "date": ["2024-12-31"]
}
```

#### Select field
```json
{
  "column_id": "Col123",
  "select": ["OptionId123"]
}
```

#### Checkbox field
```json
{
  "column_id": "Col123",
  "checkbox": true
}
```

#### Number field
```json
{
  "column_id": "Col123",
  "number": [5000]
}
```

#### Email Field
```json
{
  "column_id": "Col123",
  "email": ["contact@example.com"]
}
```

#### Phone field
```json
{
  "column_id": "Col123",
  "phone": ["+1-555-123-4567"]
}
```

#### Attachment field
```json
{
  "column_id": "Col123",
  "attachment": ["F1234567890"]
}
```

#### Link field
```json
{
  "column_id": "Col123",
  "link": [
    {
      "original_url": "https://example.com",
      "display_as_url": false,
      "display_name": "Example Website"
    }
  ]
}
```

#### Message field
```json
{
  "column_id": "Col123",
  "message": ["https://yourteam.slack.com/archives/C1234567890/p1234567890123456"]
}
```

#### Rating field
```json
{
  "column_id": "Col123",
  "rating": [4]
}
```

#### Timestamp Field
```json
{
  "column_id": "Col123",
  "timestamp": [1704067200]
}
```

---

## 重要な注意事項

1. **リスト構造の理解**: アイテムを追加または更新する前に、`get_list_structure`を使用してリストの列構造を理解してください。

2. **DEFAULT_LIST_IDの活用**: 環境変数`DEFAULT_LIST_ID`が設定されている場合、すべてのツール呼び出しで`list_id`パラメータを省略できます。

## フィルター演算子

リストアイテムを検索する際に使用できる演算子：

- `equals`: 完全一致
- `not_equals`: 値が等しくない
- `contains`: 部分文字列を含む（大文字小文字を区別しない）
- `not_contains`: 部分文字列を含まない
- `in`: 指定されたリストに値が含まれる
- `not_in`: 指定されたリストに値が含まれない

## ドキュメント出典

このドキュメントは、Slack公式ドキュメント (https://docs.slack.dev/reference/methods/slackLists.items.create) に基づいて作成されています。
最新の情報については、公式ドキュメントを参照してください。
"""
