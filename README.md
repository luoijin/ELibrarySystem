# ELibrary System

A university library management application built with Python and
CustomTkinter, backed by a SQLite database. It supports two roles,
librarian (admin) and patron (student/faculty), each with a dedicated
dashboard.

This is a full rewrite of an earlier JSON-based prototype. See
[CHANGELOG.md](CHANGELOG.md) for a detailed comparison between the two
versions.

---

## 1. Features

### Librarian (admin)

- **Book management** — add, edit, delete books; search by title,
  author, ISBN or category; view total/available copies and status.
- **Patron management** — register new patrons; edit or delete
  existing patrons (deletion is blocked while a patron has active
  borrowings).
- **Circulation** — check a book out to a patron (due date is
  automatically set to 14 days from today; available copies decrease
  by one); return a book (available copies increase by one; an
  overdue fine is calculated automatically).
- **Overdue alerts** — a dedicated view listing every currently
  overdue loan, with patron contact details, days overdue and fine
  due.

### Patron (student/faculty)

- **Browse books** — search and view the full catalogue, including
  live availability.
- **My borrowed books** — view currently checked-out books, due
  dates, and the current fine (if any), updated live against today's
  date.
- **My fines** — a summary of outstanding fines on active loans and a
  history of past fines from returned books.
- **My account** — view personal account details.

Checkout and return are performed by the librarian only, on behalf of
the patron. This mirrors typical university library workflows and is
consistent with the specification (circulation is described as a
librarian action).

---

## 2. Project Structure

```
ELibrarySystem/
├── main.py                  # Entry point and screen controller
├── database.py               # SQLite connection, schema, seeding, data access
├── models.py                  # Optional data classes (User, Book, Transaction)
├── styles.py                  # Global UI style constants (colors, fonts, spacing)
├── utils.py                   # Date utilities, fine calculation, password hashing
├── gui/
│   ├── __init__.py
│   ├── login.py                # Login screen
│   ├── admin_dashboard.py      # Librarian dashboard (books, patrons, circulation, overdue)
│   └── patron_dashboard.py     # Patron dashboard (browse, borrowed, fines, account)
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

`elibrary.db` (the SQLite database file) is **not** shipped with the
project — it is created automatically, with schema and mock data, the
first time you run `main.py`.

---

## 3. Setup Instructions

### Prerequisites

- Python 3.9 or later (tested with Python 3.12).
- `tkinter` — this ships with most standard Python installations. On
  some Linux distributions it must be installed separately, e.g.:
  ```bash
  sudo apt-get install python3-tk
  ```

### Install and run

```bash
# 1. Clone or unzip the project, then move into the project folder
cd ELibrarySystem

