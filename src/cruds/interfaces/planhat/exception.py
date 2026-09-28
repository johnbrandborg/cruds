"""
Custom Exceptions specifically for an Interface
"""

from typing import Any


class PlanhatUpsertError(Exception):
    """One or more records failed during a Planhat bulk operation."""

    def __init__(self, errors: dict[str, list[Any]]) -> None:
        self.errors = errors
        super().__init__(f"Bulk upsert errors: {errors}")
