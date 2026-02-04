# Slack Lists MCP Server

An MCP (Model Context Protocol) server for managing Slack Lists. This server provides tools to create, read, update, and delete items in Slack Lists, with advanced filtering capabilities.

## Features

- ✨ Full CRUD operations for Slack List items
- 🔍 Advanced filtering with multiple operators
- 📑 Pagination support for large lists
- 🏗️ Dynamic column structure discovery
- 🎯 Type-safe operations with validation
- 🚀 Async/await support for better performance
- 🔐 Access control management (read/write/owner permissions)
- 📤 List export functionality (async job-based)
- 🔄 Automatic retry with exponential backoff
- 📝 Item duplication and subtask creation

## Installation

### Configure in Claude Desktop

Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "slack-lists": {
      "command": "uvx",
      "args": ["slack-lists-mcp"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-bot-token"
      }
    }
  }
}
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token | ✅ | - |
| `DEFAULT_LIST_ID` | Default list ID to use when not specified in tool calls | ❌ | - |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | ❌ | INFO |
| `SLACK_API_TIMEOUT` | Timeout for Slack API calls (seconds) | ❌ | 30 |
| `SLACK_RETRY_COUNT` | Number of retries for failed API calls | ❌ | 3 |
| `DEBUG_MODE` | Enable debug mode | ❌ | false |

### Setting up Slack Bot

