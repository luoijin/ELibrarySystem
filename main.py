"""
main.py
=======

Application entry point and top-level controller for the ELibrary
System.

Responsibilities:

* Initialise the SQLite database (creating tables and seeding mock
  data on first run).
* Create the main application window using the global style
  configuration from ``styles.py``.
* Switch between the login screen and the appropriate role-based
  dashboard (librarian or patron) based on authentication results.
"""

import customtkinter as ctk

import database
import styles
from gui.login import LoginFrame
from gui.admin_dashboard import AdminDashboard
from gui.patron_dashboard import PatronDashboard


class ELibraryApp(ctk.CTk):
    """Root application window and screen controller."""

    def __init__(self):
        super().__init__()

        self.title(styles.WINDOW_TITLE)
        self.geometry(styles.WINDOW_SIZE)
        self.minsize(*styles.WINDOW_MIN_SIZE)
        self.configure(fg_color=styles.BG_COLOR)

        self.current_user = None
        self.current_frame = None

        self.show_login()

    # ------------------------------------------------------------------
    # Screen management
    # ------------------------------------------------------------------
    def _replace_frame(self, frame: ctk.CTkFrame):
        """Destroy the current frame (if any) and display a new one."""
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame
        self.current_frame.pack(fill="both", expand=True)

    def show_login(self):
        """Display the login screen."""
        self.current_user = None
        login_frame = LoginFrame(self, on_login_success=self._handle_login_success)
        self._replace_frame(login_frame)

    def _handle_login_success(self, user_row):
        """Route to the correct dashboard based on the authenticated user's role."""
        self.current_user = user_row
        if user_row["role"] == "librarian":
            dashboard = AdminDashboard(self, current_user=user_row, on_logout=self.show_login)
        else:
            dashboard = PatronDashboard(self, current_user=user_row, on_logout=self.show_login)
        self._replace_frame(dashboard)


def main():
    """Initialise the database and launch the application."""
    database.initialize_database()
    app = ELibraryApp()
    app.mainloop()


if __name__ == "__main__":
    main()
