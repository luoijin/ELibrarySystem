# Changelog

All notable changes to the ELibrary System are documented in this
file, grouped by version.

---

## Version 2.0 — Patron Types, Peso Currency, Genre & CRUD Hardening

This revision builds on the 1.0 SQLite rewrite. It does not change the
storage engine (still SQLite) or the overall architecture; it adds new
fields, business rules and validation, and polishes several UI
behaviours per an updated specification.

### Added

- **`users.patron_type` column** (`student` / `faculty` / `staff`),
  added via `ALTER TABLE` so existing 1.0 databases upgrade in place
  without losing data. Defaults to `student`.
- **`books.genre` column**, added the same way, alongside the existing
  `category` column. Both are now required, independent dropdown
  fields (`BOOK_CATEGORIES` / `BOOK_GENRES` in `utils.py`) in the
  Add/Edit Book form.
- **`BORROW_POLICIES` dictionary** (`utils.py`) defining, per patron
  type, the loan period in days, the daily overdue fine rate, and the
  maximum number of simultaneous active loans. All due-date and fine
  calculations, and the checkout eligibility check, read from this
  single dictionary.
- **Philippine Peso (₱) currency formatting** everywhere money is
  shown (fines, policy summaries), replacing the previous `$` symbol.
- **"View Details" button** on the Books table, plus double-clicking a
  row, opens a read-only pop-up (`BookDetailsDialog`) showing every
  field of the selected book — useful because table columns can
  truncate long titles, authors or publishers.
- **Field-level validation** on every Create/Update form, with clear
  `messagebox` warnings/errors:
  - Books: required Title/Author/ISBN/Category/Genre/Total Copies,
    maximum lengths, unique ISBN, non-negative numeric Total Copies,
    plausible Year, and a guard preventing Total Copies from being
    reduced below the number of copies currently checked out.
  - Patrons: required Full Name/Student ID, unique/length-limited
    Username, minimum-length Password (6+ characters, optional on
    edit), and email format validation when an email is supplied.
- **Patron-type-aware circulation**: the Circulation screen now shows
  each patron's type and their current loan count against their
  maximum directly in the patron picker and in a live hint label;
  checkout is blocked with a clear error once a patron reaches their
  type's maximum simultaneous loans.
- **`get_active_loans_count()`** and an expanded `checkout_book()` in
  `database.py` that looks up the patron's policy and enforces the
  maximum-loans rule at the data-access layer (not just in the UI), so
  the rule is enforced consistently regardless of caller.
- Seed data expanded to **29 books** (previously 25) spanning both
  category and genre, plus a second seeded patron account,
  `faculty1` / `faculty123`, to demonstrate the faculty policy.

### Changed

- **All `Treeview` listing queries now order by `id ASC`** by default
  (`get_all_books`, `search_books`, `get_all_patrons`,
  `get_active_transactions`, `get_overdue_transactions`,
  `get_transaction_history`, `get_transactions_for_user`,
  `get_available_books_for_checkout`) — previously several of these
  ordered by title, full name, or due date instead.
- `calculate_due_date()` and `calculate_fine()` in `utils.py` now
  accept a `patron_type` parameter and look up the relevant policy,
  instead of using the single global `LOAN_PERIOD_DAYS` /
  `DAILY_FINE_RATE` constants from 1.0.
- `add_patron()` / `update_patron()` now accept and persist
  `patron_type`; the Patron form includes a Patron Type dropdown.
- `add_book()` / `update_book()` now accept and persist `genre`; the
  Book form's free-text Category field was replaced with a Category
  dropdown, and a new Genre dropdown was added.
- Books and Patrons tables display a `genre` / `Type` column
  respectively; the Circulation and Overdue Alerts tables display each
  transaction's patron type and use the patron's own fine rate instead
  of a single flat rate.
- `models.py` data classes (`User`, `Book`, `Transaction`) updated
  with `patron_type` / `genre` fields and a few convenience properties
  (`patron_type_display`, `policy`, `current_fine` now
  patron-type-aware).