1. Create a Slack App at [api.slack.com](https://api.slack.com/apps)
2. Add the following OAuth scopes to your Bot Token:
   - `lists:read` - Read list items
   - `lists:write` - Create and update list items
3. Install the app to your workspace
4. Copy the Bot User OAuth Token (starts with `xoxb-`)

### Using Default List ID

You can set a default list ID using the `DEFAULT_LIST_ID` environment variable. This allows you to omit the `list_id` parameter from tool calls when working with a specific list.

**Example configuration:**
```json
{
  "mcpServers": {
    "slack-lists": {
      "command": "uvx",
      "args": ["slack-lists-mcp"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-bot-token",
        "DEFAULT_LIST_ID": "F1234567890"
      }
    }
  }
}
```

With this configuration, you can call tools without specifying `list_id`:
- `add_list_item` with just `initial_fields`
- `list_items` with just `limit` and `filters`
- `get_list_structure` with no parameters

## Available Tools

### 1. `get_list_structure`
Get the column structure of a Slack List.

**Parameters:**
- `list_id` (optional): The ID of the list (uses DEFAULT_LIST_ID env var if not provided)

**Returns:** Column definitions including IDs, names, types, and options

### 2. `add_list_item`
Add a new item to a Slack List.

**Parameters:**
- `initial_fields` (optional): Array of field objects with column_id and value (required unless using `duplicated_item_id`)
- `duplicated_item_id` (optional): ID of an existing item to duplicate
- `parent_item_id` (optional): ID of a parent item to create a subtask under
- `list_id` (optional): The ID of the list (uses DEFAULT_LIST_ID env var if not provided)

**Example (Simplified format):**
```json
{
  "list_id": "F1234567890",
  "initial_fields": [
    {
      "column_id": "Col123",
      "text": "Task Name"  // Simple text format
    },
    {
      "column_id": "Col456",
      "select": "OptABC123"  // Single select value
    },
    {
      "column_id": "Col789",
      "user": "U1234567"  // Single user ID
    },
    {
      "column_id": "Col012",
      "checkbox": false
    }
  ]
}
```

**Example (Full rich_text format - also supported):**
```json
{
  "list_id": "F1234567890",
  "initial_fields": [
    {
      "column_id": "Col123",
      "rich_text": [{
        "type": "rich_text",
        "elements": [{
          "type": "rich_text_section",
          "elements": [{"type": "text", "text": "Task Name"}]
        }]
      }]
    },
    {
      "column_id": "Col456",
      "select": ["OptABC123"]  // Array format
    }
  ]
}
```

### 3. `update_list_item`
Update existing items in a Slack List.

**Parameters:**
- `cells` (required): Array of cell objects with row_id, column_id, and value
- `list_id` (optional): The ID of the list (uses DEFAULT_LIST_ID env var if not provided)

**Field Formats:** (Same as add_list_item)
- **Text fields**: Can use simple `text` key (auto-converted to rich_text)
- **Select fields**: Can use single value (auto-wrapped in array)
- **User fields**: Can use single user ID (auto-wrapped in array)
- **Checkbox fields**: Boolean value

**Example (Simplified format):**
```json
{
  "list_id": "F1234567890",
  "cells": [
    {
      "row_id": "Rec123",
      "column_id": "Col123",
      "text": "Updated Task Name"  // Simple text format
    },
    {
      "row_id": "Rec123",
      "column_id": "Col456",
      "checkbox": true
    },
    {
      "row_id": "Rec123",
      "column_id": "Col789",
      "select": "OptXYZ456"  // Single select value
    }
  ]
}
```

### 4. `delete_list_item`
Delete an item from a Slack List.

**Parameters:**
- `item_id` (required): The ID of the item to delete
- `list_id` (optional): The ID of the list (uses DEFAULT_LIST_ID env var if not provided)

### 5. `get_list_item`
Get a specific item from a Slack List.

**Parameters:**
- `item_id` (required): The ID of the item
- `list_id` (optional): The ID of the list (uses DEFAULT_LIST_ID env var if not provided)
- `include_is_subscribed` (optional): Include subscription status

### 6. `list_items`
List all items in a Slack List with optional filtering.

**Parameters:**
- `list_id` (optional): The ID of the list (uses DEFAULT_LIST_ID env var if not provided)
- `limit` (optional): Maximum number of items (default: 100)
- `cursor` (optional): Pagination cursor
- `archived` (optional): Filter for archived items
- `filters` (optional): Column-based filters

**Filter Operators:**
- `equals`: Exact match
- `not_equals`: Not equal to value
- `contains`: Contains substring (case-insensitive)
- `not_contains`: Does not contain substring
- `in`: Value is in the provided list
- `not_in`: Value is not in the provided list

**Example with filters:**
```json
{
  "list_id": "F1234567890",
  "filters": {
    "name": {"contains": "Task"},
    "todo_completed": {"equals": false},
    "todo_assignee": {"in": ["U123", "U456"]}
  }
}
```

### 7. `get_list_info`
Get metadata about a Slack List.

**Parameters:**

- `list_id` (optional): The ID of the list (uses DEFAULT_LIST_ID env var if not provided)

### 8. `delete_list_items`

Delete multiple items from a Slack List in a single call.

**Parameters:**

- `item_ids` (required): Array of item IDs to delete
- `list_id` (optional): The ID of the list (uses DEFAULT_LIST_ID env var if not provided)

**Example:**
```json
{
  "list_id": "F1234567890",
  "item_ids": ["Rec123", "Rec456", "Rec789"]
}
```

### 9. `create_list`

Create a new Slack List.

**Parameters:**

- `name` (optional): Name of the list
- `description` (optional): Description of the list
- `todo_mode` (optional): When true, creates with Completed, Assignee, Due Date columns
- `schema` (optional): Custom column definitions for the list structure
- `copy_from_list_id` (optional): ID of an existing list to duplicate
- `include_copied_list_records` (optional): Include records when copying from another list

**Example (Simple todo list):**
```json
{
  "name": "My Tasks",
  "todo_mode": true
}
```

**Example (Custom schema):**
```json
{
  "name": "Project Tracker",
  "schema": [
    {"key": "task", "name": "Task", "type": "text", "is_primary_column": true},
    {"key": "status", "name": "Status", "type": "select"},
    {"key": "assignee", "name": "Assignee", "type": "user"},
    {"key": "due", "name": "Due Date", "type": "date"}
  ]
}
```

### 10. `update_list`

Update a Slack List's properties.

**Parameters:**

- `list_id` (required): The ID of the list to update
- `name` (optional): New name for the list
- `description` (optional): New description for the list
- `todo_mode` (optional): Enable/disable todo mode

### 11. `set_list_access`

Set access level for users or channels on a Slack List.

**Parameters:**

- `list_id` (required): The ID of the list
- `access_level` (required): Permission level - `read`, `write`, or `owner`
- `user_ids` (optional): Array of user IDs to grant access (mutually exclusive with channel_ids)
- `channel_ids` (optional): Array of channel IDs to grant access (mutually exclusive with user_ids)

**Example:**
```json
{
  "list_id": "F1234567890",
  "access_level": "write",
  "user_ids": ["U123456", "U789012"]
}
```

### 12. `delete_list_access`

Revoke access for users or channels from a Slack List.

**Parameters:**

- `list_id` (required): The ID of the list
- `user_ids` (optional): Array of user IDs to revoke access (mutually exclusive with channel_ids)
- `channel_ids` (optional): Array of channel IDs to revoke access (mutually exclusive with user_ids)

### 13. `start_list_export`

Start an async export job for a Slack List.

**Parameters:**

- `list_id` (required): The ID of the list to export
- `include_archived` (optional): Include archived items in the export (default: false)

**Returns:** Job ID for polling with `get_list_export_url`

### 14. `get_list_export_url`

Get the download URL for a completed list export job.

**Parameters:**

- `list_id` (required): The ID of the list
- `job_id` (required): The job ID from `start_list_export`

**Returns:** Download URL if ready, or processing status

**Example workflow:**

```python
# 1. Start export
result = start_list_export(list_id="F123")
job_id = result["job_id"]

# 2. Poll for completion (wait a few seconds)
export = get_list_export_url(list_id="F123", job_id=job_id)
if export["status"] == "completed":
    download_url = export["download_url"]
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/ppspps824/slack-lists-mcp.git
cd slack-lists-mcp

# Install dependencies
uv sync
```

### Running in Development Mode

```bash
# Run with FastMCP dev mode (with auto-reload)
uv run fastmcp dev src/slack_lists_mcp/server.py:mcp

# Or run directly
uv run slack-lists-mcp
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=slack_lists_mcp

# Run specific test file
uv run pytest tests/test_server.py -v
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- [GitHub Issues](https://github.com/yourusername/slack-lists-mcp/issues)
- [Slack API Documentation](https://api.slack.com/methods#lists)
- [MCP Documentation](https://modelcontextprotocol.io)
