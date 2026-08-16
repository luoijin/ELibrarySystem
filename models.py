"""
models.py
=========

Lightweight data classes representing the core entities of the
ELibrary System: ``User``, ``Book`` and ``Transaction``.

These classes are optional convenience wrappers (as permitted by the
specification) around the raw ``sqlite3.Row`` objects returned by
``database.py`` queries. They provide typed, IDE-friendly attribute
access and small computed properties (e.g. a book's availability
status) without introducing an ORM dependency.
"""

from dataclasses import dataclass
from typing import Optional

from utils import calculate_fine, is_overdue


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
        )

    @property
    def is_librarian(self) -> bool:
        return self.role == "librarian"

    @property
    def is_patron(self) -> bool:
        return self.role == "patron"


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
            return calculate_fine(self.due_date)
        return self.fine