### Removed

- The flat, one-size-fits-all `LOAN_PERIOD_DAYS = 14` and
  `DAILY_FINE_RATE = 10.00` module-level constants (superseded by
  `BORROW_POLICIES`); they are no longer used anywhere in the code.
- The `$`-based `format_currency()` implementation (superseded by the
  ₱-based version).

### Notes

- No "Demo Account" or similar text was found anywhere in the 1.0
  codebase, so there was nothing to remove for that requirement; the
  login screen's credential hint already showed only the real seeded
  usernames/passwords.
- `PRAGMA foreign_keys = ON` and the three-table design (`users`,
  `books`, `transactions`) are unchanged from 1.0.

---

## Version 1.0 — JSON → SQLite Rewrite

The original prototype persisted all data in four separate JSON files
(`books.json`, `users.json`, `borrows.json`, `favorites.json`). This
version replaced that storage layer entirely and introduced role-based
dashboards built on CustomTkinter.

### Added

- **SQLite persistence** (`elibrary.db`) with three tables — `users`,
  `books`, `transactions` — created automatically on first run via
  `CREATE TABLE IF NOT EXISTS`, with `PRAGMA foreign_keys = ON` for
  referential integrity between transactions and their user/book.
- **Mock data seeding**: 25 sample books across a range of categories,
  one librarian account (`librarian` / `admin123`), and one patron
  account (`23065360` / `patron123`), inserted only when the relevant
  table is empty so re-running the app never duplicates data.
- **SHA-256 password hashing** (`utils.hash_password` /
  `verify_password`), using only the standard-library `hashlib`
  module — no new dependency introduced.
- **Role-based dashboards**: a `LoginFrame` authenticates against the
  `users` table and routes to either `AdminDashboard` (librarian) or
  `PatronDashboard` (patron) based on the authenticated row's `role`.
- **Librarian dashboard**: Book management (add/edit/delete/search),
  Patron management (register/edit/delete, blocked while a patron has
  active borrowings), Circulation (checkout/return with a 14-day due
  date and a flat $10/day overdue fine), and a dedicated Overdue
  Alerts view.
- **Patron dashboard**: Browse Books, My Borrowed Books, My Fines (with
  a live-calculated current fine for still-borrowed books), and My
  Account.
- **Global style module** (`styles.py`) centralising every colour,
  font and spacing constant used across the UI (`PRIMARY_COLOR`,
  `BG_COLOR`, `TEXT_COLOR`, `BUTTON_HOVER_COLOR`, `FONT_FAMILY`
  ("Century Gothic"), `FONT_SIZES`, `PADDING`, `CORNER_RADIUS`, etc.),
  plus a `configure_ttk_style()` helper so `ttk.Treeview` tables match
  the CustomTkinter visual language. No widget hard-codes a colour,
  font or dimension directly.
- **Modular structure**: `main.py` (entry point/controller),
  `database.py` (SQLite layer), `models.py` (optional dataclasses),
  `styles.py` (style constants), `utils.py` (helpers), and
  `gui/login.py` / `gui/admin_dashboard.py` /
  `gui/patron_dashboard.py`.

### Removed

- All JSON file persistence (`books.json`, `users.json`,
  `borrows.json`, `favorites.json`) and any code that read or wrote
  them.
- The `favorites` concept from the original prototype — not part of
  the specification for this rewrite and intentionally not carried
  over.

### Why the rewrite

JSON files provide no referential integrity (nothing stops a
transaction from pointing at a deleted book or user), no atomic
multi-row writes (a crash mid-save can corrupt the file), and no
efficient querying (every read/filter/sort had to be done in Python
after loading the entire file into memory). SQLite solves all three
with foreign keys, transactions, and SQL `WHERE`/`ORDER BY`, while
remaining a single embedded file with no separate server to install or
run — a good match for a desktop CustomTkinter application.
