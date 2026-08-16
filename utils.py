"""
utils.py
========

Small, dependency-free helper functions shared across the application:
password hashing, date handling and fine calculation.

Keeping this logic in one place avoids duplicating date-arithmetic and
fine-calculation code across the librarian and patron dashboards, and
makes the fine policy easy to audit/change in a single location.
"""

import hashlib
from datetime import datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"
LOAN_PERIOD_DAYS = 14
DAILY_FINE_RATE = 10.00


def hash_password(raw_password: str) -> str:
    """Hash a plain-text password using SHA-256.

    Args:
        raw_password: The plain-text password to hash.

    Returns:
        The hexadecimal digest of the password.
    """
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored SHA-256 hash."""
    return hash_password(raw_password) == hashed_password


def today() -> datetime:
    """Return today's date (time component stripped)."""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def today_str() -> str:
    """Return today's date formatted as ``YYYY-MM-DD``."""
    return today().strftime(DATE_FORMAT)


def days_from_today_str(days: int) -> str:
    """Return a date ``days`` days from today, formatted as ``YYYY-MM-DD``."""
    return (today() + timedelta(days=days)).strftime(DATE_FORMAT)


def parse_date(date_str: str) -> datetime:
    """Parse a ``YYYY-MM-DD`` string into a ``datetime`` object."""
    return datetime.strptime(date_str, DATE_FORMAT)


def calculate_due_date(checkout_date_str: str = None) -> str:
    """Calculate a due date 14 days after the given checkout date.

    Args:
        checkout_date_str: The checkout date as ``YYYY-MM-DD``. Defaults
            to today if not provided.

    Returns:
        The due date as a ``YYYY-MM-DD`` string.
    """
    base = parse_date(checkout_date_str) if checkout_date_str else today()
    return (base + timedelta(days=LOAN_PERIOD_DAYS)).strftime(DATE_FORMAT)


def calculate_fine(due_date_str: str, return_date_str: str = None) -> float:
    """Calculate the overdue fine for a loan.

    Args:
        due_date_str: The due date of the loan, as ``YYYY-MM-DD``.
        return_date_str: The date the book was (or would be) returned,
            as ``YYYY-MM-DD``. If ``None``, today's date is used, which
            allows the caller to preview the fine for a book that is
            still on loan.

    Returns:
        The fine amount as a float, rounded to 2 decimal places. Zero
        if the book was not overdue.
    """
    due_date = parse_date(due_date_str)
    reference_date = parse_date(return_date_str) if return_date_str else today()

    overdue_days = (reference_date - due_date).days
    if overdue_days <= 0:
        return 0.0

    return round(overdue_days * DAILY_FINE_RATE, 2)


def is_overdue(due_date_str: str) -> bool:
    """Return True if the given due date has passed and today has not returned it."""
    return parse_date(due_date_str) < today()


def format_currency(amount: float) -> str:
    """Format a numeric amount as a currency string with 2 decimal places."""
    return f"${amount:,.2f}"
