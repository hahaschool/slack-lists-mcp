# Slack Lists MCP Server

An MCP (Model Context Protocol) server for managing Slack Lists. This server provides tools to create, read, update, and delete items in Slack Lists, with advanced filtering capabilities.

## Features

- ✨ Full CRUD operations for Slack Lists and items
- 🔍 Advanced filtering with multiple operators
- 📑 Pagination support with async iteration
- 🏗️ Dynamic column structure discovery
- 🎯 Type-safe operations with `FieldType` and `AccessLevel` enums
- 🚀 Async/await support for better performance
- 🔐 Access control management (read/write/owner permissions)
- 📤 List export functionality with polling helper
- 🔄 Automatic retry with exponential backoff
- 📝 Item duplication and subtask creation
- 🛠️ Fluent builders for schema and item creation
- 🔧 Helper functions for all 17+ field types

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

**Note:** Slack Lists are only available to workspaces on a **paid plan**.

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

## Available Tools (17 total)

### List Management

| Tool | Description |
|------|-------------|
| `create_list` | Create a new Slack List |
| `update_list` | Update list properties |
| `delete_list` | Delete an entire list (permanent!) |
| `get_list_info` | Get list metadata |
| `get_list_structure` | Get column schema |

### Item Operations

| Tool | Description |
|------|-------------|
| `add_list_item` | Add a new item |
| `update_list_item` | Update item fields |
| `delete_list_item` | Delete a single item |
| `delete_list_items` | Delete multiple items |
| `get_list_item` | Get a specific item |
| `list_items` | List items with filtering |

### Access Control

| Tool | Description |
|------|-------------|
| `set_list_access` | Grant read/write/owner access |
| `delete_list_access` | Revoke access |

### Export

| Tool | Description |
|------|-------------|
| `start_list_export` | Start async export job |
| `get_list_export_url` | Get export download URL |
| `wait_for_export` | Wait for export completion |

---

### Tool Details

#### `get_list_structure`
Get the column structure of a Slack List.

```json
{
  "list_id": "F1234567890"
}
```

#### `add_list_item`
Add a new item to a Slack List.

```json
{
  "list_id": "F1234567890",
  "initial_fields": [
    {"column_id": "Col123", "text": "Task Name"},
    {"column_id": "Col456", "select": "OptABC123"},
    {"column_id": "Col789", "user": "U1234567"},
    {"column_id": "Col012", "checkbox": false}
  ]
}
```

**Item Duplication:**
```json
{
  "list_id": "F1234567890",
  "duplicated_item_id": "Rec12345678"
}
```

**Create Subtask:**
```json
{
  "list_id": "F1234567890",
  "parent_item_id": "Rec12345678",
  "initial_fields": [{"column_id": "Col123", "text": "Subtask"}]
}
```

#### `update_list_item`
Update existing items in a Slack List.

```json
{
  "list_id": "F1234567890",
  "cells": [
    {"row_id": "Rec123", "column_id": "Col123", "text": "Updated Name"},
    {"row_id": "Rec123", "column_id": "Col456", "checkbox": true}
  ]
}
```

**Create via update (batch creation):**
```json
{
  "list_id": "F1234567890",
  "cells": [
    {"row_id_to_create": true, "column_id": "Col123", "text": "New Item 1"},
    {"row_id_to_create": true, "column_id": "Col123", "text": "New Item 2"}
  ]
}
```

#### `list_items`
List items with optional filtering.

```json
{
  "list_id": "F1234567890",
  "limit": 50,
  "filters": {
    "name": {"contains": "Task"},
    "todo_completed": {"equals": false},
    "todo_assignee": {"in": ["U123", "U456"]}
  }
}
```

**Filter Operators:**
- `equals`: Exact match
- `not_equals`: Not equal to value
- `contains`: Contains substring (case-insensitive)
- `not_contains`: Does not contain substring
- `in`: Value is in the provided list
- `not_in`: Value is not in the provided list

#### `create_list`
Create a new Slack List.

