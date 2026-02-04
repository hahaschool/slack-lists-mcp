"""Data models for Slack Lists API requests."""

from typing import Any

from pydantic import BaseModel, Field


class FieldData(BaseModel):
    """Field data for adding/updating list items."""

    column_id: str = Field(description="The column ID")
    # Dynamic field based on column type
    rich_text: list[dict[str, Any]] | None = Field(
        default=None,
        description="Rich text content",
    )
    user: list[str] | None = Field(default=None, description="User IDs")
    date: list[str] | None = Field(default=None, description="Date values")
    select: list[str] | None = Field(default=None, description="Option IDs")
    checkbox: bool | None = Field(default=None, description="Checkbox state")
    number: list[float] | None = Field(default=None, description="Number values")
    email: list[str] | None = Field(default=None, description="Email addresses")
    phone: list[str] | None = Field(default=None, description="Phone numbers")
    channel: list[str] | None = Field(default=None, description="Channel IDs")
    rating: list[int] | None = Field(default=None, description="Rating values")
    timestamp: list[int] | None = Field(default=None, description="Unix timestamps")
    attachment: list[str] | None = Field(default=None, description="File IDs")
    link: list[dict[str, str]] | None = Field(default=None, description="Link objects")
    reference: list[str] | None = Field(default=None, description="Reference IDs")


class CellData(BaseModel):
    """Cell data for updating list items."""

    row_id: str | None = Field(
        default=None,
        description="The item/row ID to update (required for updates)",
    )
    row_id_to_create: bool | None = Field(
        default=None,
        description="Set to true to create a new row instead of updating",
    )
    column_id: str = Field(description="The column ID")
    # Dynamic field based on column type (same as FieldData)
    rich_text: list[dict[str, Any]] | None = Field(
        default=None,
        description="Rich text content",
    )
    user: list[str] | None = Field(default=None, description="User IDs")
    date: list[str] | None = Field(default=None, description="Date values")
    select: list[str] | None = Field(default=None, description="Option IDs")
    checkbox: bool | None = Field(default=None, description="Checkbox state")
    number: list[float] | None = Field(default=None, description="Number values")
    email: list[str] | None = Field(default=None, description="Email addresses")
    phone: list[str] | None = Field(default=None, description="Phone numbers")
    channel: list[str] | None = Field(default=None, description="Channel IDs")
    rating: list[int] | None = Field(default=None, description="Rating values")
    timestamp: list[int] | None = Field(default=None, description="Unix timestamps")
    attachment: list[str] | None = Field(default=None, description="File IDs")
    link: list[dict[str, str]] | None = Field(default=None, description="Link objects")
    reference: list[str] | None = Field(default=None, description="Reference IDs")


class AddItemRequest(BaseModel):
    """Request model for adding an item to a list."""

    list_id: str = Field(description="The ID of the list to add the item to")
    initial_fields: list[FieldData | dict[str, Any]] = Field(
        description="List of field data with column_id and appropriate value format",
    )


class UpdateItemRequest(BaseModel):
    """Request model for updating list items."""

    list_id: str = Field(description="The ID of the list containing the items")
    cells: list[CellData | dict[str, Any]] = Field(
        description="List of cell data with row_id, column_id and appropriate value format",
    )


class DeleteItemRequest(BaseModel):
    """Request model for deleting a list item."""

    list_id: str = Field(description="The ID of the list containing the item")
    item_id: str = Field(description="The ID of the item to delete")


class GetItemRequest(BaseModel):
    """Request model for getting a specific list item."""

    list_id: str = Field(description="The ID of the list containing the item")
    item_id: str = Field(description="The ID of the item to retrieve")
    include_is_subscribed: bool = Field(
        default=False,
        description="Include subscription status",
    )


class ListItemsRequest(BaseModel):
    """Request model for listing items in a list."""

    list_id: str = Field(description="The ID of the list to retrieve items from")
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of items to return",
    )
    cursor: str | None = Field(default=None, description="Cursor for pagination")
    archived: bool | None = Field(
        default=None,
        description="Filter for archived items",
    )
    completed_only: bool | None = Field(
        default=None,
        description="Filter for completed items only",
    )
    assignee: str | None = Field(
        default=None,
        description="Filter by assignee user ID",
    )
    sort_by: str | None = Field(
        default=None,
        description="Sort field (created_at, updated_at, due_date, priority)",
    )
    sort_order: str | None = Field(
        default=None,
        description="Sort order (asc, desc)",
    )


class CreateListRequest(BaseModel):
    """Request model for creating a new list."""

    name: str | None = Field(default=None, description="Name of the list")
    description: str | None = Field(
        default=None,
        description="Optional description of the list",
    )
    todo_mode: bool | None = Field(
        default=None,
        description="When True, creates with Completed, Assignee, Due Date columns",
    )
    schema: list[dict[str, Any]] | None = Field(
        default=None,
        description="Column definitions for custom list structure",
    )
    copy_from_list_id: str | None = Field(
        default=None,
        description="ID of an existing list to duplicate",
    )
    include_copied_list_records: bool | None = Field(
        default=None,
        description="Include records when copying from another list",
    )


class ErrorResponse(BaseModel):
    """Model for API error responses."""

    error: str = Field(description="Error message")
    error_code: str | None = Field(default=None, description="Error code")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details",
    )


# Response models are now simple dicts for flexibility
# Use dict[str, Any] for all Slack API responses
