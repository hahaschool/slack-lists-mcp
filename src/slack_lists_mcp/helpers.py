"""Helper functions for Slack Lists field formatting.

These utilities simplify the creation of properly formatted field values
for the Slack Lists API.
"""

from enum import Enum
from typing import Any


class FieldType(str, Enum):
    """Supported Slack Lists field types."""

    TEXT = "text"
    SELECT = "select"
    USER = "user"
    DATE = "date"
    NUMBER = "number"
    CHECKBOX = "checkbox"
    LINK = "link"
    EMAIL = "email"
    PHONE = "phone"
    RATING = "rating"
    TIMESTAMP = "timestamp"
    CHANNEL = "channel"
    ATTACHMENT = "attachment"
    MESSAGE = "message"
    VOTE = "vote"
    CANVAS = "canvas"
    REFERENCE = "reference"


class AccessLevel(str, Enum):
    """Slack Lists access levels."""

    READ = "read"
    WRITE = "write"
    OWNER = "owner"


def make_rich_text(text: str) -> list[dict[str, Any]]:
    """Convert plain text to Slack rich_text format.

    Args:
        text: Plain text string to convert

    Returns:
        Rich text block structure ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "rich_text": make_rich_text("Hello World")}

    """
    return [
        {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "text", "text": text}],
                },
            ],
        },
    ]


def make_link(url: str, display_name: str | None = None) -> list[dict[str, Any]]:
    """Create a properly formatted link field value.

    Args:
        url: The URL to link to
        display_name: Optional display text for the link

    Returns:
        Link field structure ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "link": make_link("https://example.com", "Example")}

    """
    link_obj: dict[str, Any] = {"original_url": url}
    if display_name:
        link_obj["display_name"] = display_name
        link_obj["display_as_url"] = False
    return [link_obj]


def make_select(option_ids: str | list[str]) -> list[str]:
    """Create a properly formatted select field value.

    Args:
        option_ids: Single option ID or list of option IDs

    Returns:
        List of option IDs ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "select": make_select("OptABC123")}

    """
    if isinstance(option_ids, str):
        return [option_ids]
    return list(option_ids)


def make_user(user_ids: str | list[str]) -> list[str]:
    """Create a properly formatted user field value.

    Args:
        user_ids: Single user ID or list of user IDs

    Returns:
        List of user IDs ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "user": make_user("U123456")}

    """
    if isinstance(user_ids, str):
        return [user_ids]
    return list(user_ids)


def make_date(dates: str | list[str]) -> list[str]:
    """Create a properly formatted date field value.

    Args:
        dates: Single date string (YYYY-MM-DD) or list of date strings

    Returns:
        List of date strings ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "date": make_date("2024-12-31")}

    """
    if isinstance(dates, str):
        return [dates]
    return list(dates)


def make_number(numbers: int | float | list[int | float]) -> list[float]:
    """Create a properly formatted number field value.

    Args:
        numbers: Single number or list of numbers

    Returns:
        List of numbers ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "number": make_number(42)}

    """
    if isinstance(numbers, (int, float)):
        return [float(numbers)]
    return [float(n) for n in numbers]


def make_checkbox(checked: bool) -> bool:
    """Create a properly formatted checkbox field value.

    Args:
        checked: Whether the checkbox is checked

    Returns:
        Boolean value ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "checkbox": make_checkbox(True)}

    """
    return bool(checked)


def make_rating(rating: int) -> list[int]:
    """Create a properly formatted rating field value.

    Args:
        rating: Rating value (typically 1-5)

    Returns:
        List containing the rating value ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "rating": make_rating(4)}

    """
    return [int(rating)]


def make_timestamp(unix_timestamp: int | float) -> list[int]:
    """Create a properly formatted timestamp field value.

    Args:
        unix_timestamp: Unix timestamp in seconds

    Returns:
        List containing the timestamp ready for Slack API

    Example:
        >>> import time
        >>> field = {"column_id": "Col123", "timestamp": make_timestamp(int(time.time()))}

    """
    return [int(unix_timestamp)]


def make_channel(channel_ids: str | list[str]) -> list[str]:
    """Create a properly formatted channel field value.

    Args:
        channel_ids: Single channel ID or list of channel IDs

    Returns:
        List of channel IDs ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "channel": make_channel("C123456")}

    """
    if isinstance(channel_ids, str):
        return [channel_ids]
    return list(channel_ids)


def make_email(emails: str | list[str]) -> list[str]:
    """Create a properly formatted email field value.

    Args:
        emails: Single email or list of emails

    Returns:
        List of emails ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "email": make_email("user@example.com")}

    """
    if isinstance(emails, str):
        return [emails]
    return list(emails)


def make_phone(phones: str | list[str]) -> list[str]:
    """Create a properly formatted phone field value.

    Args:
        phones: Single phone number or list of phone numbers

    Returns:
        List of phone numbers ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "phone": make_phone("+1-555-1234")}

    """
    if isinstance(phones, str):
        return [phones]
    return list(phones)


def make_attachment(file_ids: str | list[str]) -> list[str]:
    """Create a properly formatted attachment field value.

    Args:
        file_ids: Single file ID or list of file IDs

    Returns:
        List of file IDs ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "attachment": make_attachment("F1234567890")}

    """
    if isinstance(file_ids, str):
        return [file_ids]
    return list(file_ids)


