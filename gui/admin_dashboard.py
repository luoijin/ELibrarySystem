"""
gui/admin_dashboard.py
=======================

The librarian (admin) dashboard. Provides four functional areas as
required by the specification:

* Book management (add / edit / delete / search).
* Patron management (register / edit / delete).
* Circulation (checkout and return of books).
* Overdue alerts (a dedicated view of all overdue loans).

Tabular data (book lists, patron lists, transaction lists) is rendered
with ``tkinter.ttk.Treeview``. This is part of Python's standard
``tkinter`` library (the same toolkit CustomTkinter itself is built on)
rather than a third-party package, so it does not introduce a new
dependency beyond ``customtkinter``. Its appearance is re-styled with
``ttk.Style`` so that it matches the global colour/font configuration
in ``styles.py`` instead of using ttk's default look.
"""

from tkinter import messagebox, ttk

import customtkinter as ctk

import database
import styles
import utils


class AdminDashboard(ctk.CTkFrame):
    """Main frame for the librarian role, containing sidebar navigation."""

    NAV_ITEMS = ("Books", "Patrons", "Circulation", "Overdue Alerts")

    def __init__(self, master, current_user, on_logout):
        """Initialise the librarian dashboard.

        Args:
            master: The parent widget.
            current_user: The authenticated librarian ``sqlite3.Row``.
            on_logout: Callback invoked when the librarian logs out.
        """
        super().__init__(master, fg_color=styles.BG_COLOR)
        self.current_user = current_user
        self.on_logout = on_logout
        self.active_nav_button = None

        styles.configure_ttk_style()
        self._build_layout()
        self.show_section("Books")

    # ------------------------------------------------------------------
    # Layout scaffolding
    # ------------------------------------------------------------------
    def _build_layout(self):
        """Build the sidebar and content container."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Sidebar -----------------------------------------------------
        sidebar = ctk.CTkFrame(
            self, fg_color=styles.SIDEBAR_COLOR, width=styles.SIDEBAR_WIDTH, corner_radius=0
        )
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="ELibrary System",
            font=styles.get_font("subheading", "bold"),
            text_color=styles.TEXT_ON_SIDEBAR_COLOR,
        ).pack(pady=(styles.PADDING["lg"], styles.PADDING["xs"]), padx=styles.PADDING["md"])

        ctk.CTkLabel(
            sidebar,
            text=f"Librarian: {self.current_user['full_name']}",
            font=styles.get_font("small"),
            text_color=styles.TEXT_ON_SIDEBAR_COLOR,
            wraplength=styles.SIDEBAR_WIDTH - 32,
        ).pack(pady=(0, styles.PADDING["lg"]), padx=styles.PADDING["md"])

        self.nav_buttons = {}
        for item in self.NAV_ITEMS:
            button = ctk.CTkButton(
                sidebar,
                text=item,
                font=styles.get_font("body"),
                fg_color="transparent",
                hover_color=styles.PRIMARY_HOVER_COLOR,
                text_color=styles.TEXT_ON_SIDEBAR_COLOR,
                anchor="w",
                corner_radius=styles.CORNER_RADIUS["sm"],
                height=styles.BUTTON_HEIGHT,
                command=lambda i=item: self.show_section(i),
            )
            button.pack(fill="x", padx=styles.PADDING["md"], pady=styles.PADDING["xs"])
            self.nav_buttons[item] = button

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(expand=True, fill="both")

        ctk.CTkButton(
            sidebar,
            text="Log Out",
            font=styles.get_font("body", "bold"),
            fg_color=styles.DANGER_COLOR,
            hover_color=styles.DANGER_HOVER_COLOR,
            text_color=styles.TEXT_ON_PRIMARY_COLOR,
            corner_radius=styles.CORNER_RADIUS["sm"],
            height=styles.BUTTON_HEIGHT,
            command=self.on_logout,
        ).pack(fill="x", padx=styles.PADDING["md"], pady=styles.PADDING["lg"])

        # --- Content area --------------------------------------------------
        self.content = ctk.CTkFrame(self, fg_color=styles.BG_COLOR, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=styles.PADDING["lg"], pady=styles.PADDING["lg"])

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _set_active_nav(self, item_name):
        for name, button in self.nav_buttons.items():
            if name == item_name:
                button.configure(fg_color=styles.PRIMARY_COLOR)
            else:
                button.configure(fg_color="transparent")

    def show_section(self, section_name):
        """Switch the content area to the requested section, rebuilding it with fresh data."""
        self._set_active_nav(section_name)
        self._clear_content()

        if section_name == "Books":
            self._build_books_section()
        elif section_name == "Patrons":
            self._build_patrons_section()
        elif section_name == "Circulation":
            self._build_circulation_section()
        elif section_name == "Overdue Alerts":
            self._build_overdue_section()

    def _section_title(self, text):
        ctk.CTkLabel(
            self.content,
            text=text,
            font=styles.get_font("heading", "bold"),
            text_color=styles.TEXT_COLOR,
        ).pack(anchor="w", pady=(0, styles.PADDING["md"]))

    # ------------------------------------------------------------------
    # Books section
    # ------------------------------------------------------------------
    def _build_books_section(self):
        self._section_title("Book Management")

        toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, styles.PADDING["sm"]))

        self.book_search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Search by title, author, ISBN or category",
            font=styles.get_font("body"),
            height=styles.ENTRY_HEIGHT,
            width=360,
        )
        self.book_search_entry.pack(side="left", padx=(0, styles.PADDING["sm"]))
        self.book_search_entry.bind("<Return>", lambda _e: self._refresh_books_table())

        ctk.CTkButton(
            toolbar,
            text="Search",
            font=styles.get_font("body"),
            fg_color=styles.SECONDARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            height=styles.ENTRY_HEIGHT,
            command=self._refresh_books_table,
        ).pack(side="left", padx=(0, styles.PADDING["sm"]))

        ctk.CTkButton(
            toolbar,
            text="Clear",
            font=styles.get_font("body"),
            fg_color=styles.SURFACE_COLOR,
            text_color=styles.TEXT_COLOR,
            hover_color=styles.BORDER_COLOR,
            border_width=styles.BORDER_WIDTH,
            border_color=styles.BORDER_COLOR,
            height=styles.ENTRY_HEIGHT,
            command=self._clear_book_search,
        ).pack(side="left")

        ctk.CTkButton(
            toolbar,
            text="Add Book",
            font=styles.get_font("body", "bold"),
            fg_color=styles.PRIMARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            height=styles.ENTRY_HEIGHT,
            command=self._open_add_book_dialog,
        ).pack(side="right")

        columns = ("id", "title", "author", "isbn", "publisher", "year", "category", "total", "available", "status")
        headings = ("ID", "Title", "Author", "ISBN", "Publisher", "Year", "Category", "Total", "Available", "Status")
        widths = (40, 190, 140, 110, 120, 60, 110, 55, 75, 90)

        table_frame = ctk.CTkFrame(self.content, fg_color=styles.SURFACE_COLOR, corner_radius=styles.CORNER_RADIUS["md"])
        table_frame.pack(fill="both", expand=True, pady=(0, styles.PADDING["sm"]))

        self.books_tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", style="Elib.Treeview"
        )
        for col, heading, width in zip(columns, headings, widths):
            self.books_tree.heading(col, text=heading)
            self.books_tree.column(col, width=width, anchor="w")
        self.books_tree.column("id", anchor="center")
        self.books_tree.column("year", anchor="center")
        self.books_tree.column("total", anchor="center")
        self.books_tree.column("available", anchor="center")
        self.books_tree.column("status", anchor="center")
        self.books_tree.pack(fill="both", expand=True, padx=styles.PADDING["sm"], pady=styles.PADDING["sm"])

        action_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        action_bar.pack(fill="x")

        ctk.CTkButton(
            action_bar,
            text="Edit Selected",
            font=styles.get_font("body"),
            fg_color=styles.SECONDARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            command=self._open_edit_book_dialog,
        ).pack(side="left", padx=(0, styles.PADDING["sm"]))

        ctk.CTkButton(
            action_bar,
            text="Delete Selected",
            font=styles.get_font("body"),
            fg_color=styles.DANGER_COLOR,
            hover_color=styles.DANGER_HOVER_COLOR,
            command=self._delete_selected_book,
        ).pack(side="left")

        self._refresh_books_table()

    def _clear_book_search(self):
        self.book_search_entry.delete(0, "end")
        self._refresh_books_table()

    def _refresh_books_table(self):
        search_term = self.book_search_entry.get().strip()
        rows = database.search_books(search_term) if search_term else database.get_all_books()

        for item in self.books_tree.get_children():
            self.books_tree.delete(item)

        for row in rows:
            status = "Available" if row["available_copies"] > 0 else "Unavailable"
            self.books_tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row["id"],
                    row["title"],
                    row["author"],
                    row["isbn"],
                    row["publisher"] or "",
                    row["year"] or "",
                    row["category"],
                    row["total_copies"],
                    row["available_copies"],
                    status,
                ),
            )

    def _get_selected_book_id(self):
        selection = self.books_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a book from the table first.")
            return None
        return int(selection[0])

    def _open_add_book_dialog(self):
        BookFormDialog(self, on_saved=self._refresh_books_table)

    def _open_edit_book_dialog(self):
        book_id = self._get_selected_book_id()
        if book_id is None:
            return
        book_row = database.get_book_by_id(book_id)
        BookFormDialog(self, on_saved=self._refresh_books_table, existing_book=book_row)

    def _delete_selected_book(self):
        book_id = self._get_selected_book_id()
        if book_id is None:
            return

        if database.book_has_active_borrowings(book_id):
            messagebox.showerror(
                "Cannot Delete",
                "This book cannot be deleted because one or more copies are currently checked out.",
            )
            return

        book_row = database.get_book_by_id(book_id)
        confirmed = messagebox.askyesno(
            "Confirm Deletion", f"Delete '{book_row['title']}' from the catalogue?"
        )
        if confirmed:
            database.delete_book(book_id)
            self._refresh_books_table()

    # ------------------------------------------------------------------
    # Patrons section
    # ------------------------------------------------------------------
    def _build_patrons_section(self):
        self._section_title("Patron Management")

        toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, styles.PADDING["sm"]))

        ctk.CTkButton(
            toolbar,
            text="Register New Patron",
            font=styles.get_font("body", "bold"),
            fg_color=styles.PRIMARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            height=styles.ENTRY_HEIGHT,
            command=self._open_add_patron_dialog,
        ).pack(side="right")

        columns = ("id", "username", "full_name", "email", "student_id", "contact", "active_loans")
        headings = ("ID", "Username", "Full Name", "Email", "Student ID", "Contact", "Active Loans")
        widths = (40, 110, 160, 190, 100, 110, 95)

        table_frame = ctk.CTkFrame(self.content, fg_color=styles.SURFACE_COLOR, corner_radius=styles.CORNER_RADIUS["md"])
        table_frame.pack(fill="both", expand=True, pady=(0, styles.PADDING["sm"]))

        self.patrons_tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", style="Elib.Treeview"
        )
        for col, heading, width in zip(columns, headings, widths):
            self.patrons_tree.heading(col, text=heading)
            self.patrons_tree.column(col, width=width, anchor="w")
        self.patrons_tree.column("id", anchor="center")
        self.patrons_tree.column("active_loans", anchor="center")
        self.patrons_tree.pack(fill="both", expand=True, padx=styles.PADDING["sm"], pady=styles.PADDING["sm"])

        action_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        action_bar.pack(fill="x")

        ctk.CTkButton(
            action_bar,
            text="Edit Selected",
            font=styles.get_font("body"),
            fg_color=styles.SECONDARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            command=self._open_edit_patron_dialog,
        ).pack(side="left", padx=(0, styles.PADDING["sm"]))

        ctk.CTkButton(
            action_bar,
            text="Delete Selected",
            font=styles.get_font("body"),
            fg_color=styles.DANGER_COLOR,
            hover_color=styles.DANGER_HOVER_COLOR,
            command=self._delete_selected_patron,
        ).pack(side="left")

        self._refresh_patrons_table()

    def _refresh_patrons_table(self):
        for item in self.patrons_tree.get_children():
            self.patrons_tree.delete(item)

        for row in database.get_all_patrons():
            active_transactions = database.get_transactions_for_user(row["id"])
            active_loans = sum(1 for t in active_transactions if t["status"] == "borrowed")
            self.patrons_tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row["id"],
                    row["username"],
                    row["full_name"],
                    row["email"] or "",
                    row["student_id"] or "",
                    row["contact"] or "",
                    active_loans,
                ),
            )

    def _get_selected_patron_id(self):
        selection = self.patrons_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a patron from the table first.")
            return None
        return int(selection[0])

    def _open_add_patron_dialog(self):
        PatronFormDialog(self, on_saved=self._refresh_patrons_table)

    def _open_edit_patron_dialog(self):
        patron_id = self._get_selected_patron_id()
        if patron_id is None:
            return
        patron_row = database.get_user_by_id(patron_id)
        PatronFormDialog(self, on_saved=self._refresh_patrons_table, existing_patron=patron_row)

    def _delete_selected_patron(self):
        patron_id = self._get_selected_patron_id()
        if patron_id is None:
            return

        if database.patron_has_active_borrowings(patron_id):
            messagebox.showerror(
                "Cannot Delete",
                "This patron cannot be deleted because they currently have active borrowings.",
            )
            return

        patron_row = database.get_user_by_id(patron_id)
        confirmed = messagebox.askyesno(
            "Confirm Deletion", f"Delete patron '{patron_row['full_name']}'?"
        )
        if confirmed:
            database.delete_patron(patron_id)
            self._refresh_patrons_table()

    # ------------------------------------------------------------------
    # Circulation section (checkout / return)
    # ------------------------------------------------------------------
    def _build_circulation_section(self):
        self._section_title("Circulation - Checkout and Return")

        form = ctk.CTkFrame(self.content, fg_color=styles.SURFACE_COLOR, corner_radius=styles.CORNER_RADIUS["md"])
        form.pack(fill="x", pady=(0, styles.PADDING["md"]))

        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(fill="x", padx=styles.PADDING["md"], pady=styles.PADDING["md"])

        ctk.CTkLabel(
            inner, text="Checkout a Book", font=styles.get_font("subheading", "bold"), text_color=styles.TEXT_COLOR
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, styles.PADDING["sm"]))

        ctk.CTkLabel(inner, text="Patron", font=styles.get_font("body"), text_color=styles.TEXT_MUTED_COLOR).grid(
            row=1, column=0, sticky="w"
        )
        patrons = database.get_all_patrons()
        self._patron_lookup = {
            f"{p['full_name']} ({p['student_id'] or p['username']})": p["id"] for p in patrons
        }
        self.checkout_patron_combo = ctk.CTkComboBox(
            inner, values=list(self._patron_lookup.keys()) or ["No patrons available"],
            font=styles.get_font("body"), width=280, state="readonly",
        )
        self.checkout_patron_combo.grid(row=2, column=0, padx=(0, styles.PADDING["md"]), pady=(0, styles.PADDING["sm"]), sticky="w")

        ctk.CTkLabel(inner, text="Book", font=styles.get_font("body"), text_color=styles.TEXT_MUTED_COLOR).grid(
            row=1, column=1, sticky="w"
        )
        available_books = database.get_available_books_for_checkout()
        self._book_lookup = {
            f"{b['title']} - {b['isbn']} ({b['available_copies']} available)": b["id"] for b in available_books
        }
        self.checkout_book_combo = ctk.CTkComboBox(
            inner, values=list(self._book_lookup.keys()) or ["No books available"],
            font=styles.get_font("body"), width=320, state="readonly",
        )
        self.checkout_book_combo.grid(row=2, column=1, padx=(0, styles.PADDING["md"]), pady=(0, styles.PADDING["sm"]), sticky="w")

        ctk.CTkButton(
            inner,
            text="Checkout",
            font=styles.get_font("body", "bold"),
            fg_color=styles.PRIMARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            command=self._perform_checkout,
        ).grid(row=2, column=2, sticky="w")

        ctk.CTkLabel(
            inner,
            text=f"Due date will automatically be set to {utils.LOAN_PERIOD_DAYS} days from today.",
            font=styles.get_font("small"),
            text_color=styles.TEXT_MUTED_COLOR,
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(styles.PADDING["xs"], 0))

        ctk.CTkLabel(
            self.content,
            text="Currently Borrowed Books",
            font=styles.get_font("subheading", "bold"),
            text_color=styles.TEXT_COLOR,
        ).pack(anchor="w", pady=(styles.PADDING["sm"], styles.PADDING["xs"]))

        columns = ("id", "patron", "student_id", "book", "checkout", "due", "current_fine", "status")
        headings = ("Txn ID", "Patron", "Student ID", "Book", "Checkout Date", "Due Date", "Current Fine", "Status")
        widths = (55, 150, 90, 200, 100, 100, 95, 90)

        table_frame = ctk.CTkFrame(self.content, fg_color=styles.SURFACE_COLOR, corner_radius=styles.CORNER_RADIUS["md"])
        table_frame.pack(fill="both", expand=True, pady=(0, styles.PADDING["sm"]))

        self.active_tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Elib.Treeview")
        for col, heading, width in zip(columns, headings, widths):
            self.active_tree.heading(col, text=heading)
            self.active_tree.column(col, width=width, anchor="w")
        self.active_tree.column("id", anchor="center")
        self.active_tree.column("current_fine", anchor="center")
        self.active_tree.column("status", anchor="center")
        self.active_tree.pack(fill="both", expand=True, padx=styles.PADDING["sm"], pady=styles.PADDING["sm"])
        self.active_tree.tag_configure("overdue", foreground=styles.DANGER_COLOR)

        ctk.CTkButton(
            self.content,
            text="Return Selected Book",
            font=styles.get_font("body", "bold"),
            fg_color=styles.SECONDARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            command=self._perform_return,
        ).pack(anchor="w")

        self._refresh_active_transactions_table()

    def _refresh_active_transactions_table(self):
        for item in self.active_tree.get_children():
            self.active_tree.delete(item)

        for row in database.get_active_transactions():
            current_fine = utils.calculate_fine(row["due_date"])
            overdue = utils.is_overdue(row["due_date"])
            status = "Overdue" if overdue else "On Time"
            tags = ("overdue",) if overdue else ()
            self.active_tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row["id"],
                    row["patron_name"],
                    row["student_id"] or "",
                    row["book_title"],
                    row["checkout_date"],
                    row["due_date"],
                    utils.format_currency(current_fine),
                    status,
                ),
                tags=tags,
            )

    def _perform_checkout(self):
        patron_label = self.checkout_patron_combo.get()
        book_label = self.checkout_book_combo.get()

        patron_id = self._patron_lookup.get(patron_label)
        book_id = self._book_lookup.get(book_label)

        if patron_id is None or book_id is None:
            messagebox.showwarning("Incomplete Selection", "Please select both a patron and a book.")
            return

        checkout_date = utils.today_str()
        due_date = utils.calculate_due_date(checkout_date)

        try:
            database.checkout_book(patron_id, book_id, checkout_date, due_date)
        except ValueError as exc:
            messagebox.showerror("Checkout Failed", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Database Error", f"Could not complete checkout.\n\n{exc}")
            return

        messagebox.showinfo("Checkout Successful", f"Book checked out. Due date: {due_date}.")
        self.show_section("Circulation")

    def _perform_return(self):
        selection = self.active_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a borrowed book to return.")
            return

        transaction_id = int(selection[0])
        row = next((t for t in database.get_active_transactions() if t["id"] == transaction_id), None)
        if row is None:
            messagebox.showerror("Error", "Selected transaction could not be found.")
            return

        return_date = utils.today_str()
        fine = utils.calculate_fine(row["due_date"], return_date)

        confirmation_message = f"Return '{row['book_title']}' for {row['patron_name']}?"
        if fine > 0:
            confirmation_message += f"\n\nOverdue fine due: {utils.format_currency(fine)}"

        confirmed = messagebox.askyesno("Confirm Return", confirmation_message)
        if not confirmed:
            return

        try:
            database.return_book(transaction_id, return_date, fine)
        except ValueError as exc:
            messagebox.showerror("Return Failed", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Database Error", f"Could not complete return.\n\n{exc}")
            return

        messagebox.showinfo("Return Successful", "The book has been returned.")
        self.show_section("Circulation")

    # ------------------------------------------------------------------
    # Overdue alerts section
    # ------------------------------------------------------------------
    def _build_overdue_section(self):
        self._section_title("Overdue Alerts")

        overdue_rows = database.get_overdue_transactions()

        ctk.CTkLabel(
            self.content,
            text=f"{len(overdue_rows)} overdue item(s) require attention.",
            font=styles.get_font("body"),
            text_color=styles.DANGER_COLOR if overdue_rows else styles.TEXT_MUTED_COLOR,
        ).pack(anchor="w", pady=(0, styles.PADDING["sm"]))

        columns = ("id", "patron", "student_id", "contact", "book", "isbn", "due", "days_overdue", "fine")
        headings = ("Txn ID", "Patron", "Student ID", "Contact", "Book", "ISBN", "Due Date", "Days Overdue", "Fine Due")
        widths = (55, 150, 90, 100, 190, 110, 100, 100, 90)

        table_frame = ctk.CTkFrame(self.content, fg_color=styles.SURFACE_COLOR, corner_radius=styles.CORNER_RADIUS["md"])
        table_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Elib.Treeview")
        for col, heading, width in zip(columns, headings, widths):
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="w")
        tree.column("id", anchor="center")
        tree.column("days_overdue", anchor="center")
        tree.column("fine", anchor="center")
        tree.pack(fill="both", expand=True, padx=styles.PADDING["sm"], pady=styles.PADDING["sm"])
        tree.tag_configure("overdue", foreground=styles.DANGER_COLOR)

        for row in overdue_rows:
            days_overdue = (utils.today() - utils.parse_date(row["due_date"])).days
            fine = utils.calculate_fine(row["due_date"])
            tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["patron_name"],
                    row["student_id"] or "",
                    row["patron_contact"] or "",
                    row["book_title"],
                    row["book_isbn"],
                    row["due_date"],
                    days_overdue,
                    utils.format_currency(fine),
                ),
                tags=("overdue",),
            )


# ===========================================================================
# Dialogs
# ===========================================================================

class BookFormDialog(ctk.CTkToplevel):
    """A modal dialog used to add or edit a book."""

    def __init__(self, parent, on_saved, existing_book=None):
        super().__init__(parent)
        self.parent = parent
        self.on_saved = on_saved
        self.existing_book = existing_book

        self.title("Edit Book" if existing_book else "Add Book")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=styles.BG_COLOR)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self._build_form()

    def _labeled_entry(self, parent, label_text, initial_value=""):
        ctk.CTkLabel(
            parent, text=label_text, font=styles.get_font("body"), text_color=styles.TEXT_MUTED_COLOR
        ).pack(anchor="w", padx=styles.PADDING["md"], pady=(styles.PADDING["sm"], 0))
        entry = ctk.CTkEntry(parent, font=styles.get_font("body"), height=styles.ENTRY_HEIGHT)
        entry.pack(fill="x", padx=styles.PADDING["md"])
        if initial_value:
            entry.insert(0, str(initial_value))
        return entry

    def _build_form(self):
        book = self.existing_book

        self.title_entry = self._labeled_entry(self, "Title", book["title"] if book else "")
        self.author_entry = self._labeled_entry(self, "Author", book["author"] if book else "")
        self.isbn_entry = self._labeled_entry(self, "ISBN", book["isbn"] if book else "")
        self.publisher_entry = self._labeled_entry(self, "Publisher", book["publisher"] if book else "")
        self.year_entry = self._labeled_entry(self, "Year", book["year"] if book else "")
        self.category_entry = self._labeled_entry(self, "Category", book["category"] if book else "")
        self.copies_entry = self._labeled_entry(self, "Total Copies", book["total_copies"] if book else "")

        ctk.CTkButton(
            self,
            text="Save",
            font=styles.get_font("body", "bold"),
            fg_color=styles.PRIMARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            height=styles.BUTTON_HEIGHT,
            command=self._save,
        ).pack(fill="x", padx=styles.PADDING["md"], pady=(styles.PADDING["lg"], styles.PADDING["sm"]))

        ctk.CTkButton(
            self,
            text="Cancel",
            font=styles.get_font("body"),
            fg_color=styles.SURFACE_COLOR,
            text_color=styles.TEXT_COLOR,
            border_width=styles.BORDER_WIDTH,
            border_color=styles.BORDER_COLOR,
            hover_color=styles.BORDER_COLOR,
            height=styles.BUTTON_HEIGHT,
            command=self.destroy,
        ).pack(fill="x", padx=styles.PADDING["md"])

    def _save(self):
        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        isbn = self.isbn_entry.get().strip()
        publisher = self.publisher_entry.get().strip()
        year_text = self.year_entry.get().strip()
        category = self.category_entry.get().strip()
        copies_text = self.copies_entry.get().strip()

        if not title or not author or not isbn or not category or not copies_text:
            messagebox.showwarning(
                "Missing Information",
                "Title, Author, ISBN, Category and Total Copies are required.",
                parent=self,
            )
            return

        try:
            total_copies = int(copies_text)
            if total_copies < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Value", "Total Copies must be a non-negative whole number.", parent=self)
            return

        year_value = None
        if year_text:
            try:
                year_value = int(year_text)
            except ValueError:
                messagebox.showwarning("Invalid Value", "Year must be a whole number.", parent=self)
                return

        existing_id = self.existing_book["id"] if self.existing_book else None
        if database.isbn_exists(isbn, exclude_id=existing_id):
            messagebox.showerror("Duplicate ISBN", "A book with this ISBN already exists.", parent=self)
            return

        try:
            if self.existing_book:
                database.update_book(
                    existing_id, title, author, isbn, publisher, year_value, category, total_copies
                )
            else:
                database.add_book(title, author, isbn, publisher, year_value, category, total_copies)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Database Error", f"Could not save the book.\n\n{exc}", parent=self)
            return

        self.on_saved()
        self.destroy()


class PatronFormDialog(ctk.CTkToplevel):
    """A modal dialog used to register or edit a patron."""

    def __init__(self, parent, on_saved, existing_patron=None):
        super().__init__(parent)
        self.parent = parent
        self.on_saved = on_saved
        self.existing_patron = existing_patron

        self.title("Edit Patron" if existing_patron else "Register New Patron")
        self.geometry("420x600")
        self.resizable(False, False)
        self.configure(fg_color=styles.BG_COLOR)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self._build_form()

    def _labeled_entry(self, parent, label_text, initial_value="", show=None):
        ctk.CTkLabel(
            parent, text=label_text, font=styles.get_font("body"), text_color=styles.TEXT_MUTED_COLOR
        ).pack(anchor="w", padx=styles.PADDING["md"], pady=(styles.PADDING["sm"], 0))
        entry = ctk.CTkEntry(parent, font=styles.get_font("body"), height=styles.ENTRY_HEIGHT, show=show)
        entry.pack(fill="x", padx=styles.PADDING["md"])
        if initial_value:
            entry.insert(0, str(initial_value))
        return entry

    def _build_form(self):
        patron = self.existing_patron

        self.username_entry = self._labeled_entry(self, "Username", patron["username"] if patron else "")
        if patron:
            self.username_entry.configure(state="disabled")

        password_label = "New Password (leave blank to keep unchanged)" if patron else "Password"
        self.password_entry = self._labeled_entry(self, password_label, show="*")

        self.full_name_entry = self._labeled_entry(self, "Full Name", patron["full_name"] if patron else "")
        self.email_entry = self._labeled_entry(self, "Email", patron["email"] if patron else "")
        self.student_id_entry = self._labeled_entry(self, "Student ID", patron["student_id"] if patron else "")
        self.contact_entry = self._labeled_entry(self, "Contact Number", patron["contact"] if patron else "")

        ctk.CTkButton(
            self,
            text="Save",
            font=styles.get_font("body", "bold"),
            fg_color=styles.PRIMARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            height=styles.BUTTON_HEIGHT,
            command=self._save,
        ).pack(fill="x", padx=styles.PADDING["md"], pady=(styles.PADDING["lg"], styles.PADDING["sm"]))

        ctk.CTkButton(
            self,
            text="Cancel",
            font=styles.get_font("body"),
            fg_color=styles.SURFACE_COLOR,
            text_color=styles.TEXT_COLOR,
            border_width=styles.BORDER_WIDTH,
            border_color=styles.BORDER_COLOR,
            hover_color=styles.BORDER_COLOR,
            height=styles.BUTTON_HEIGHT,
            command=self.destroy,
        ).pack(fill="x", padx=styles.PADDING["md"])

    def _save(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        full_name = self.full_name_entry.get().strip()
        email = self.email_entry.get().strip()
        student_id = self.student_id_entry.get().strip()
        contact = self.contact_entry.get().strip()

        if not full_name or not student_id:
            messagebox.showwarning("Missing Information", "Full Name and Student ID are required.", parent=self)
            return

        if not self.existing_patron:
            if not username or not password:
                messagebox.showwarning(
                    "Missing Information", "Username and Password are required for new patrons.", parent=self
                )
                return
            if database.username_exists(username):
                messagebox.showerror("Duplicate Username", "This username is already taken.", parent=self)
                return

        try:
            if self.existing_patron:
                password_hash = utils.hash_password(password) if password else None
                database.update_patron(
                    self.existing_patron["id"], full_name, email, student_id, contact, password_hash
                )
            else:
                database.add_patron(
                    username, utils.hash_password(password), full_name, email, student_id, contact
                )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Database Error", f"Could not save the patron.\n\n{exc}", parent=self)
            return

        self.on_saved()
        self.destroy()
