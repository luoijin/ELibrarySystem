"""
gui/patron_dashboard.py
========================

The patron (student / faculty) dashboard. Provides three read-only
functional areas as required by the specification:

* Browsing the book catalogue.
* Viewing currently borrowed books and their fines.
* Viewing account details.

Checkout and return are librarian-only operations (performed from the
``AdminDashboard``); the patron dashboard is intentionally read-only
with respect to circulation, per the specification.
"""

from tkinter import ttk

import customtkinter as ctk

import database
import styles
import utils


class PatronDashboard(ctk.CTkFrame):
    """Main frame for the patron role, containing sidebar navigation."""

    NAV_ITEMS = ("Browse Books", "My Borrowed Books", "My Fines", "My Account")

    def __init__(self, master, current_user, on_logout):
        """Initialise the patron dashboard.

        Args:
            master: The parent widget.
            current_user: The authenticated patron ``sqlite3.Row``.
            on_logout: Callback invoked when the patron logs out.
        """
        super().__init__(master, fg_color=styles.BG_COLOR)
        self.current_user = current_user
        self.on_logout = on_logout

        styles.configure_ttk_style()
        self._build_layout()
        self.show_section("Browse Books")

    # ------------------------------------------------------------------
    # Layout scaffolding
    # ------------------------------------------------------------------
    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

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
            text=f"Welcome, {self.current_user['full_name']}",
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

        if section_name == "Browse Books":
            self._build_browse_section()
        elif section_name == "My Borrowed Books":
            self._build_borrowed_section()
        elif section_name == "My Fines":
            self._build_fines_section()
        elif section_name == "My Account":
            self._build_account_section()

    def _section_title(self, text):
        ctk.CTkLabel(
            self.content,
            text=text,
            font=styles.get_font("heading", "bold"),
            text_color=styles.TEXT_COLOR,
        ).pack(anchor="w", pady=(0, styles.PADDING["md"]))

    def _make_table(self, columns, headings, widths):
        table_frame = ctk.CTkFrame(self.content, fg_color=styles.SURFACE_COLOR, corner_radius=styles.CORNER_RADIUS["md"])
        table_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Elib.Treeview")
        for col, heading, width in zip(columns, headings, widths):
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True, padx=styles.PADDING["sm"], pady=styles.PADDING["sm"])
        tree.tag_configure("overdue", foreground=styles.DANGER_COLOR)
        return tree

    # ------------------------------------------------------------------
    # Browse Books section
    # ------------------------------------------------------------------
    def _build_browse_section(self):
        self._section_title("Browse Books")

        toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, styles.PADDING["sm"]))

        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Search by title, author, ISBN or category",
            font=styles.get_font("body"),
            height=styles.ENTRY_HEIGHT,
            width=360,
        )
        self.search_entry.pack(side="left", padx=(0, styles.PADDING["sm"]))
        self.search_entry.bind("<Return>", lambda _e: self._refresh_browse_table())

        ctk.CTkButton(
            toolbar,
            text="Search",
            font=styles.get_font("body"),
            fg_color=styles.SECONDARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            height=styles.ENTRY_HEIGHT,
            command=self._refresh_browse_table,
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
            command=self._clear_browse_search,
        ).pack(side="left")

        columns = ("title", "author", "isbn", "publisher", "year", "category", "available", "status")
        headings = ("Title", "Author", "ISBN", "Publisher", "Year", "Category", "Available", "Status")
        widths = (220, 150, 110, 130, 60, 120, 75, 95)
        self.browse_tree = self._make_table(columns, headings, widths)
        self.browse_tree.column("year", anchor="center")
        self.browse_tree.column("available", anchor="center")
        self.browse_tree.column("status", anchor="center")

        self._refresh_browse_table()

    def _clear_browse_search(self):
        self.search_entry.delete(0, "end")
        self._refresh_browse_table()

    def _refresh_browse_table(self):
        search_term = self.search_entry.get().strip()
        rows = database.search_books(search_term) if search_term else database.get_all_books()

        for item in self.browse_tree.get_children():
            self.browse_tree.delete(item)

        for row in rows:
            status = "Available" if row["available_copies"] > 0 else "Unavailable"
            tags = () if row["available_copies"] > 0 else ("overdue",)
            self.browse_tree.insert(
                "",
                "end",
                values=(
                    row["title"],
                    row["author"],
                    row["isbn"],
                    row["publisher"] or "",
                    row["year"] or "",
                    row["category"],
                    row["available_copies"],
                    status,
                ),
                tags=tags,
            )

    # ------------------------------------------------------------------
    # My Borrowed Books section
    # ------------------------------------------------------------------
    def _build_borrowed_section(self):
        self._section_title("My Borrowed Books")

        transactions = database.get_transactions_for_user(self.current_user["id"])
        active = [t for t in transactions if t["status"] == "borrowed"]

        ctk.CTkLabel(
            self.content,
            text=f"You currently have {len(active)} book(s) checked out.",
            font=styles.get_font("body"),
            text_color=styles.TEXT_MUTED_COLOR,
        ).pack(anchor="w", pady=(0, styles.PADDING["sm"]))

        columns = ("title", "author", "isbn", "checkout", "due", "current_fine", "status")
        headings = ("Title", "Author", "ISBN", "Checkout Date", "Due Date", "Current Fine", "Status")
        widths = (220, 150, 110, 100, 100, 100, 90)
        tree = self._make_table(columns, headings, widths)
        tree.column("current_fine", anchor="center")
        tree.column("status", anchor="center")

        for row in active:
            current_fine = utils.calculate_fine(row["due_date"])
            overdue = utils.is_overdue(row["due_date"])
            status = "Overdue" if overdue else "On Time"
            tags = ("overdue",) if overdue else ()
            tree.insert(
                "",
                "end",
                values=(
                    row["book_title"],
                    row["book_author"],
                    row["book_isbn"],
                    row["checkout_date"],
                    row["due_date"],
                    utils.format_currency(current_fine),
                    status,
                ),
                tags=tags,
            )

    # ------------------------------------------------------------------
    # My Fines section
    # ------------------------------------------------------------------
    def _build_fines_section(self):
        self._section_title("My Fines")

        transactions = database.get_transactions_for_user(self.current_user["id"])
        active = [t for t in transactions if t["status"] == "borrowed"]
        returned = [t for t in transactions if t["status"] == "returned"]

        outstanding_total = sum(utils.calculate_fine(t["due_date"]) for t in active)
        historical_total = sum(t["fine"] for t in returned)

        summary = ctk.CTkFrame(self.content, fg_color=styles.SURFACE_COLOR, corner_radius=styles.CORNER_RADIUS["md"])
        summary.pack(fill="x", pady=(0, styles.PADDING["md"]))

        summary_inner = ctk.CTkFrame(summary, fg_color="transparent")
        summary_inner.pack(fill="x", padx=styles.PADDING["md"], pady=styles.PADDING["md"])

        ctk.CTkLabel(
            summary_inner,
            text="Outstanding Fines (active loans)",
            font=styles.get_font("body"),
            text_color=styles.TEXT_MUTED_COLOR,
        ).pack(anchor="w")
        ctk.CTkLabel(
            summary_inner,
            text=utils.format_currency(outstanding_total),
            font=styles.get_font("heading", "bold"),
            text_color=styles.DANGER_COLOR if outstanding_total > 0 else styles.SUCCESS_COLOR,
        ).pack(anchor="w")

        ctk.CTkLabel(
            self.content,
            text="Fine History",
            font=styles.get_font("subheading", "bold"),
            text_color=styles.TEXT_COLOR,
        ).pack(anchor="w", pady=(0, styles.PADDING["xs"]))

        columns = ("title", "due", "return", "fine", "status")
        headings = ("Book Title", "Due Date", "Return Date", "Fine", "Status")
        widths = (260, 110, 110, 90, 90)
        tree = self._make_table(columns, headings, widths)
        tree.column("fine", anchor="center")
        tree.column("status", anchor="center")

        for row in transactions:
            if row["status"] == "borrowed":
                fine = utils.calculate_fine(row["due_date"])
                return_date = "-"
                status_label = "Overdue" if utils.is_overdue(row["due_date"]) else "Borrowed"
            else:
                fine = row["fine"]
                return_date = row["return_date"]
                status_label = "Returned"

            tags = ("overdue",) if fine > 0 else ()
            tree.insert(
                "",
                "end",
                values=(
                    row["book_title"],
                    row["due_date"],
                    return_date,
                    utils.format_currency(fine),
                    status_label,
                ),
                tags=tags,
            )

        _ = historical_total  # retained for potential future summary use

    # ------------------------------------------------------------------
    # My Account section
    # ------------------------------------------------------------------
    def _build_account_section(self):
        self._section_title("My Account")

        card = ctk.CTkFrame(self.content, fg_color=styles.SURFACE_COLOR, corner_radius=styles.CORNER_RADIUS["md"])
        card.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=styles.PADDING["lg"], pady=styles.PADDING["lg"])

        fields = (
            ("Full Name", self.current_user["full_name"]),
            ("Username", self.current_user["username"]),
            ("Student ID", self.current_user["student_id"] or "N/A"),
            ("Email", self.current_user["email"] or "N/A"),
            ("Contact Number", self.current_user["contact"] or "N/A"),
            ("Role", "Patron"),
        )

        for label_text, value_text in fields:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=styles.PADDING["xs"])

            ctk.CTkLabel(
                row, text=label_text, font=styles.get_font("body", "bold"),
                text_color=styles.TEXT_COLOR, width=160, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=str(value_text), font=styles.get_font("body"),
                text_color=styles.TEXT_MUTED_COLOR, anchor="w",
            ).pack(side="left")
