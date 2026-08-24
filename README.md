# ELibrary System

A university library management application built with Python and
CustomTkinter, backed by a SQLite database. It supports two roles —
**librarian (admin)** and **patron (student / faculty / staff)** —
each with a dedicated dashboard.

This is version 2.0, an enhancement of the original SQLite rewrite.
See [CHANGELOG.md](CHANGELOG.md) for a detailed, version-by-version
comparison.

---

## 1. Features

### Librarian (admin)

- **Book management** — add, edit, delete books; search by title,
  author, ISBN, category or genre; view total/available copies and
  status; a **View Details** button opens a pop-up with every field
  of a book (useful when a title, author or publisher is too long to
  read in the table).
- **Patron management** — register new patrons with a patron type
  (Student / Faculty / Staff); edit or delete existing patrons
  (deletion is blocked while a patron has active borrowings).
- **Circulation** — check a book out to a patron. The due date and
  the maximum number of simultaneous loans are both determined by the
  patron's type (see the borrowing policy table below); available
  copies decrease by one. Returning a book increases available copies
  by one and calculates an overdue fine automatically, using the
  patron's own daily fine rate.
- **Overdue alerts** — a dedicated view listing every currently
  overdue loan, with patron contact details, patron type, days
  overdue and fine due, in ₱ (Philippine Pesos).

### Patron (student / faculty / staff)

- **Browse books** — search and view the full catalogue, including
  category, genre and live availability.
- **My borrowed books** — view currently checked-out books, due
  dates, and the current fine (if any), updated live against today's
  date and calculated using the patron's own policy.
- **My fines** — a summary of outstanding fines on active loans and a
  history of past fines from returned books.
- **My account** — view personal account details, patron type, and a
  summary of the applicable borrowing policy (loan period, daily fine
  rate, maximum loans, current active loans).

Checkout and return are performed by the librarian only, on behalf of
the patron. This mirrors typical university library workflows and is
consistent with the specification (circulation is described as a
librarian action).

### Borrowing policy by patron type

| Patron Type | Loan Period | Daily Overdue Fine | Max Simultaneous Loans |
|---|---|---|---|
| Student | 14 days | ₱10.00 | 10 |
| Faculty | 120 days | ₱5.00 | 30 |
| Staff | 30 days | ₱8.00 | 15 |

These values live in a single dictionary (`BORROW_POLICIES` in
`utils.py`) so the policy can be changed in one place without hunting
for hard-coded numbers throughout the GUI layer.

---

## 2. Project Structure

