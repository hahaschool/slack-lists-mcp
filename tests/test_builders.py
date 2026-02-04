"""Tests for the builder classes."""

import pytest

from slack_lists_mcp.builders import (
    ColumnBuilder,
    ItemBuilder,
    SchemaBuilder,
    SelectOption,
    batch_create_items,
)


# Tests for SelectOption


def test_select_option_valid_color():
    """Test SelectOption with valid color."""
    option = SelectOption("done", "Done", "green")
    result = option.build()

    assert result["key"] == "done"
    assert result["value"] == "Done"
    assert result["color"] == "green"


def test_select_option_default_color():
    """Test SelectOption with default gray color."""
    option = SelectOption("todo", "To Do")
    result = option.build()

    assert result["color"] == "gray"


def test_select_option_invalid_color():
    """Test SelectOption rejects invalid color."""
    with pytest.raises(ValueError) as exc_info:
        SelectOption("key", "value", "invalid_color")
    assert "Invalid color" in str(exc_info.value)


def test_select_option_all_colors():
    """Test all valid colors are accepted."""
    valid_colors = [
        "indigo", "blue", "cyan", "pink", "yellow",
        "green", "gray", "red", "purple", "orange", "brown"
    ]
    for color in valid_colors:
        option = SelectOption("key", "value", color)
        assert option.build()["color"] == color


# Tests for ColumnBuilder


def test_column_builder_text():
    """Test building a text column."""
    column = ColumnBuilder("task", "Task Name").text().build()

    assert column["key"] == "task"
    assert column["name"] == "Task Name"
    assert column["type"] == "text"


def test_column_builder_primary():
    """Test building a primary text column."""
    column = ColumnBuilder("name", "Name").text().primary().build()

    assert column["is_primary_column"] is True
    assert column["type"] == "text"


def test_column_builder_primary_must_be_text():
    """Test that primary column must be text type."""
    with pytest.raises(ValueError) as exc_info:
        ColumnBuilder("status", "Status").select([]).primary().build()
    assert "Primary column must be text type" in str(exc_info.value)


def test_column_builder_select_with_options():
    """Test building a select column with options."""
    column = (
        ColumnBuilder("status", "Status")
        .select([
            SelectOption("todo", "To Do", "gray"),
            SelectOption("done", "Done", "green"),
        ])
        .build()
    )

    assert column["type"] == "select"
    assert len(column["options"]["choices"]) == 2
    assert column["options"]["choices"][0]["key"] == "todo"


def test_column_builder_multi_select():
    """Test building a multi-select column."""
    column = (
        ColumnBuilder("tags", "Tags")
        .multi_select([
            SelectOption("bug", "Bug", "red"),
            SelectOption("feature", "Feature", "blue"),
        ])
        .build()
    )

    assert column["type"] == "select"
    assert column["options"]["format"] == "multi_select"


def test_column_builder_date_with_format():
    """Test building a date column with custom format."""
    column = ColumnBuilder("due", "Due Date").date("MM/DD/YYYY").build()

    assert column["type"] == "date"
    assert column["options"]["format"] == "MM/DD/YYYY"


def test_column_builder_user_multi():
    """Test building a multi-user column."""
    column = ColumnBuilder("assignees", "Assignees").user(multi=True).build()

    assert column["type"] == "user"
    assert column["options"]["format"] == "multi_entity"


def test_column_builder_all_types():
    """Test all column types can be built."""
    types_to_test = [
        ("text", "text"),
        ("number", "number"),
        ("checkbox", "checkbox"),
        ("email", "email"),
        ("phone", "phone"),
        ("link", "link"),
        ("attachment", "attachment"),
        ("rating", "rating"),
        ("channel", "channel"),
        ("message", "message"),
        ("timestamp", "timestamp"),
        ("vote", "vote"),
        ("canvas", "canvas"),
    ]

    for method_name, expected_type in types_to_test:
        builder = ColumnBuilder("col", "Column")
        method = getattr(builder, method_name)
        column = method().build()
        assert column["type"] == expected_type


def test_column_builder_no_type_raises():
    """Test that building without setting type raises error."""
    with pytest.raises(ValueError) as exc_info:
        ColumnBuilder("col", "Column").build()
    assert "Column type must be set" in str(exc_info.value)


# Tests for SchemaBuilder


def test_schema_builder_basic():
    """Test building a basic schema."""
    schema = (
        SchemaBuilder()
        .add_text("task", "Task Name", primary=True)
        .add_checkbox("done", "Done")
        .build()
    )

    assert len(schema) == 2
    assert schema[0]["is_primary_column"] is True
    assert schema[1]["type"] == "checkbox"


def test_schema_builder_with_select():
    """Test building a schema with select column."""
    schema = (
        SchemaBuilder()
        .add_text("name", "Name", primary=True)
        .add_select("status", "Status", [
            SelectOption("active", "Active", "green"),
            SelectOption("inactive", "Inactive", "gray"),
        ])
        .build()
    )

    assert len(schema) == 2
    assert schema[1]["type"] == "select"
    assert len(schema[1]["options"]["choices"]) == 2


def test_schema_builder_only_one_primary():
    """Test that only one primary column is allowed."""
    builder = SchemaBuilder().add_text("col1", "Column 1", primary=True)

    with pytest.raises(ValueError) as exc_info:
        builder.add_text("col2", "Column 2", primary=True)
    assert "only have one primary column" in str(exc_info.value)


