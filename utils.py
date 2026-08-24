"""
utils.py
========

Small, dependency-free helper functions and reference constants shared
across the application: password hashing, date handling, patron-type
borrowing policies, fine calculation, currency formatting and form
validation helpers.

Keeping this logic in one place avoids duplicating date-arithmetic,
policy and validation code across the librarian and patron dashboards,
and makes the borrowing policy easy to audit/change in a single
location.
"""

import hashlib
import re
from datetime import datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"

# ---------------------------------------------------------------------------
# Currency
# ---------------------------------------------------------------------------
# The system uses Philippine Pesos throughout. Centralising the symbol and
# the formatting function means every screen displays money the same way.
CURRENCY_SYMBOL = "\u20b1"  # PHP peso sign (PHP - Philippine Peso)


def format_currency(amount: float) -> str:
    """Format a numeric amount as a Peso currency string with 2 decimals."""
    return f"{CURRENCY_SYMBOL}{amount:,.2f}"


# ---------------------------------------------------------------------------
# Patron types & borrowing policy
# ---------------------------------------------------------------------------
# Each patron type has its own loan period, daily fine rate and maximum
# number of simultaneous active loans. All circulation logic (due-date
# calculation, fine calculation, checkout eligibility) reads from this
# single dictionary so the policy can be changed in one place without
# hunting for hard-coded numbers throughout the GUI layer.
PATRON_TYPES = ("student", "faculty", "staff")
DEFAULT_PATRON_TYPE = "student"

BORROW_POLICIES = {
    "student": {"label": "Student", "loan_days": 14, "fine_per_day": 10.0, "max_loans": 10},
    "faculty": {"label": "Faculty", "loan_days": 120, "fine_per_day": 5.0, "max_loans": 30},
    "staff": {"label": "Staff", "loan_days": 30, "fine_per_day": 8.0, "max_loans": 15},
}

PATRON_TYPE_LABELS = [BORROW_POLICIES[t]["label"] for t in PATRON_TYPES]
_LABEL_TO_PATRON_TYPE = {BORROW_POLICIES[t]["label"]: t for t in PATRON_TYPES}


def patron_type_label(patron_type: str) -> str:
    """Return the display label for a stored patron_type value."""
    return BORROW_POLICIES.get(patron_type, BORROW_POLICIES[DEFAULT_PATRON_TYPE])["label"]


def patron_type_from_label(label: str) -> str:
    """Return the stored patron_type value for a display label."""
    return _LABEL_TO_PATRON_TYPE.get(label, DEFAULT_PATRON_TYPE)


def get_policy(patron_type: str) -> dict:
    """Return the borrowing policy dict for a patron type, defaulting to student."""
    return BORROW_POLICIES.get(patron_type, BORROW_POLICIES[DEFAULT_PATRON_TYPE])


# ---------------------------------------------------------------------------
# Book reference data (dropdown options)
# ---------------------------------------------------------------------------
# "category" is a broad academic classification; "genre" is a more specific
# literary/topical classification. Both are required, separate fields on
# every book and are presented as dropdowns in the Add/Edit Book form so
# librarians cannot introduce inconsistent free-text values.
BOOK_CATEGORIES = [
    "Computer Science",
    "Mathematics",
    "Physics",
    "Chemistry",
    "Biology",
    "Economics",
    "Philosophy",
    "History",
    "Literature",
    "Language",
    "Art",
    "Music",
    "Engineering",
    "Business",
    "Psychology",
]

BOOK_GENRES = [
    "Fiction",
    "Non-Fiction",
    "Thriller",
    "Mystery",
    "Romance",
    "Science Fiction",
    "Fantasy",
    "Biography",
    "History",
    "Poetry",
    "Drama",
    "Reference",
    "Textbook",
]

# ---------------------------------------------------------------------------
# Field-length limits used by form validation
# ---------------------------------------------------------------------------
MAX_LENGTHS = {
    "book_title": 200,
    "book_author": 100,
    "book_isbn": 20,
    "book_publisher": 150,
    "username": 50,
    "full_name": 100,
    "email": 100,
    "student_id": 30,
    "contact": 30,
}

MIN_PASSWORD_LENGTH = 6

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_blank(value: str) -> bool:
    """Return True if the given string is None, empty, or whitespace only."""
    return value is None or value.strip() == ""


def is_valid_email(email: str) -> bool:
    """Return True if the string looks like a syntactically valid email address."""
    if is_blank(email):
        return False
    return bool(_EMAIL_PATTERN.match(email.strip()))


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

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


def calculate_due_date(checkout_date_str: str = None, patron_type: str = DEFAULT_PATRON_TYPE) -> str:
    """Calculate the due date for a checkout based on the patron's loan period.

    Args:
        checkout_date_str: The checkout date as ``YYYY-MM-DD``. Defaults
            to today if not provided.
        patron_type: One of ``student``, ``faculty`` or ``staff``. The
            number of loan days is looked up from ``BORROW_POLICIES``.

    Returns:
        The due date as a ``YYYY-MM-DD`` string.
    """
    base = parse_date(checkout_date_str) if checkout_date_str else today()
    loan_days = get_policy(patron_type)["loan_days"]
    return (base + timedelta(days=loan_days)).strftime(DATE_FORMAT)


def calculate_fine(due_date_str: str, return_date_str: str = None, patron_type: str = DEFAULT_PATRON_TYPE) -> float:
    """Calculate the overdue fine for a loan using the patron's daily rate.

    Args:
        due_date_str: The due date of the loan, as ``YYYY-MM-DD``.
        return_date_str: The date the book was (or would be) returned,
            as ``YYYY-MM-DD``. If ``None``, today's date is used, which
            allows the caller to preview the fine for a book that is
            still on loan.
        patron_type: One of ``student``, ``faculty`` or ``staff``. The
            daily fine rate is looked up from ``BORROW_POLICIES``.

    Returns:
        The fine amount as a float, rounded to 2 decimal places. Zero
        if the book was not overdue.
    """
    due_date = parse_date(due_date_str)
    reference_date = parse_date(return_date_str) if return_date_str else today()

    overdue_days = (reference_date - due_date).days
    if overdue_days <= 0:
        return 0.0

    fine_per_day = get_policy(patron_type)["fine_per_day"]
    return round(overdue_days * fine_per_day, 2)


def is_overdue(due_date_str: str) -> bool:
    """Return True if the given due date has passed and today has not returned it."""
    return parse_date(due_date_str) < today()