```
ELibrarySystem/
├── main.py                  # Entry point and screen controller
├── database.py               # SQLite connection, schema, migration, seeding, data access
├── models.py                  # Optional data classes (User, Book, Transaction)
├── styles.py                  # Global UI style constants (colors, fonts, spacing)
├── utils.py                   # Date utilities, borrowing policy, fine calc, validation, currency
├── gui/
│   ├── __init__.py
│   ├── login.py                # Login screen
│   ├── admin_dashboard.py      # Librarian dashboard + Book/Patron dialogs
│   └── patron_dashboard.py     # Patron dashboard
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

`elibrary.db` is created automatically in this same folder the first
time the application runs; it is not shipped in the ZIP.

---

## 3. Setup Instructions

1. **Requirements**: Python 3.9+ with Tkinter available (Tkinter ships
   with most standard Python installations; on some Linux
   distributions it must be installed separately, e.g.
   `sudo apt install python3-tk`).

2. **Clone or extract** the project folder.

3. **Install dependencies** (only one third-party package is used):

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:

   ```bash
   python main.py
   ```

   On first run, `elibrary.db` is created automatically in the
   project folder, the schema is built, and mock data (books, a
   librarian account and two patron accounts) is seeded. On every
   subsequent run, the existing database is reused as-is — no data is
   ever duplicated or overwritten.

   If you have an `elibrary.db` file from an earlier (1.0) version of
   this project, simply place it in the project folder before running
   `main.py`. The application detects the older schema and adds the
   new `patron_type` and `genre` columns automatically via `ALTER
   TABLE`, without touching any of your existing data.

---

## 4. Default Login Credentials

| Role | Username | Password |
|---|---|---|
| Librarian | `librarian` | `admin123` |
| Patron (Student) | `23065360` | `patron123` |
| Patron (Faculty) | `faculty1` | `faculty123` |

---

## 5. How to Use the System

### As a Librarian

1. Log in with the librarian credentials above.
2. **Books** tab: search the catalogue, add a new book (Title,
   Author, ISBN, Publisher, Year, Category, Genre and Total Copies —
   Category and Genre are dropdowns), edit or delete a selected book,
   or click **View Details** to see every field of a book in a
   pop-up.
3. **Patrons** tab: register a new patron (Username, Password, Full
   Name, Email, Student ID, Contact, and Patron Type), edit or delete
   an existing patron. Deletion is blocked while the patron has an
   active loan.
4. **Circulation** tab: pick a patron and an available book, then
   click **Checkout**. The due date and the patron's current loan
   count against their maximum are shown once a patron is selected.
   Select a currently-borrowed book from the table and click **Return
   Selected Book** to process a return and see any overdue fine.
5. **Overdue Alerts** tab: view every currently overdue loan, with
   contact details and the fine due, to follow up with patrons.

### As a Patron

1. Log in with a patron's credentials.
2. **Browse Books**: search the full catalogue by title, author,
   ISBN, category or genre.
3. **My Borrowed Books**: see what you currently have checked out,
   due dates, and any current fine.
4. **My Fines**: see your total outstanding fine and a history of
   past fines.
5. **My Account**: view your details, patron type, and the borrowing
   policy that applies to you.

---

## 6. Data Validation

All Create/Update forms validate their inputs before writing to the
database and show a clear message box if something is wrong:

- **Books**: Title and Author are required (≤ 200 / ≤ 100 characters);
  ISBN is required, ≤ 20 characters, and must be unique; Category and
  Genre are required dropdown selections; Total Copies must be a
  non-negative whole number and cannot be reduced below the number of
  copies currently checked out; Year (if given) must be a plausible
  whole number.
- **Patrons**: Username is required for new patrons, ≤ 50 characters,
  and must be unique; Password is required for new patrons and must
  be at least 6 characters (optional on edit — leave blank to keep the
  existing password); Full Name and Student ID are required; Email, if
  provided, must match a valid email format.
- **Deletion safeguards**: a book cannot be deleted while any copy is
  checked out; a patron cannot be deleted while they have an active
  loan.
- **Circulation**: checkout is blocked if the book has no available
  copies, or if the patron has already reached their patron type's
  maximum number of simultaneous loans.

---

## 7. Change Log

See [CHANGELOG.md](CHANGELOG.md) for the full, itemised history,
including the original JSON → SQLite rewrite and this version's
enhancements (patron types, ₱ currency, genre field, CRUD validation,
View Details, ascending ID ordering, and the removal of any "demo"
wording).

---

## 8. Assumptions

The following assumptions were made where the specification was silent
or ambiguous:

1. **Circulation is librarian-only.** The specification lists checkout
   and return as actions the librarian performs ("librarian selects a
   patron and a book"), so the patron dashboard is read-only with
   respect to circulation; patrons view their borrowed books and fines
   but do not self-checkout.
2. **`patron_type` on the librarian's own account.** The `users` table
   has one `patron_type` column shared by all rows for schema
   simplicity. It is meaningless for librarian accounts and is simply
   ignored by the UI and business logic for that role; it defaults to
   `'student'` and has no visible or functional effect on a librarian
   login.
3. **Editing a book's Total Copies** adjusts Available Copies by the
   same delta (e.g. raising Total Copies by 2 also raises Available
   Copies by 2), floored so it never goes negative and capped so it
   never exceeds the new Total Copies. Total Copies cannot be reduced
   below the number of copies currently checked out.
4. **Category vs. Genre.** "Category" is treated as the broad academic
   subject (Computer Science, Mathematics, ...) and "Genre" as a more
   specific literary/topical classification (Fiction, Biography,
   Textbook, ...). Both are required, independent dropdown fields, as
   requested; a book may reasonably have any combination of the two
   (e.g. Category = Literature, Genre = Science Fiction).
5. **Student ID doubles as a contact/lookup field** for patrons and is
   required (matching the original prototype's use of student ID as a
   login identifier for the seeded patron account); it is not
   currently enforced as numeric-only, since faculty/staff IDs may use
   a different format (the seeded faculty account uses `FAC-1001`).
6. **Currency formatting** uses `₱{amount:,.2f}` (thousands separator,
   two decimal places) everywhere money is displayed, including a
   ₱0.00 fine when nothing is due, so the currency symbol is always
   visible for consistency.
7. **"Sort IDs ascending" applies to every Treeview**, including
   Circulation's active-loans table and the Overdue Alerts table
   (previously sorted by due date), to comply literally with the
   requirement that all tables display in ascending ID order by
   default.
8. No "Demo Account" or similar wording was present anywhere in the
   codebase prior to this revision (the login screen already showed
   only the real seeded credentials), so there was nothing to remove;
   this is noted here for completeness against the requirements
   checklist.