def make_message(permalinks: str | list[str]) -> list[str]:
    """Create a properly formatted message field value.

    Args:
        permalinks: Single Slack message permalink or list of permalinks

    Returns:
        List of message permalinks ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "message": make_message("https://team.slack.com/archives/C123/p123")}

    """
    if isinstance(permalinks, str):
        return [permalinks]
    return list(permalinks)


def make_vote(vote_value: int) -> list[int]:
    """Create a properly formatted vote field value.

    Args:
        vote_value: Vote count or value

    Returns:
        List containing the vote value ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "vote": make_vote(5)}

    """
    return [int(vote_value)]


def make_canvas(canvas_ids: str | list[str]) -> list[str]:
    """Create a properly formatted canvas field value.

    Args:
        canvas_ids: Single canvas ID or list of canvas IDs

    Returns:
        List of canvas IDs ready for Slack API

    Example:
        >>> field = {"column_id": "Col123", "canvas": make_canvas("F1234567890")}

    """
    if isinstance(canvas_ids, str):
        return [canvas_ids]
    return list(canvas_ids)


def extract_text(rich_text: list[dict[str, Any]] | None) -> str:
    """Extract plain text from Slack rich_text Block Kit format.

    This is useful for reading item values returned by the API,
    which are in rich_text format, and converting them to plain text.

    Args:
        rich_text: Rich text blocks from Slack API response

    Returns:
        Extracted plain text string

    Example:
        >>> item = await client.get_item(list_id="F123", item_id="Rec123")
        >>> for field in item["item"]["fields"]:
        ...     if "rich_text" in field:
        ...         text = extract_text(field["rich_text"])
        ...         print(text)

    """
    if not rich_text:
        return ""

    texts = []
    for block in rich_text:
        if block.get("type") == "rich_text":
            for element in block.get("elements", []):
                if element.get("type") == "rich_text_section":
                    for sub_element in element.get("elements", []):
                        if sub_element.get("type") == "text":
                            texts.append(sub_element.get("text", ""))
                        elif sub_element.get("type") == "link":
                            # Include link text or URL
                            texts.append(
                                sub_element.get("text", sub_element.get("url", ""))
                            )
                        elif sub_element.get("type") == "user":
                            texts.append(f"<@{sub_element.get('user_id', '')}>")
                        elif sub_element.get("type") == "channel":
                            texts.append(f"<#{sub_element.get('channel_id', '')}>")
                elif element.get("type") == "rich_text_list":
                    # Handle bulleted/numbered lists
                    for item in element.get("elements", []):
                        if item.get("type") == "rich_text_section":
                            for sub_element in item.get("elements", []):
                                if sub_element.get("type") == "text":
                                    texts.append(sub_element.get("text", ""))
                elif element.get("type") == "rich_text_preformatted":
                    # Handle code blocks
                    for sub_element in element.get("elements", []):
                        if sub_element.get("type") == "text":
                            texts.append(sub_element.get("text", ""))
                elif element.get("type") == "rich_text_quote":
                    # Handle quotes
                    for sub_element in element.get("elements", []):
                        if sub_element.get("type") == "text":
                            texts.append(sub_element.get("text", ""))

    return "".join(texts)


def make_field(
    column_id: str,
    value: Any,
    field_type: str | FieldType = "text",
) -> dict[str, Any]:
    """Create a complete field dictionary for add/update operations.

    This is a convenience function that creates the full field structure
    with automatic type handling.

    Args:
        column_id: The column ID from list structure
        value: The value to set (auto-formatted based on field_type)
        field_type: One of: text, select, user, date, number, checkbox,
                   link, email, phone, rating, timestamp, channel,
                   attachment, message, vote, canvas

    Returns:
        Complete field dictionary ready for initial_fields or cells

    Example:
        >>> fields = [
        ...     make_field("Col1", "Task Name", "text"),
        ...     make_field("Col2", "U123456", "user"),
        ...     make_field("Col3", True, "checkbox"),
        ...     make_field("Col4", 4, "rating"),
        ...     make_field("Col5", "F123", FieldType.ATTACHMENT),
        ... ]

    """
    field: dict[str, Any] = {"column_id": column_id}

    # Convert FieldType enum to string if needed
    if isinstance(field_type, FieldType):
        field_type = field_type.value

    if field_type == "text":
        field["rich_text"] = make_rich_text(str(value))
    elif field_type == "select":
        field["select"] = make_select(value)
    elif field_type == "user":
        field["user"] = make_user(value)
    elif field_type == "date":
        field["date"] = make_date(value)
    elif field_type == "number":
        field["number"] = make_number(value)
    elif field_type == "rating":
        field["rating"] = make_rating(value)
    elif field_type == "timestamp":
        field["timestamp"] = make_timestamp(value)
    elif field_type == "channel":
        field["channel"] = make_channel(value)
    elif field_type == "checkbox":
        field["checkbox"] = bool(value)
    elif field_type == "link":
        if isinstance(value, str):
            field["link"] = make_link(value)
        elif isinstance(value, tuple) and len(value) == 2:
            field["link"] = make_link(value[0], value[1])
        else:
            field["link"] = value
    elif field_type == "email":
        field["email"] = make_email(value)
    elif field_type == "phone":
        field["phone"] = make_phone(value)
    elif field_type == "attachment":
        field["attachment"] = make_attachment(value)
    elif field_type == "message":
        field["message"] = make_message(value)
    elif field_type == "vote":
        field["vote"] = make_vote(value)
    elif field_type == "canvas":
        field["canvas"] = make_canvas(value)
    else:
        # For unknown types, set directly
        field[field_type] = value

    return field
