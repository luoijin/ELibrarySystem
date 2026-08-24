"""
models.py
=========

Lightweight data classes representing the core entities of the
ELibrary System: ``User``, ``Book`` and ``Transaction``.

These classes are optional convenience wrappers (as permitted by the
specification) around the raw ``sqlite3.Row`` objects returned by
``database.py`` queries. They provide typed, IDE-friendly attribute
access and small computed properties (e.g. a book's availability
status, a patron's borrowing policy) without introducing an ORM
dependency.
"""

from dataclasses import dataclass
from typing import Optional

from utils import calculate_fine, is_overdue, get_policy, patron_type_label, DEFAULT_PATRON_TYPE


@dataclass
class User:
    """Represents a row in the ``users`` table."""

    id: int
    username: str
    password: str
    role: str
    full_name: str
    email: Optional[str] = None
    student_id: Optional[str] = None
    contact: Optional[str] = None
    patron_type: str = DEFAULT_PATRON_TYPE

    @classmethod
    def from_row(cls, row) -> "User":
        """Build a ``User`` from a ``sqlite3.Row``."""
        return cls(
            id=row["id"],
            username=row["username"],
            password=row["password"],
            role=row["role"],
            full_name=row["full_name"],
            email=row["email"],
            student_id=row["student_id"],
            contact=row["contact"],
            patron_type=row["patron_type"] if "patron_type" in row.keys() and row["patron_type"] else DEFAULT_PATRON_TYPE,
        )

    @property
    def is_librarian(self) -> bool:
        return self.role == "librarian"

    @property
    def is_patron(self) -> bool:
        return self.role == "patron"

    @property
    def patron_type_display(self) -> str:
        """Human-readable patron type label (e.g. 'Student')."""
        return patron_type_label(self.patron_type)

    @property
    def policy(self) -> dict:
        """This patron's borrowing policy (loan days, fine rate, max loans)."""
        return get_policy(self.patron_type)


@dataclass
class Book:
    """Represents a row in the ``books`` table."""

    id: int
    title: str
    author: str
    isbn: str
    publisher: Optional[str]
    year: Optional[int]
    category: str
    genre: str
    total_copies: int
    available_copies: int

    @classmethod
    def from_row(cls, row) -> "Book":
        """Build a ``Book`` from a ``sqlite3.Row``."""
        return cls(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            isbn=row["isbn"],
            publisher=row["publisher"],
            year=row["year"],
            category=row["category"],
            genre=row["genre"] if "genre" in row.keys() else "",
            total_copies=row["total_copies"],
            available_copies=row["available_copies"],
        )

    @property
    def status(self) -> str:
        """Return a human-readable availability status."""
        return "Available" if self.available_copies > 0 else "Unavailable"


@dataclass
class Transaction:
    """Represents a row in the ``transactions`` table."""

    id: int
    user_id: int
    book_id: int
    checkout_date: str
    due_date: str
    return_date: Optional[str]
    fine: float
    status: str

    # Joined/denormalised display fields (populated by queries that use JOIN)
    book_title: Optional[str] = None
    patron_name: Optional[str] = None
    patron_type: str = DEFAULT_PATRON_TYPE

    @classmethod
    def from_row(cls, row) -> "Transaction":
        """Build a ``Transaction`` from a ``sqlite3.Row``."""
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            book_id=row["book_id"],
            checkout_date=row["checkout_date"],
            due_date=row["due_date"],
            return_date=row["return_date"],
            fine=row["fine"],
            status=row["status"],
            book_title=row["book_title"] if "book_title" in row.keys() else None,
            patron_name=row["patron_name"] if "patron_name" in row.keys() else None,
            patron_type=row["patron_type"] if "patron_type" in row.keys() and row["patron_type"] else DEFAULT_PATRON_TYPE,
        )

    @property
    def is_active(self) -> bool:
        return self.status == "borrowed"

    @property
    def is_overdue_now(self) -> bool:
        """Whether this active loan is currently overdue (as of today)."""
        return self.is_active and is_overdue(self.due_date)

    @property
    def current_fine(self) -> float:
        """Fine as of today for active loans, or the stored fine for returned ones."""
        if self.is_active:
            return calculate_fine(self.due_date, patron_type=self.patron_type)
        return self.fine
