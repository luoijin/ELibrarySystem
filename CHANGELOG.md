# Changelog — SQLite Rewrite vs. Original JSON Prototype

This document compares the rewritten ELibrary System against the
original JSON-based prototype (`import os.txt`, referencing
`books.json`, `users.json`, `borrows.json`, `favorites.json`).

## Storage Layer

| Area | Original (JSON) | Rewrite (SQLite) | Why |
|---|---|---|---|
| Data files | Four separate JSON files (`books.json`, `users.json`, `borrows.json`, `favorites.json`) read/written ad hoc | Single `elibrary.db` SQLite database with three tables: `users`, `books`, `transactions` | JSON files have no schema enforcement, no transactional guarantees, and are prone to becoming out of sync with each other (e.g. a borrow record referencing a deleted book). SQLite provides atomic writes, foreign keys and a single source of truth. |
| Schema | Implicit, defined by whatever keys happened to be written to each JSON file | Explicit `CREATE TABLE` statements with typed columns and `CHECK` / `FOREIGN KEY` constraints | Makes invalid states (e.g. an unknown role, or a transaction pointing at a non-existent book) impossible at the database layer instead of only at the application layer. |
| Seeding | Manual/ad hoc, inconsistent between files | `database.initialize_database()` creates tables and seeds 25 books plus the two required accounts exactly once, on first run, idempotently | Guarantees the app is immediately usable after a fresh clone, every time, without manual setup steps. |

## Features Added

- **Fine calculation** — `$10.00`/day overdue rate, computed both at
  return time (stored on the transaction) and live for still-borrowed
  books (computed against today's date). This did not exist in the
  original prototype at all.
- **Overdue Alerts view** — a dedicated librarian screen listing every
  currently overdue loan with patron contact info, days overdue and
  fine due. Not present in the original.
- **Patron "My Fines" view** — outstanding fine total plus fine
  history. Not present in the original.
- **Referential-integrity checks** — a patron with active borrowings
  cannot be deleted; a book with any copy currently checked out cannot
  be deleted. The original prototype had no such protection.
- **Search** — books can be searched by title, author, ISBN *or*
  category from both the librarian and patron dashboards.

## Features Removed

- **Favorites** — the `favorites.json` / incomplete `Database` class
  for favorites from the original prototype has been removed entirely,
  per the project instructions. It was explicitly out of scope.

## UI / UX Changes

- **No emojis** anywhere in the interface (the original used emojis in
  places).
- **Consistent blue accent** (`#1F6AA5`) applied via a single global
  style module (`styles.py`) instead of colours/fonts being set
  per-widget throughout the code.
- **Formal typography** — Century Gothic font family, with a small
  fixed set of font sizes (heading/subheading/body/small) instead of
  ad hoc sizes scattered through the original UI code.
- **Consistent spacing and corner radii** driven by shared `PADDING`
  and `CORNER_RADIUS` constants.
- **Resizable, appropriately sized window** (1100×700, with a sane
  minimum size) as specified.

## Code Quality / Architecture Changes

- **Modular structure** — the original prototype's logic was contained
  in a small number of tightly-coupled files mixing UI and JSON I/O.
  The rewrite separates concerns into `database.py` (persistence),
  `models.py` (typed data classes), `utils.py` (date/fine/hashing
  helpers), `styles.py` (visual language) and three dedicated GUI
  modules (`gui/login.py`, `gui/admin_dashboard.py`,
  `gui/patron_dashboard.py`), coordinated by a slim `main.py`
  controller.
- **Authentication** — replaced hard-coded admin credentials and
  JSON-based user lookups with a single `database.authenticate_user()`
  function backed by the `users` table, with SHA-256 password hashing
  (see README "Assumptions").
- **Error handling** — all database-facing operations in the GUI are
  wrapped with `try/except` and surfaced to the user via
  `tkinter.messagebox`, instead of failing silently or crashing.
- **Docstrings** — every module and public function includes a
  docstring describing its purpose, arguments and return values,
  following PEP 8 conventions.

## Dependencies

- Original: `customtkinter` (plus ad hoc JSON file handling using the
  standard library).
- Rewrite: `customtkinter` only (SQLite access via the standard
  library `sqlite3` module; tables via the standard library
  `tkinter.ttk` module). No new third-party dependency was introduced.