# 2. (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python3 main.py
```

On first launch, `elibrary.db` is created automatically in the project
folder and seeded with:

- 25 books across 9 categories (Computer Science, Mathematics,
  Physics, Chemistry, Biology, Economics, Philosophy, History,
  Literature, Language).
- One librarian account.
- One patron account with student ID `23065360`.

---

## 4. Default Login Credentials

| Role      | Username     | Password   |
|-----------|--------------|------------|
| Librarian | `librarian`  | `admin123` |
| Patron    | `23065360`   | `patron123`|

---

## 5. How to Use the System

### As a librarian

1. Log in with the librarian credentials above.
2. Use the sidebar to navigate between **Books**, **Patrons**,
   **Circulation** and **Overdue Alerts**.
3. **Books** — click *Add Book* to register a new title, or select a
   row and click *Edit Selected* / *Delete Selected*. Use the search
   box to filter by title, author, ISBN or category.
4. **Patrons** — click *Register New Patron* to create an account, or
   select a row and click *Edit Selected* / *Delete Selected*. A
   patron with active borrowings cannot be deleted.
5. **Circulation** — choose a patron and an available book from the
   dropdowns and click *Checkout*. The due date (today + 14 days) is
   set automatically. The table below lists all currently borrowed
   books; select one and click *Return Selected Book* to process a
   return (any overdue fine is calculated and shown before you
   confirm).
6. **Overdue Alerts** — review every loan that is currently past its
   due date, along with the patron's contact information and the fine
   currently owed.

### As a patron

1. Log in with the patron credentials above (or any patron account
   registered by a librarian).
2. **Browse Books** — search the catalogue and see availability.
3. **My Borrowed Books** — see what you currently have checked out,
   due dates, and the live fine for anything overdue.
4. **My Fines** — see your outstanding fine total and a history of
   fines from past returns.
5. **My Account** — view your registered account details.

---

## 6. Design Decisions

- **Global style module (`styles.py`)** — every colour, font and
  spacing value used in the UI is defined once in `styles.py` and
  imported everywhere else. No widget hard-codes a colour, font or
  dimension. This satisfies the requirement to centralise the visual
  language and makes re-theming trivial.
- **`ttk.Treeview` for tables** — CustomTkinter has no built-in table
  widget. Rather than hand-roll one with rows of `CTkLabel`s (fragile
  and slow for larger lists), the standard library's
  `tkinter.ttk.Treeview` is used and re-styled via `ttk.Style` using
  the same colour/font constants from `styles.py`, so it visually
  matches the rest of the application. `ttk` ships with `tkinter`
  itself (which CustomTkinter depends on), so this does **not**
  introduce a dependency beyond `customtkinter`.
- **SQLite schema** — three tables exactly as specified: `users`,
  `books`, `transactions`. `transactions` stores `user_id` and
  `book_id` as foreign keys and records `checkout_date`, `due_date`,
  `return_date`, `fine` and `status` (`'borrowed'` or `'returned'`),
  which is sufficient to answer every requirement (active loans,
  overdue loans, fine history) with plain SQL queries.
- **Data access functions live in `database.py`** — rather than adding
  a separate repository/DAO file not mentioned in the specification,
  all SQL query functions are grouped in `database.py` alongside the
  connection/schema/seeding logic, consistent with the specified
  module list.

---

## 7. Assumptions

The specification left a few details unstated. The following
assumptions were made and are documented here as requested:

1. **Password storage.** The original prompt did not specify how
   passwords should be stored. Rather than reproduce plain-text
   password storage from the original prototype, passwords are hashed
   with SHA-256 (Python's built-in `hashlib`, no new dependency) before
   being written to the database. Default seeded logins are unaffected
   — you still log in with the plain-text passwords listed above.
2. **Fine currency.** Fines are displayed in US dollars (`$`) at a
   flat rate of `$10.00` per overdue day, as specified. No currency
   conversion or localisation is implemented.
3. **Fine "payment."** The specification asks for fine *calculation*
   and *display*, not fine collection/payment tracking. Fines are
   therefore calculated and shown but there is no "mark as paid"
   workflow, since it was not requested.
4. **Editing total copies.** When a librarian edits a book and changes
   `total_copies`, `available_copies` is adjusted by the same delta
   (e.g. raising total copies by 2 also raises available copies by 2),
   floored at zero. This was not specified explicitly but is the only
   way to keep the two figures consistent.
5. **Deleting books with active loans.** Not explicitly covered by the
   specification, but for the same referential-integrity reason given
   for patrons, a book cannot be deleted while any copy is currently
   checked out.
6. **Checkout/return performed by librarian only.** The specification
   describes checkout/return as something "the librarian selects" —
   patrons therefore have read-only visibility into their own loans
   and fines, with no self-checkout feature, since this was not
   requested.
7. **Font availability.** `Century Gothic` is used as specified in
   `styles.py`. If it is not installed on the host operating system,
   Tkinter/CustomTkinter will silently substitute a comparable system
   font; no bundled font file is included.
8. **No `favorites` feature.** Per the original project instructions,
   the `favorites` concept from the old JSON prototype was dropped
   entirely and is not present anywhere in this rewrite.

---

## 8. Dependencies

Only one external package is required:

```
customtkinter
```

(`tkinter`/`ttk` and `sqlite3` are part of the Python standard
library.)
