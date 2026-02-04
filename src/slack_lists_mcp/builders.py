"""Builder classes for Slack Lists schema and item creation.

These utilities provide a fluent interface for constructing list schemas,
column definitions, and items with proper formatting.
"""

from typing import Any, Self

from slack_lists_mcp.helpers import (
    FieldType,
    make_attachment,
    make_canvas,
    make_channel,
    make_date,
    make_email,
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


# Valid colors for select options in Slack Lists
SELECT_COLORS = frozenset({
    "indigo",
    "blue",
    "cyan",
    "pink",
    "yellow",
    "green",
    "gray",
    "red",
    "purple",
    "orange",
    "brown",
})


class SelectOption:
    """Helper for creating select column options.

    Example:
        >>> options = [
        ...     SelectOption("todo", "To Do", "gray").build(),
        ...     SelectOption("in_progress", "In Progress", "blue").build(),
        ...     SelectOption("done", "Done", "green").build(),
        ... ]

    """

    def __init__(self, key: str, value: str, color: str = "gray"):
        """Create a select option.

        Args:
            key: Unique identifier for the option
            value: Display text for the option
            color: Color for the option (indigo, blue, cyan, pink, yellow,
                   green, gray, red, purple, orange, brown)

        """
        if color not in SELECT_COLORS:
            raise ValueError(
                f"Invalid color '{color}'. Valid colors: {', '.join(sorted(SELECT_COLORS))}"
            )
        self.key = key
        self.value = value
        self.color = color

    def build(self) -> dict[str, str]:
        """Build the option dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "color": self.color,
        }


class ColumnBuilder:
    """Fluent builder for creating column definitions.

    Example:
        >>> column = (
        ...     ColumnBuilder("task", "Task Name")
        ...     .text()
        ...     .primary()
        ...     .build()
        ... )

        >>> status_column = (
        ...     ColumnBuilder("status", "Status")
        ...     .select([
        ...         SelectOption("todo", "To Do", "gray"),
        ...         SelectOption("done", "Done", "green"),
        ...     ])
        ...     .build()
        ... )

    """

    def __init__(self, key: str, name: str):
        """Initialize the column builder.

        Args:
            key: Unique key for the column
            name: Display name for the column

        """
        self._key = key
        self._name = name
        self._type: str | None = None
        self._is_primary = False
        self._options: dict[str, Any] = {}

    def text(self) -> Self:
        """Set column type to text."""
        self._type = "text"
        return self

    def number(self) -> Self:
        """Set column type to number."""
        self._type = "number"
        return self

    def select(self, choices: list[SelectOption | dict[str, str]]) -> Self:
        """Set column type to select with options.

        Args:
            choices: List of SelectOption objects or dicts with key/value/color

        """
        self._type = "select"
        built_choices = []
        for choice in choices:
            if isinstance(choice, SelectOption):
                built_choices.append(choice.build())
            else:
                built_choices.append(choice)
        self._options["choices"] = built_choices
        return self

    def multi_select(self, choices: list[SelectOption | dict[str, str]]) -> Self:
        """Set column type to multi-select with options.

        Args:
            choices: List of SelectOption objects or dicts with key/value/color

        """
        self.select(choices)
        self._options["format"] = "multi_select"
        return self

    def date(self, format: str = "default") -> Self:
        """Set column type to date.

        Args:
            format: Date format (default, DD/MM/YYYY, MM/DD/YYYY, YYYY/MM/DD,
                   MMMM DD YYYY, DD MMMM YYYY)

        """
        self._type = "date"
        if format != "default":
            self._options["format"] = format
        return self

    def user(self, multi: bool = False) -> Self:
        """Set column type to user.

        Args:
            multi: Allow multiple users if True

        """
        self._type = "user"
        if multi:
            self._options["format"] = "multi_entity"
        return self

    def checkbox(self) -> Self:
        """Set column type to checkbox."""
        self._type = "checkbox"
        return self

    def email(self) -> Self:
        """Set column type to email."""
        self._type = "email"
        return self

    def phone(self) -> Self:
        """Set column type to phone."""
        self._type = "phone"
        return self

    def link(self) -> Self:
        """Set column type to link."""
        self._type = "link"
        return self

    def attachment(self) -> Self:
        """Set column type to attachment."""
        self._type = "attachment"
        return self

    def rating(self) -> Self:
        """Set column type to rating."""
        self._type = "rating"
        return self

    def channel(self) -> Self:
        """Set column type to channel reference."""
        self._type = "channel"
        return self

    def message(self) -> Self:
        """Set column type to message reference."""
        self._type = "message"
        return self

    def timestamp(self) -> Self:
        """Set column type to timestamp."""
        self._type = "timestamp"
        return self

    def vote(self) -> Self:
        """Set column type to vote."""
        self._type = "vote"
        return self

    def canvas(self) -> Self:
        """Set column type to canvas."""
        self._type = "canvas"
        return self

    def primary(self) -> Self:
        """Mark this column as the primary column (must be text type)."""
        self._is_primary = True
        return self

    def build(self) -> dict[str, Any]:
        """Build the column definition dictionary."""
        if self._type is None:
            raise ValueError("Column type must be set before building")

        column: dict[str, Any] = {
            "key": self._key,
            "name": self._name,
            "type": self._type,
        }

        if self._is_primary:
            if self._type != "text":
                raise ValueError("Primary column must be text type")
            column["is_primary_column"] = True

        if self._options:
            column["options"] = self._options

        return column


class SchemaBuilder:
    """Fluent builder for creating list schemas.

    Example:
        >>> schema = (
        ...     SchemaBuilder()
        ...     .add_text("task", "Task Name", primary=True)
        ...     .add_select("status", "Status", [
        ...         SelectOption("todo", "To Do", "gray"),
        ...         SelectOption("in_progress", "In Progress", "blue"),
        ...         SelectOption("done", "Done", "green"),
        ...     ])
        ...     .add_user("assignee", "Assignee")
        ...     .add_date("due_date", "Due Date")
        ...     .build()
        ... )

    """

    def __init__(self):
        """Initialize the schema builder."""
        self._columns: list[dict[str, Any]] = []
        self._has_primary = False

    def add_column(self, column: ColumnBuilder | dict[str, Any]) -> Self:
        """Add a column to the schema.

        Args:
            column: ColumnBuilder instance or column dict

        """
        if isinstance(column, ColumnBuilder):
            col_dict = column.build()
        else:
            col_dict = column

        if col_dict.get("is_primary_column"):
            if self._has_primary:
                raise ValueError("Schema can only have one primary column")
            self._has_primary = True

        self._columns.append(col_dict)
        return self

    def add_text(self, key: str, name: str, primary: bool = False) -> Self:
        """Add a text column.

        Args:
            key: Column key
            name: Column display name
            primary: Whether this is the primary column

        """
        builder = ColumnBuilder(key, name).text()
        if primary:
            builder.primary()
        return self.add_column(builder)

    def add_number(self, key: str, name: str) -> Self:
        """Add a number column."""
        return self.add_column(ColumnBuilder(key, name).number())

    def add_select(
        self, key: str, name: str, choices: list[SelectOption | dict[str, str]]
    ) -> Self:
        """Add a select column with options."""
        return self.add_column(ColumnBuilder(key, name).select(choices))

    def add_multi_select(
        self, key: str, name: str, choices: list[SelectOption | dict[str, str]]
    ) -> Self:
        """Add a multi-select column with options."""
        return self.add_column(ColumnBuilder(key, name).multi_select(choices))

    def add_date(self, key: str, name: str, format: str = "default") -> Self:
        """Add a date column."""
        return self.add_column(ColumnBuilder(key, name).date(format))

    def add_user(self, key: str, name: str, multi: bool = False) -> Self:
        """Add a user column."""
        return self.add_column(ColumnBuilder(key, name).user(multi))

    def add_checkbox(self, key: str, name: str) -> Self:
        """Add a checkbox column."""
        return self.add_column(ColumnBuilder(key, name).checkbox())

    def add_email(self, key: str, name: str) -> Self:
        """Add an email column."""
        return self.add_column(ColumnBuilder(key, name).email())

    def add_phone(self, key: str, name: str) -> Self:
        """Add a phone column."""
        return self.add_column(ColumnBuilder(key, name).phone())

    def add_link(self, key: str, name: str) -> Self:
        """Add a link column."""
        return self.add_column(ColumnBuilder(key, name).link())

    def add_attachment(self, key: str, name: str) -> Self:
        """Add an attachment column."""
        return self.add_column(ColumnBuilder(key, name).attachment())

    def add_rating(self, key: str, name: str) -> Self:
        """Add a rating column."""
        return self.add_column(ColumnBuilder(key, name).rating())

    def add_channel(self, key: str, name: str) -> Self:
        """Add a channel reference column."""
        return self.add_column(ColumnBuilder(key, name).channel())

    def add_message(self, key: str, name: str) -> Self:
        """Add a message reference column."""
        return self.add_column(ColumnBuilder(key, name).message())

    def add_timestamp(self, key: str, name: str) -> Self:
        """Add a timestamp column."""
        return self.add_column(ColumnBuilder(key, name).timestamp())

    def add_vote(self, key: str, name: str) -> Self:
        """Add a vote column."""
        return self.add_column(ColumnBuilder(key, name).vote())

    def add_canvas(self, key: str, name: str) -> Self:
        """Add a canvas reference column."""
        return self.add_column(ColumnBuilder(key, name).canvas())

    def build(self) -> list[dict[str, Any]]:
        """Build the schema as a list of column definitions."""
        if not self._columns:
            raise ValueError("Schema must have at least one column")
        return self._columns


class ItemBuilder:
    """Fluent builder for creating list items.

    Example:
        >>> item = (
        ...     ItemBuilder()
        ...     .text("Col123", "Task title")
        ...     .user("Col456", "U123456")
        ...     .date("Col789", "2024-12-31")
        ...     .checkbox("ColABC", True)
        ...     .build()
        ... )

    """

    def __init__(self):
        """Initialize the item builder."""
        self._fields: list[dict[str, Any]] = []

    def add_field(self, column_id: str, field_type: str, value: Any) -> Self:
        """Add a field with explicit type.

        Args:
            column_id: The column ID
            field_type: The field type (text, user, date, etc.)
            value: The field value

        """
        field: dict[str, Any] = {"column_id": column_id}

        if field_type == "text":
            field["rich_text"] = make_rich_text(str(value))
        elif field_type == "user":
            field["user"] = make_user(value)
        elif field_type == "select":
            field["select"] = make_select(value)
        elif field_type == "date":
            field["date"] = make_date(value)
        elif field_type == "number":
            field["number"] = make_number(value)
        elif field_type == "checkbox":
            field["checkbox"] = bool(value)
        elif field_type == "email":
            field["email"] = make_email(value)
        elif field_type == "phone":
            field["phone"] = make_phone(value)
        elif field_type == "link":
            if isinstance(value, str):
                field["link"] = make_link(value)
            elif isinstance(value, tuple) and len(value) == 2:
                field["link"] = make_link(value[0], value[1])
            else:
                field["link"] = value
        elif field_type == "attachment":
            field["attachment"] = make_attachment(value)
        elif field_type == "message":
            field["message"] = make_message(value)
        elif field_type == "rating":
            field["rating"] = make_rating(value)
        elif field_type == "timestamp":
            field["timestamp"] = make_timestamp(value)
        elif field_type == "channel":
            field["channel"] = make_channel(value)
        elif field_type == "vote":
            field["vote"] = make_vote(value)
        elif field_type == "canvas":
            field["canvas"] = make_canvas(value)
        else:
            field[field_type] = value

        self._fields.append(field)
        return self

    def text(self, column_id: str, value: str) -> Self:
        """Add a text field."""
        return self.add_field(column_id, "text", value)

    def user(self, column_id: str, user_ids: str | list[str]) -> Self:
        """Add a user field."""
        return self.add_field(column_id, "user", user_ids)

    def select(self, column_id: str, option_ids: str | list[str]) -> Self:
        """Add a select field."""
        return self.add_field(column_id, "select", option_ids)

    def date(self, column_id: str, dates: str | list[str]) -> Self:
        """Add a date field."""
        return self.add_field(column_id, "date", dates)

    def number(self, column_id: str, value: int | float | list) -> Self:
        """Add a number field."""
        return self.add_field(column_id, "number", value)

    def checkbox(self, column_id: str, checked: bool) -> Self:
        """Add a checkbox field."""
        return self.add_field(column_id, "checkbox", checked)

    def email(self, column_id: str, emails: str | list[str]) -> Self:
        """Add an email field."""
        return self.add_field(column_id, "email", emails)

    def phone(self, column_id: str, phones: str | list[str]) -> Self:
        """Add a phone field."""
        return self.add_field(column_id, "phone", phones)

    def link(
        self, column_id: str, url: str, display_name: str | None = None
    ) -> Self:
        """Add a link field."""
        if display_name:
            return self.add_field(column_id, "link", (url, display_name))
        return self.add_field(column_id, "link", url)

    def attachment(self, column_id: str, file_ids: str | list[str]) -> Self:
        """Add an attachment field."""
        return self.add_field(column_id, "attachment", file_ids)

    def message(self, column_id: str, permalinks: str | list[str]) -> Self:
        """Add a message field."""
        return self.add_field(column_id, "message", permalinks)

    def rating(self, column_id: str, value: int) -> Self:
        """Add a rating field."""
        return self.add_field(column_id, "rating", value)

    def timestamp(self, column_id: str, unix_timestamp: int | float) -> Self:
        """Add a timestamp field."""
        return self.add_field(column_id, "timestamp", unix_timestamp)

    def channel(self, column_id: str, channel_ids: str | list[str]) -> Self:
        """Add a channel field."""
        return self.add_field(column_id, "channel", channel_ids)

    def vote(self, column_id: str, value: int) -> Self:
        """Add a vote field."""
        return self.add_field(column_id, "vote", value)

    def canvas(self, column_id: str, canvas_ids: str | list[str]) -> Self:
        """Add a canvas field."""
        return self.add_field(column_id, "canvas", canvas_ids)

    def build(self) -> list[dict[str, Any]]:
        """Build the fields list for add_item or update_item."""
        if not self._fields:
            raise ValueError("Item must have at least one field")
        return self._fields

    def build_cells(self, row_id: str) -> list[dict[str, Any]]:
        """Build cells list for update_item with a specific row_id.

        Args:
            row_id: The item/row ID to update

        """
        cells = []
        for field in self._fields:
            cell = field.copy()
            cell["row_id"] = row_id
            cells.append(cell)
        return cells

    def build_create_cells(self) -> list[dict[str, Any]]:
        """Build cells list for creating a new item via update_item."""
        cells = []
        for field in self._fields:
            cell = field.copy()
            cell["row_id_to_create"] = True
            cells.append(cell)
        return cells


def batch_create_items(
    items: list[ItemBuilder | list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Create cells for batch item creation via update_item.

    This helper generates cells with row_id_to_create for creating
    multiple items in a single update_item call.

    Args:
        items: List of ItemBuilder instances or field lists

    Returns:
        List of cells ready for update_item

    Example:
        >>> cells = batch_create_items([
        ...     ItemBuilder().text("Col1", "Task 1").user("Col2", "U123"),
        ...     ItemBuilder().text("Col1", "Task 2").user("Col2", "U456"),
        ... ])
        >>> await client.update_item(list_id="F123", cells=cells)

    """
    all_cells = []
    for item in items:
        if isinstance(item, ItemBuilder):
            all_cells.extend(item.build_create_cells())
        else:
            # Assume it's a list of field dicts
            for field in item:
                cell = field.copy()
                cell["row_id_to_create"] = True
                all_cells.append(cell)
    return all_cells
