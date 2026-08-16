"""
database.py
============

SQLite persistence layer for the ELibrary System.

This module owns the connection to ``elibrary.db``, creates the schema
on first run and seeds the database with mock data (books, a librarian
account and a patron account) so that the application is immediately
usable after installation.

Design decisions
-----------------
* A single SQLite file (``elibrary.db``) replaces the four separate
  JSON files used by the original prototype (books.json, users.json,
  borrows.json, favorites.json). SQLite gives us referential
  integrity (foreign keys), atomic transactions and concurrent-safe
  reads/writes, none of which plain JSON files provide.
* Three tables are used, exactly as required by the specification:
  ``users``, ``books`` and ``transactions``. The ``favorites`` concept
  from the original prototype is intentionally NOT carried over, per
  the project instructions.
* Passwords are stored as SHA-256 hashes rather than plain text. This
  was not explicitly requested, but storing credentials in plain text
  would be a poor practice to reproduce in a rewrite; the assumption
  is documented in the README. Hashing uses only the Python standard
  library (``hashlib``), so it does not introduce a new dependency.
"""

import sqlite3
from pathlib import Path

from utils import hash_password, today_str, days_from_today_str

DB_FILENAME = "elibrary.db"
DB_PATH = Path(__file__).resolve().parent / DB_FILENAME


def get_connection() -> sqlite3.Connection:
    """Create and return a new SQLite connection.

    Foreign key enforcement is switched on explicitly because SQLite
    disables it by default for backward-compatibility reasons.

    Returns:
        A ``sqlite3.Connection`` configured with ``row_factory`` set to
        ``sqlite3.Row`` so query results can be accessed by column name.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    """Create tables (if needed) and seed mock data on first run.

    This function is idempotent: it can be called every time the
    application starts. Table creation uses ``CREATE TABLE IF NOT
    EXISTS`` and seeding only happens when the relevant table is empty,
    so re-running the application never duplicates data.
    """
    connection = get_connection()
    try:
        _create_schema(connection)
        _seed_users(connection)
        _seed_books(connection)
        connection.commit()
    finally:
        connection.close()


def _create_schema(connection: sqlite3.Connection) -> None:
    """Create the users, books and transactions tables."""
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('librarian', 'patron')),
            full_name TEXT NOT NULL,
            email TEXT,
            student_id TEXT UNIQUE,
            contact TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT NOT NULL UNIQUE,
            publisher TEXT,
            year INTEGER,
            category TEXT NOT NULL,
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            checkout_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            fine REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL CHECK (status IN ('borrowed', 'returned')),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
        """
    )


