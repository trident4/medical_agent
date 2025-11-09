"""
Utility modules for the medical assistant application.
"""

from app.utils.pagination import PaginatedResponse, Paginator, PaginationParams
from datetime import datetime, date


def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date."""
    today = date.today()

    # Calculate age
    age = today.year - birth_date.year

    # Adjust age if birthday hasn't occurred this year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1

    return max(0, age)  # Ensure age is not negative


__all__ = [
    "calculate_age",
    "PaginatedResponse",
    "Paginator",
    "PaginationParams",
]
