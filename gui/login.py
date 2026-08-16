"""
gui/login.py
============

The login screen shown when the application starts. Validates
credentials against the ``users`` table in SQLite and, on success,
hands control back to the main controller via the ``on_login_success``
callback so it can display the correct role-based dashboard.
"""

import customtkinter as ctk
from tkinter import messagebox

import database
import styles


class LoginFrame(ctk.CTkFrame):
    """The login screen frame."""

    def __init__(self, master, on_login_success):
        """Initialise the login screen.

        Args:
            master: The parent widget (the main application window).
            on_login_success: Callback invoked with the authenticated
                ``sqlite3.Row`` user object after a successful login.
        """
        super().__init__(master, fg_color=styles.BG_COLOR)
        self.on_login_success = on_login_success
        self._build_ui()

    def _build_ui(self):
        """Construct and lay out all widgets for the login screen."""
        # Centered card that holds the login form.
        card = ctk.CTkFrame(
            self,
            fg_color=styles.SURFACE_COLOR,
            corner_radius=styles.CORNER_RADIUS["lg"],
            border_width=styles.BORDER_WIDTH,
            border_color=styles.BORDER_COLOR,
            width=420,
            height=460,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # Header banner.
        header = ctk.CTkFrame(
            card,
            fg_color=styles.PRIMARY_COLOR,
            corner_radius=0,
            height=110,
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="ELibrary System",
            font=styles.get_font("heading", "bold"),
            text_color=styles.TEXT_ON_PRIMARY_COLOR,
        ).pack(pady=(styles.PADDING["lg"], 0))

        ctk.CTkLabel(
            header,
            text="University Library Management",
            font=styles.get_font("small"),
            text_color=styles.TEXT_ON_PRIMARY_COLOR,
        ).pack()

        # Form body.
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=styles.PADDING["xl"], pady=styles.PADDING["lg"])

        ctk.CTkLabel(
            body,
            text="Sign In",
            font=styles.get_font("subheading", "bold"),
            text_color=styles.TEXT_COLOR,
        ).pack(anchor="w", pady=(0, styles.PADDING["md"]))

        ctk.CTkLabel(
            body,
            text="Username",
            font=styles.get_font("body"),
            text_color=styles.TEXT_MUTED_COLOR,
        ).pack(anchor="w")

        self.username_entry = ctk.CTkEntry(
            body,
            height=styles.ENTRY_HEIGHT,
            corner_radius=styles.CORNER_RADIUS["sm"],
            font=styles.get_font("body"),
            placeholder_text="Enter your username or student ID",
        )
        self.username_entry.pack(fill="x", pady=(styles.PADDING["xs"], styles.PADDING["md"]))

        ctk.CTkLabel(
            body,
            text="Password",
            font=styles.get_font("body"),
            text_color=styles.TEXT_MUTED_COLOR,
        ).pack(anchor="w")

        self.password_entry = ctk.CTkEntry(
            body,
            height=styles.ENTRY_HEIGHT,
            corner_radius=styles.CORNER_RADIUS["sm"],
            font=styles.get_font("body"),
            placeholder_text="Enter your password",
            show="*",
        )
        self.password_entry.pack(fill="x", pady=(styles.PADDING["xs"], styles.PADDING["lg"]))
        self.password_entry.bind("<Return>", lambda _event: self._attempt_login())

        self.login_button = ctk.CTkButton(
            body,
            text="Log In",
            height=styles.BUTTON_HEIGHT,
            corner_radius=styles.CORNER_RADIUS["sm"],
            font=styles.get_font("body", "bold"),
            fg_color=styles.PRIMARY_COLOR,
            hover_color=styles.BUTTON_HOVER_COLOR,
            text_color=styles.TEXT_ON_PRIMARY_COLOR,
            command=self._attempt_login,
        )
        self.login_button.pack(fill="x", pady=(0, styles.PADDING["md"]))

        hint = ctk.CTkLabel(
            body,
            text="Librarian: librarian / admin123\nPatron: 23065360 / patron123",
            font=styles.get_font("small"),
            text_color=styles.TEXT_MUTED_COLOR,
            justify="center",
        )
        hint.pack(pady=(styles.PADDING["sm"], 0))

    def _attempt_login(self):
        """Validate the entered credentials and trigger the login callback."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Missing Information", "Please enter both username and password.")
            return

        try:
            user_row = database.authenticate_user(username, password)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user via message box
            messagebox.showerror("Database Error", f"Could not verify credentials.\n\n{exc}")
            return

        if user_row is None:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            self.password_entry.delete(0, "end")
            return

        self.password_entry.delete(0, "end")
        self.on_login_success(user_row)