def _seed_users(connection: sqlite3.Connection) -> None:
    """Insert the default librarian and patron accounts if none exist."""
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM users")
    if cursor.fetchone()["count"] > 0:
        return

    default_users = [
        (
            "librarian",
            hash_password("admin123"),
            "librarian",
            "Head Librarian",
            "librarian@university.edu",
            None,
            "555-0100",
        ),
        (
            "23065360",
            hash_password("patron123"),
            "patron",
            "Alex Morgan",
            "alex.morgan@university.edu",
            "23065360",
            "555-0199",
        ),
    ]
    cursor.executemany(
        """
        INSERT INTO users (username, password, role, full_name, email, student_id, contact)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        default_users,
    )


def _seed_books(connection: sqlite3.Connection) -> None:
    """Insert at least 20 sample books across various categories."""
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM books")
    if cursor.fetchone()["count"] > 0:
        return

    # (title, author, isbn, publisher, year, category, total_copies)
    sample_books = [
        ("Introduction to Algorithms", "Thomas H. Cormen", "9780262033848", "MIT Press", 2009, "Computer Science", 4),
        ("Clean Code", "Robert C. Martin", "9780132350884", "Prentice Hall", 2008, "Computer Science", 3),
        ("Design Patterns", "Erich Gamma", "9780201633610", "Addison-Wesley", 1994, "Computer Science", 2),
        ("Structure and Interpretation of Computer Programs", "Harold Abelson", "9780262510875", "MIT Press", 1996, "Computer Science", 2),
        ("Database System Concepts", "Abraham Silberschatz", "9780078022159", "McGraw-Hill", 2019, "Computer Science", 3),
        ("Calculus", "James Stewart", "9781285740621", "Cengage Learning", 2015, "Mathematics", 5),
        ("Linear Algebra Done Right", "Sheldon Axler", "9783319110790", "Springer", 2015, "Mathematics", 3),
        ("Introduction to Probability", "Joseph K. Blitzstein", "9781466575578", "CRC Press", 2014, "Mathematics", 2),
        ("Discrete Mathematics and Its Applications", "Kenneth Rosen", "9780073383095", "McGraw-Hill", 2012, "Mathematics", 4),
        ("Physics for Scientists and Engineers", "Raymond Serway", "9781133947271", "Cengage Learning", 2013, "Physics", 3),
        ("Cosmos", "Carl Sagan", "9780345539434", "Ballantine Books", 2013, "Physics", 2),
        ("Organic Chemistry", "Paula Yurkanis Bruice", "9780134042282", "Pearson", 2016, "Chemistry", 3),
        ("Campbell Biology", "Lisa A. Urry", "9780134093413", "Pearson", 2016, "Biology", 4),
        ("The Selfish Gene", "Richard Dawkins", "9780198788607", "Oxford University Press", 2016, "Biology", 2),
        ("A Brief History of Time", "Stephen Hawking", "9780553380163", "Bantam Books", 1998, "Physics", 3),
        ("Principles of Economics", "N. Gregory Mankiw", "9781305585126", "Cengage Learning", 2017, "Economics", 4),
        ("Freakonomics", "Steven D. Levitt", "9780061234002", "William Morrow", 2009, "Economics", 2),
        ("The Republic", "Plato", "9780140455113", "Penguin Classics", 2007, "Philosophy", 2),
        ("Meditations", "Marcus Aurelius", "9780140449334", "Penguin Classics", 2006, "Philosophy", 2),
        ("A People's History of the United States", "Howard Zinn", "9780062397348", "Harper Perennial", 2015, "History", 3),
        ("Sapiens: A Brief History of Humankind", "Yuval Noah Harari", "9780062316097", "Harper", 2015, "History", 4),
        ("To Kill a Mockingbird", "Harper Lee", "9780061120084", "Harper Perennial", 2006, "Literature", 3),
        ("1984", "George Orwell", "9780451524935", "Signet Classics", 1961, "Literature", 5),
        ("Pride and Prejudice", "Jane Austen", "9780141439518", "Penguin Classics", 2003, "Literature", 3),
        ("The Elements of Style", "William Strunk Jr.", "9780205309023", "Pearson", 1999, "Language", 2),
    ]

    rows = [
        (title, author, isbn, publisher, year, category, total, total)
        for (title, author, isbn, publisher, year, category, total) in sample_books
    ]
    cursor.executemany(
        """
        INSERT INTO books (title, author, isbn, publisher, year, category, total_copies, available_copies)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


# ===========================================================================
# Data access layer
# ===========================================================================
# The functions below provide a small, explicit query API used by the GUI
# modules. They intentionally avoid an ORM so the SQL is transparent and
# easy to audit; each function opens its own short-lived connection so the
# GUI layer never has to manage connection lifecycles directly.


# ---------------------------------------------------------------------------
# Users / authentication
# ---------------------------------------------------------------------------

def authenticate_user(username: str, password: str):
    """Validate credentials and return the matching user row, or None."""
    from utils import verify_password

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row and verify_password(password, row["password"]):
            return row
        return None
    finally:
        connection.close()


def get_all_patrons():
    """Return all users with the 'patron' role, ordered by full name."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE role = 'patron' ORDER BY full_name COLLATE NOCASE"
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_user_by_id(user_id: int):
    """Return a single user row by id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()
    finally:
        connection.close()


def username_exists(username: str, exclude_id: int = None) -> bool:
    """Check whether a username is already taken (optionally excluding one id)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if exclude_id is not None:
            cursor.execute(
                "SELECT COUNT(*) AS count FROM users WHERE username = ? AND id != ?",
                (username, exclude_id),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) AS count FROM users WHERE username = ?", (username,)
            )
        return cursor.fetchone()["count"] > 0
    finally:
        connection.close()


def add_patron(username, password_hash, full_name, email, student_id, contact) -> int:
    """Insert a new patron and return the new row id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, password, role, full_name, email, student_id, contact)
            VALUES (?, ?, 'patron', ?, ?, ?, ?)
            """,
            (username, password_hash, full_name, email, student_id, contact),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_patron(user_id, full_name, email, student_id, contact, password_hash=None):
    """Update a patron's details. Password is only updated if provided."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if password_hash:
            cursor.execute(
                """
                UPDATE users
                SET full_name = ?, email = ?, student_id = ?, contact = ?, password = ?
                WHERE id = ?
                """,
                (full_name, email, student_id, contact, password_hash, user_id),
            )
        else:
            cursor.execute(
                """
                UPDATE users
                SET full_name = ?, email = ?, student_id = ?, contact = ?
                WHERE id = ?
                """,
                (full_name, email, student_id, contact, user_id),
            )
        connection.commit()
    finally:
        connection.close()


