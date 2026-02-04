"""Tests for the helpers module."""

import pytest

from slack_lists_mcp.helpers import (
    make_date,
    make_field,
    make_link,
    make_number,
    make_rich_text,
    make_select,
    make_user,
)


def test_make_rich_text():
    """Test rich text creation."""
    result = make_rich_text("Hello World")

    assert len(result) == 1
    assert result[0]["type"] == "rich_text"
    assert result[0]["elements"][0]["type"] == "rich_text_section"
    assert result[0]["elements"][0]["elements"][0]["text"] == "Hello World"


def test_make_link_simple():
    """Test simple link creation."""
    result = make_link("https://example.com")

    assert len(result) == 1
    assert result[0]["original_url"] == "https://example.com"
    assert "display_name" not in result[0]


def test_make_link_with_display_name():
    """Test link with display name."""
    result = make_link("https://example.com", "Example Site")

    assert len(result) == 1
    assert result[0]["original_url"] == "https://example.com"
    assert result[0]["display_name"] == "Example Site"
    assert result[0]["display_as_url"] is False


def test_make_select_single():
    """Test single select value."""
    result = make_select("OptABC123")

    assert result == ["OptABC123"]


def test_make_select_list():
    """Test multiple select values."""
    result = make_select(["Opt1", "Opt2"])

    assert result == ["Opt1", "Opt2"]


def test_make_user_single():
    """Test single user."""
    result = make_user("U123456")

    assert result == ["U123456"]


def test_make_user_list():
    """Test multiple users."""
    result = make_user(["U123", "U456"])

    assert result == ["U123", "U456"]


def test_make_date_single():
    """Test single date."""
    result = make_date("2024-12-31")

    assert result == ["2024-12-31"]


def test_make_date_list():
    """Test multiple dates."""
    result = make_date(["2024-01-01", "2024-12-31"])

    assert result == ["2024-01-01", "2024-12-31"]


def test_make_number_int():
    """Test integer number."""
    result = make_number(42)

    assert result == [42.0]


def test_make_number_float():
    """Test float number."""
    result = make_number(3.14)

    assert result == [3.14]


def test_make_number_list():
    """Test multiple numbers."""
    result = make_number([1, 2, 3])

    assert result == [1.0, 2.0, 3.0]


def test_make_field_text():
    """Test make_field with text type."""
    result = make_field("Col123", "Task Name", "text")

    assert result["column_id"] == "Col123"
    assert "rich_text" in result
    assert result["rich_text"][0]["elements"][0]["elements"][0]["text"] == "Task Name"


def test_make_field_checkbox():
    """Test make_field with checkbox type."""
    result = make_field("Col123", True, "checkbox")

    assert result["column_id"] == "Col123"
    assert result["checkbox"] is True


def test_make_field_select():
    """Test make_field with select type."""
    result = make_field("Col123", "OptABC", "select")

    assert result["column_id"] == "Col123"
    assert result["select"] == ["OptABC"]


def test_make_field_user():
    """Test make_field with user type."""
    result = make_field("Col123", "U123456", "user")

    assert result["column_id"] == "Col123"
    assert result["user"] == ["U123456"]


def test_make_field_link_string():
    """Test make_field with link type (string)."""
    result = make_field("Col123", "https://example.com", "link")

    assert result["column_id"] == "Col123"
    assert result["link"][0]["original_url"] == "https://example.com"


def test_make_field_link_tuple():
    """Test make_field with link type (tuple)."""
    result = make_field("Col123", ("https://example.com", "Example"), "link")

    assert result["column_id"] == "Col123"
    assert result["link"][0]["original_url"] == "https://example.com"
    assert result["link"][0]["display_name"] == "Example"


def test_make_field_email():
    """Test make_field with email type."""
    result = make_field("Col123", "test@example.com", "email")

    assert result["column_id"] == "Col123"
    assert result["email"] == ["test@example.com"]


def test_make_field_phone():
    """Test make_field with phone type."""
    result = make_field("Col123", "+1-555-1234", "phone")

    assert result["column_id"] == "Col123"
    assert result["phone"] == ["+1-555-1234"]


def test_make_field_unknown_type():
    """Test make_field with unknown type passes through."""
    result = make_field("Col123", ["custom_value"], "custom")

    assert result["column_id"] == "Col123"
    assert result["custom"] == ["custom_value"]


# Tests for new helper functions


def test_make_checkbox_true():
    """Test checkbox with True value."""
    from slack_lists_mcp.helpers import make_checkbox

    result = make_checkbox(True)
    assert result is True


def test_make_checkbox_false():
    """Test checkbox with False value."""
    from slack_lists_mcp.helpers import make_checkbox

    result = make_checkbox(False)
    assert result is False


def test_make_checkbox_truthy():
    """Test checkbox with truthy value."""
    from slack_lists_mcp.helpers import make_checkbox

    result = make_checkbox(1)
    assert result is True


def test_make_rating():
    """Test rating field creation."""
    from slack_lists_mcp.helpers import make_rating

    result = make_rating(4)
    assert result == [4]


def test_make_rating_float():
    """Test rating field with float (converts to int)."""
    from slack_lists_mcp.helpers import make_rating

    result = make_rating(3.7)
    assert result == [3]


def test_make_timestamp():
    """Test timestamp field creation."""
    from slack_lists_mcp.helpers import make_timestamp

    result = make_timestamp(1704067200)
    assert result == [1704067200]


def test_make_timestamp_float():
    """Test timestamp field with float (converts to int)."""
    from slack_lists_mcp.helpers import make_timestamp

    result = make_timestamp(1704067200.5)
    assert result == [1704067200]


def test_make_channel_single():
    """Test channel field with single ID."""
    from slack_lists_mcp.helpers import make_channel

    result = make_channel("C123456")
    assert result == ["C123456"]


def test_make_channel_list():
    """Test channel field with list of IDs."""
    from slack_lists_mcp.helpers import make_channel

    result = make_channel(["C123", "C456"])
    assert result == ["C123", "C456"]


def test_make_email_single():
    """Test email field with single email."""
    from slack_lists_mcp.helpers import make_email

    result = make_email("user@example.com")
    assert result == ["user@example.com"]


def test_make_email_list():
    """Test email field with list of emails."""
    from slack_lists_mcp.helpers import make_email

    result = make_email(["a@example.com", "b@example.com"])
    assert result == ["a@example.com", "b@example.com"]


def test_make_phone_single():
    """Test phone field with single number."""
    from slack_lists_mcp.helpers import make_phone

    result = make_phone("+1-555-1234")
    assert result == ["+1-555-1234"]


def test_make_phone_list():
    """Test phone field with list of numbers."""
    from slack_lists_mcp.helpers import make_phone

    result = make_phone(["+1-555-1234", "+1-555-5678"])
    assert result == ["+1-555-1234", "+1-555-5678"]


def test_make_field_rating():
    """Test make_field with rating type."""
    result = make_field("Col123", 5, "rating")

    assert result["column_id"] == "Col123"
    assert result["rating"] == [5]


def test_make_field_timestamp():
    """Test make_field with timestamp type."""
    result = make_field("Col123", 1704067200, "timestamp")

    assert result["column_id"] == "Col123"
    assert result["timestamp"] == [1704067200]


def test_make_field_channel():
    """Test make_field with channel type."""
    result = make_field("Col123", "C123456", "channel")

    assert result["column_id"] == "Col123"
    assert result["channel"] == ["C123456"]
