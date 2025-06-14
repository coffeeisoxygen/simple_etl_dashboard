"""Common models dan utilities untuk aplikasi ETL Dashboard."""

from datetime import UTC, datetime
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class OperationResult[T](BaseModel):
    """Model untuk hasil operasi yang konsisten di seluruh aplikasi.

    Digunakan untuk membungkus hasil operasi database, service calls,
    dan business logic dengan informasi success/failure yang jelas.
    """

    success: bool
    data: T | None = None
    message: str
    error_code: str | None = None
    error_details: str | None = None

    @classmethod
    def success_result(
        cls, data: T, message: str = "Operation successful"
    ) -> "OperationResult[T]":
        """Create successful operation result."""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_result(
        cls,
        message: str,
        error_code: str | None = None,
        error_details: str | None = None,
    ) -> "OperationResult[T]":
        """Create error operation result."""
        return cls(
            success=False,
            data=None,
            message=message,
            error_code=error_code,
            error_details=error_details,
        )


def normalize_datetime(dt_input: datetime | str, output_format: str = "sqlite") -> str:
    """Normalize datetime untuk consistent storage dan display.

    Args:
        dt_input: DateTime object atau string yang akan dinormalisasi
        output_format: Format output ("sqlite", "display", "iso")

    Returns:
        String datetime dalam format yang diminta

    Raises:
        ValueError: Jika input tidak bisa diparsing
    """
    try:
        if isinstance(dt_input, str):
            # Parse string ke datetime - assume ISO format
            parsed_dt = datetime.fromisoformat(dt_input.replace("Z", "+00:00"))
        else:
            parsed_dt = dt_input

        # Ensure timezone aware - default ke UTC jika tidak ada
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=UTC)

        # Format sesuai kebutuhan
        if output_format == "sqlite":
            # SQLite storage: UTC time tanpa timezone info
            utc_dt = parsed_dt.astimezone(UTC)
            return utc_dt.strftime("%Y-%m-%d %H:%M:%S")
        elif output_format == "display":
            # Display: local time untuk user
            local_dt = parsed_dt.astimezone()
            return local_dt.strftime("%Y-%m-%d %H:%M:%S")
        elif output_format == "iso":
            # ISO format dengan timezone info
            return parsed_dt.isoformat()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    except Exception as e:
        raise ValueError(f"Failed to normalize datetime '{dt_input}': {str(e)}") from e


class DatabaseEntity(BaseModel):
    """Base class untuk database entities dengan simplified date handling."""

    id: int | None = None
    act_date: datetime  # Single activity date - when this record is relevant

    model_config = {
        "from_attributes": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }

    def __init__(self, **data: Any) -> None:
        if "act_date" not in data:
            data["act_date"] = datetime.now(UTC)
        super().__init__(**data)


class ValidationMixin:
    """Mixin untuk common validation methods."""

    @staticmethod
    def validate_not_empty(value: str, field_name: str) -> str:
        """Validate bahwa string tidak kosong."""
        if not value or not value.strip():
            raise ValueError(f"{field_name} tidak boleh kosong")
        return value.strip()

    @staticmethod
    def validate_min_length(value: str, min_length: int, field_name: str) -> str:
        """Validate minimum length untuk string."""
        if len(value) < min_length:
            raise ValueError(f"{field_name} minimal {min_length} karakter")
        return value