**Simple todo list:**
```json
{
  "name": "My Tasks",
  "todo_mode": true
}
```

**Custom schema:**
```json
{
  "name": "Project Tracker",
  "schema": [
    {"key": "task", "name": "Task", "type": "text", "is_primary_column": true},
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
}
```

#### `delete_list`
Delete an entire Slack List (permanent!).

```json
{
  "list_id": "F1234567890"
}
```

#### `set_list_access`
Set access level for users or channels.

```json
{
  "list_id": "F1234567890",
  "access_level": "write",
  "user_ids": ["U123456", "U789012"]
}
```

#### `wait_for_export`
Wait for export completion with automatic polling.

```json
{
  "list_id": "F1234567890",
  "job_id": "LeF123456...",
  "timeout": 120
}
```

## Supported Field Types

| Type | Description | Example |
|------|-------------|---------|
| `text` | Rich text (auto-converted) | `"Hello World"` |
| `select` | Single/multi select | `"OptABC123"` or `["Opt1", "Opt2"]` |
| `user` | User references | `"U123456"` or `["U123", "U456"]` |
| `date` | Date values | `"2024-12-31"` |
| `number` | Numeric values | `42` or `3.14` |
| `checkbox` | Boolean | `true` or `false` |
| `email` | Email addresses | `"user@example.com"` |
| `phone` | Phone numbers | `"+1-555-1234"` |
| `link` | URLs | `"https://example.com"` |
| `attachment` | File IDs | `"F1234567890"` |
| `channel` | Channel references | `"C1234567890"` |
| `message` | Message permalinks | `"https://team.slack.com/archives/..."` |
| `rating` | Rating values | `4` |
| `timestamp` | Unix timestamps | `1704067200` |
| `vote` | Vote values | `5` |
| `canvas` | Canvas IDs | `"F1234567890"` |

## Python SDK Usage

When using the client directly in Python:

### Helper Functions

```python
from slack_lists_mcp import (
    make_field,
    make_rich_text,
    make_select,
    make_user,
    extract_text,
    FieldType,
    AccessLevel,
)

# Create fields easily
fields = [
    make_field("Col1", "Task Name", "text"),
    make_field("Col2", "U123456", "user"),
    make_field("Col3", True, "checkbox"),
    make_field("Col4", 4, FieldType.RATING),
]

# Extract text from rich_text responses
for field in item["fields"]:
    if "rich_text" in field:
        text = extract_text(field["rich_text"])
        print(text)
```

### Builder Classes

```python
from slack_lists_mcp import (
    SchemaBuilder,
    SelectOption,
    ItemBuilder,
    batch_create_items,
)

# Build a schema fluently
schema = (
    SchemaBuilder()
    .add_text("task", "Task Name", primary=True)
    .add_select("status", "Status", [
        SelectOption("todo", "To Do", "gray"),
        SelectOption("in_progress", "In Progress", "blue"),
        SelectOption("done", "Done", "green"),
    ])
    .add_user("assignee", "Assignee")
    .add_date("due_date", "Due Date")
    .build()
)

# Build items fluently
fields = (
    ItemBuilder()
    .text("Col1", "My Task")
    .user("Col2", "U123456")
    .checkbox("Col3", True)
    .date("Col4", "2024-12-31")
    .build()
)

# Batch create items
cells = batch_create_items([
    ItemBuilder().text("Col1", "Task 1"),
    ItemBuilder().text("Col1", "Task 2"),
])
```

### Async Iteration

```python
from slack_lists_mcp.slack_client import SlackListsClient

client = SlackListsClient()

# Iterate through all items automatically
async for item in client.iter_all_items("F123"):
    print(item["id"])

# With filters
async for item in client.iter_all_items(
    "F123",
    filters={"status": {"equals": "active"}}
):
    process_item(item)
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

- [GitHub Issues](https://github.com/ppspps824/slack-lists-mcp/issues)
- [Slack Lists API Documentation](https://docs.slack.dev/surfaces/lists/)
- [MCP Documentation](https://modelcontextprotocol.io)