def test_schema_builder_empty_raises():
    """Test that empty schema raises error."""
    with pytest.raises(ValueError) as exc_info:
        SchemaBuilder().build()
    assert "at least one column" in str(exc_info.value)


def test_schema_builder_all_column_types():
    """Test adding all column types to schema."""
    schema = (
        SchemaBuilder()
        .add_text("text", "Text", primary=True)
        .add_number("num", "Number")
        .add_date("date", "Date")
        .add_user("user", "User")
        .add_checkbox("check", "Checkbox")
        .add_email("email", "Email")
        .add_phone("phone", "Phone")
        .add_link("link", "Link")
        .add_attachment("attach", "Attachment")
        .add_rating("rating", "Rating")
        .add_channel("channel", "Channel")
        .add_message("message", "Message")
        .add_timestamp("ts", "Timestamp")
        .add_vote("vote", "Vote")
        .add_canvas("canvas", "Canvas")
        .build()
    )

    assert len(schema) == 15


def test_schema_builder_add_column_builder():
    """Test adding a ColumnBuilder to schema."""
    col = ColumnBuilder("custom", "Custom Column").text()
    schema = SchemaBuilder().add_column(col).build()

    assert len(schema) == 1
    assert schema[0]["key"] == "custom"


# Tests for ItemBuilder


def test_item_builder_text():
    """Test building an item with text field."""
    fields = ItemBuilder().text("Col123", "Hello World").build()

    assert len(fields) == 1
    assert fields[0]["column_id"] == "Col123"
    assert "rich_text" in fields[0]


def test_item_builder_multiple_fields():
    """Test building an item with multiple fields."""
    fields = (
        ItemBuilder()
        .text("Col1", "Task Name")
        .user("Col2", "U123456")
        .checkbox("Col3", True)
        .date("Col4", "2024-12-31")
        .build()
    )

    assert len(fields) == 4
    assert fields[1]["user"] == ["U123456"]
    assert fields[2]["checkbox"] is True


def test_item_builder_link_with_display_name():
    """Test building an item with link and display name."""
    fields = ItemBuilder().link("Col1", "https://example.com", "Example").build()

    assert len(fields) == 1
    link = fields[0]["link"]
    assert link[0]["original_url"] == "https://example.com"
    assert link[0]["display_name"] == "Example"


def test_item_builder_build_cells():
    """Test building cells for update_item."""
    cells = (
        ItemBuilder()
        .text("Col1", "Updated")
        .checkbox("Col2", True)
        .build_cells("Rec123")
    )

    assert len(cells) == 2
    assert cells[0]["row_id"] == "Rec123"
    assert cells[1]["row_id"] == "Rec123"


def test_item_builder_build_create_cells():
    """Test building cells for creating via update_item."""
    cells = (
        ItemBuilder()
        .text("Col1", "New Item")
        .user("Col2", "U123")
        .build_create_cells()
    )

    assert len(cells) == 2
    assert cells[0]["row_id_to_create"] is True
    assert cells[1]["row_id_to_create"] is True


def test_item_builder_all_field_types():
    """Test all field types in ItemBuilder."""
    fields = (
        ItemBuilder()
        .text("c1", "text")
        .user("c2", "U123")
        .select("c3", "Opt123")
        .date("c4", "2024-01-01")
        .number("c5", 42)
        .checkbox("c6", True)
        .email("c7", "test@example.com")
        .phone("c8", "+1-555-1234")
        .link("c9", "https://example.com")
        .attachment("c10", "F123")
        .message("c11", "https://slack.com/archives/C123/p123")
        .rating("c12", 5)
        .timestamp("c13", 1704067200)
        .channel("c14", "C123")
        .vote("c15", 3)
        .canvas("c16", "F456")
        .build()
    )

    assert len(fields) == 16


def test_item_builder_empty_raises():
    """Test that empty item raises error."""
    with pytest.raises(ValueError) as exc_info:
        ItemBuilder().build()
    assert "at least one field" in str(exc_info.value)


# Tests for batch_create_items


def test_batch_create_items_with_builders():
    """Test batch_create_items with ItemBuilder instances."""
    cells = batch_create_items([
        ItemBuilder().text("Col1", "Task 1"),
        ItemBuilder().text("Col1", "Task 2"),
    ])

    assert len(cells) == 2
    assert all(c.get("row_id_to_create") is True for c in cells)


def test_batch_create_items_with_field_lists():
    """Test batch_create_items with raw field lists."""
    cells = batch_create_items([
        [{"column_id": "Col1", "text": "Task 1"}],
        [{"column_id": "Col1", "text": "Task 2"}],
    ])

    assert len(cells) == 2
    assert all(c.get("row_id_to_create") is True for c in cells)


def test_batch_create_items_mixed():
    """Test batch_create_items with mixed input."""
    cells = batch_create_items([
        ItemBuilder().text("Col1", "Task 1").user("Col2", "U123"),
        [{"column_id": "Col1", "text": "Task 2"}],
    ])

    assert len(cells) == 3  # 2 fields from first + 1 from second
    assert all(c.get("row_id_to_create") is True for c in cells)