def patron_has_active_borrowings(user_id: int) -> bool:
    """Return True if the patron currently has any un-returned books."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS count FROM transactions WHERE user_id = ? AND status = 'borrowed'",
            (user_id,),
        )
        return cursor.fetchone()["count"] > 0
    finally:
        connection.close()


def delete_patron(user_id: int):
    """Delete a patron. Caller must first check patron_has_active_borrowings."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = ? AND role = 'patron'", (user_id,))
        connection.commit()
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Books
# ---------------------------------------------------------------------------

def get_all_books():
    """Return all books ordered by title."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM books ORDER BY title COLLATE NOCASE")
        return cursor.fetchall()
    finally:
        connection.close()


def search_books(search_term: str):
    """Search books by title, author, ISBN or category (case-insensitive)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        term = f"%{search_term.strip()}%"
        cursor.execute(
            """
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?
            ORDER BY title COLLATE NOCASE
            """,
            (term, term, term, term),
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_book_by_id(book_id: int):
    """Return a single book row by id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        return cursor.fetchone()
    finally:
        connection.close()


def isbn_exists(isbn: str, exclude_id: int = None) -> bool:
    """Check whether an ISBN is already registered (optionally excluding one id)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if exclude_id is not None:
            cursor.execute(
                "SELECT COUNT(*) AS count FROM books WHERE isbn = ? AND id != ?",
                (isbn, exclude_id),
            )
        else:
            cursor.execute("SELECT COUNT(*) AS count FROM books WHERE isbn = ?", (isbn,))
        return cursor.fetchone()["count"] > 0
    finally:
        connection.close()


def add_book(title, author, isbn, publisher, year, category, total_copies) -> int:
    """Insert a new book (available_copies starts equal to total_copies)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO books (title, author, isbn, publisher, year, category, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, author, isbn, publisher, year, category, total_copies, total_copies),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_book(book_id, title, author, isbn, publisher, year, category, total_copies):
    """Update a book's details.

    ``available_copies`` is adjusted by the same delta as
    ``total_copies`` so that currently checked-out copies remain
    accounted for correctly (e.g. raising total_copies by 1 also
    raises available_copies by 1; lowering it lowers availability,
    never below zero).
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT total_copies, available_copies FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError("Book not found.")

        delta = total_copies - row["total_copies"]
        new_available = max(0, row["available_copies"] + delta)

        cursor.execute(
            """
            UPDATE books
            SET title = ?, author = ?, isbn = ?, publisher = ?, year = ?,
                category = ?, total_copies = ?, available_copies = ?
            WHERE id = ?
            """,
            (title, author, isbn, publisher, year, category, total_copies, new_available, book_id),
        )
        connection.commit()
    finally:
        connection.close()


def book_has_active_borrowings(book_id: int) -> bool:
    """Return True if any copy of this book is currently checked out."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS count FROM transactions WHERE book_id = ? AND status = 'borrowed'",
            (book_id,),
        )
        return cursor.fetchone()["count"] > 0
    finally:
        connection.close()


def delete_book(book_id: int):
    """Delete a book. Caller must first check book_has_active_borrowings."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        connection.commit()
    finally:
        connection.close()


def get_distinct_categories():
    """Return a sorted list of distinct book categories."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT category FROM books ORDER BY category COLLATE NOCASE")
        return [row["category"] for row in cursor.fetchall()]
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Transactions (circulation)
# ---------------------------------------------------------------------------

def checkout_book(user_id: int, book_id: int, checkout_date: str, due_date: str) -> int:
    """Record a checkout: insert a transaction and decrement available copies.

    Raises:
        ValueError: If the book has no available copies.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT available_copies FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        if row is None or row["available_copies"] <= 0:
            raise ValueError("No available copies for this book.")

        cursor.execute(
            """
            INSERT INTO transactions (user_id, book_id, checkout_date, due_date, return_date, fine, status)
            VALUES (?, ?, ?, ?, NULL, 0, 'borrowed')
            """,
            (user_id, book_id, checkout_date, due_date),
        )
        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
            (book_id,),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def return_book(transaction_id: int, return_date: str, fine: float):
    """Record a return: update the transaction and increment available copies."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT book_id, status FROM transactions WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError("Transaction not found.")
        if row["status"] == "returned":
            raise ValueError("This book has already been returned.")

        cursor.execute(
            """
            UPDATE transactions
            SET return_date = ?, fine = ?, status = 'returned'
            WHERE id = ?
            """,
            (return_date, fine, transaction_id),
        )
        cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
            (row["book_id"],),
        )
        connection.commit()
    finally:
        connection.close()


def get_active_transactions():
    """Return all currently-borrowed transactions with book/patron details."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT t.*, b.title AS book_title, b.isbn AS book_isbn,
                   u.full_name AS patron_name, u.student_id AS student_id
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            JOIN users u ON u.id = t.user_id
            WHERE t.status = 'borrowed'
            ORDER BY t.due_date ASC
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_overdue_transactions():
    """Return all currently-borrowed transactions whose due date has passed."""
    from utils import today_str

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT t.*, b.title AS book_title, b.isbn AS book_isbn,
                   u.full_name AS patron_name, u.student_id AS student_id,
                   u.contact AS patron_contact
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            JOIN users u ON u.id = t.user_id
            WHERE t.status = 'borrowed' AND t.due_date < ?
            ORDER BY t.due_date ASC
            """,
            (today_str(),),
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_transaction_history(limit: int = None):
    """Return all transactions (borrowed and returned) with details, most recent first."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = """
            SELECT t.*, b.title AS book_title, b.isbn AS book_isbn,
                   u.full_name AS patron_name, u.student_id AS student_id
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            JOIN users u ON u.id = t.user_id
            ORDER BY t.checkout_date DESC, t.id DESC
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        connection.close()


def get_transactions_for_user(user_id: int):
    """Return all transactions for a specific patron, most recent first."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT t.*, b.title AS book_title, b.author AS book_author, b.isbn AS book_isbn
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            WHERE t.user_id = ?
            ORDER BY t.checkout_date DESC, t.id DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_available_books_for_checkout():
    """Return books that currently have at least one available copy."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM books WHERE available_copies > 0 ORDER BY title COLLATE NOCASE"
        )
        return cursor.fetchall()
    finally:
        connection.close()
