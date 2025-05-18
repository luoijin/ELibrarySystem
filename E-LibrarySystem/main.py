import os
import json
import re
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("E-Library System")
        self.geometry("980x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Container frame for page switching
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.current_user = None

        self.frames = {}

        for F in (LoginPage, SignupPage, AdminDashboard, UserDashboard):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginPage)

    def show_frame(self, cont):
        frame = self.frames[cont]

        # Clear login fields when showing login page
        if cont == LoginPage:
            frame.clear_fields()
            self.current_user = None

        if cont in (UserDashboard, AdminDashboard):
            frame.refresh_content()

        frame.tkraise()

    def set_current_user(self, user):
        self.current_user = user

class Database:
    def __init__(self, books_file="books.json", favorites_file="favorites.json"):
        self.books_file = books_file
        self.favorites_file = favorites_file

        self._initialize_files()

    def _initialize_files(self):

        if not os.path.exists(self.books_file):
            with open(self.books_file, 'w') as f:
                json.dump([], f)

        if not os.path.exists(self.favorites_file):
            with open(self.favorites_file, 'w') as f:
                json.dump([], f)

    def get_book_by_isbn(self, isbn):
        try:
            with open(self.books_file, 'r') as f:
                books = json.load(f)
                for book in books:
                    if book.get('isbn') == isbn:
                        return book
            return None
        except Exception as e:
            print(f"Error getting book by ISBN: {e}")
            return None

    def is_book_in_favorites(self, isbn):
        try:
            with open(self.favorites_file, 'r') as f:
                favorites = json.load(f)
                return isbn in favorites
        except Exception as e:
            print(f"Error checking if book is in favorites: {e}")
            return False

    def add_book_to_favorites(self, isbn):
        try:
            with open(self.favorites_file, 'r') as f:
                favorites = json.load(f)

            if isbn not in favorites:
                favorites.append(isbn)

            with open(self.favorites_file, 'w') as f:
                json.dump(favorites, f)

            return True
        except Exception as e:
            print(f"Error adding book to favorites: {e}")
            return False

    def remove_book_from_favorites(self, isbn):
        try:
            with open(self.favorites_file, 'r') as f:
                favorites = json.load(f)

            if isbn in favorites:
                favorites.remove(isbn)

            with open(self.favorites_file, 'w') as f:
                json.dump(favorites, f)

            return True
        except Exception as e:
            print(f"Error removing book from favorites: {e}")
            return False

    def get_favorite_books(self):
        try:
            with open(self.favorites_file, 'r') as f:
                favorite_isbns = json.load(f)

            with open(self.books_file, 'r') as f:
                all_books = json.load(f)

            favorite_books = []
            for book in all_books:
                if book.get('isbn') in favorite_isbns:
                    favorite_books.append(book)

            return favorite_books
        except Exception as e:
            print(f"Error getting favorite books: {e}")
            return []

class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # frame responsive
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # center frame for login
        login_frame = ctk.CTkFrame(self, corner_radius=15)
        login_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        login_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(login_frame, text="E-LIBRARY SYSTEM", font=("Century Gothic", 24, "bold")).grid(
            row=0, column=0, pady=(80, 0))
        ctk.CTkLabel(login_frame, text="Login", font=("Century Gothic", 20, "bold")).grid(
            row=1, column=0, pady=(50, 10))

        self.username_entry = ctk.CTkEntry(login_frame, width=300, placeholder_text="Username")
        self.username_entry.grid(row=2, column=0, pady=10)
        self.username_entry.bind("<Return>", lambda event: self.login())

        self.password_entry = ctk.CTkEntry(login_frame, width=300, placeholder_text="Password", show="*")
        self.password_entry.grid(row=3, column=0, pady=10)
        self.password_entry.bind("<Return>", lambda event: self.login())

        ctk.CTkButton(login_frame, text="Login", width=300, command=self.login).grid(row=4, column=0, pady=10)

        signup_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        signup_frame.grid(row=5, column=0, pady=10)
        ctk.CTkLabel(signup_frame, text="Don't have an account? ", font=("Century Gothic", 12)).grid(row=0, column=0)

        signup_link = ctk.CTkLabel(signup_frame, text="Sign up", font=("Century Gothic", 12, "bold"),
                                   text_color="#1F6AA5", cursor="hand2")
        signup_link.bind("<Button-1>", lambda e: controller.show_frame(SignupPage))
        signup_link.grid(row=0, column=1)

    def clear_fields(self):
        if hasattr(self, 'username_entry'):
            self.username_entry.delete(0, tk.END)
        if hasattr(self, 'password_entry'):
            self.password_entry.delete(0, tk.END)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "All fields must be filled!")
            return

        if (username == "admin" and password == "admin123") or (username == "1" and password == "1"):
            self.controller.set_current_user({"username": "admin", "role": "Admin"})
            self.controller.show_frame(AdminDashboard)
            return

        # check user credentials from JSON file
        if os.path.exists("users.json"):
            try:
                with open("users.json", "r") as file:
                    users = json.load(file)
                    for user in users:
                        if user.get("username") == username and user.get("password") == password:
                            self.controller.set_current_user(user)
                            self.controller.show_frame(UserDashboard)
                            return
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Database error!")
                return

        messagebox.showerror("Error", "Invalid username or password!")

class SignupPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # frame responsive
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        signup_frame = ctk.CTkFrame(self, corner_radius=15)
        signup_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        signup_frame.columnconfigure(0, weight=1)
        signup_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(signup_frame, text="E-LIBRARY SYSTEM", font=("Century Gothic", 24, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(40, 10))
        ctk.CTkLabel(signup_frame, text="Sign Up", font=("Century Gothic", 20, "bold")).grid(
            row=1, column=0, columnspan=2, pady=10)

        ctk.CTkLabel(signup_frame, text="Role:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        role_frame = ctk.CTkFrame(signup_frame, fg_color="transparent")
        role_frame.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        self.role_var = tk.StringVar(value="Student")
        self.role_combo = ctk.CTkComboBox(role_frame, values=["Student", "Faculty"],
                                          variable=self.role_var, width=100, command=self.on_role_change)
        self.role_combo.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(role_frame, text="Age:").pack(side="left", padx=(10, 5))
        self.age_entry = ctk.CTkEntry(role_frame, width=50)
        self.age_entry.pack(side="left")

        # form fields with labels on left, entries on right
        fields = [
            ("Student ID:", "student_id_entry"),
            ("Full Name:", "name_entry"),
            ("Username:", "username_entry"),
            ("Password:", "password_entry", "*"),
            ("Email:", "email_entry"),
            ("Contact Number:", "contact_entry"),
            ("Address:", "address_entry")
        ]

        for i, field in enumerate(fields):
            row = i + 3  # Start from row 3
            ctk.CTkLabel(signup_frame, text=field[0]).grid(row=row, column=0, padx=10, pady=5, sticky="e")

            if len(field) == 3:  # Password field with show="*"
                entry = ctk.CTkEntry(signup_frame, width=200, show=field[2])
            else:
                entry = ctk.CTkEntry(signup_frame, width=200)

            setattr(self, field[1], entry)
            entry.grid(row=row, column=1, padx=10, pady=5, sticky="w")

        self.contact_entry.configure(validate="key", validatecommand=(self.register(self.validate_contact), '%P'))
        self.student_id_entry.configure(validate="key", validatecommand=(self.register(self.validate_student_id), '%P'))

        # Signup button
        ctk.CTkButton(signup_frame, text="Sign Up", command=self.signup).grid(
            row=10, column=0, columnspan=2, pady=10)

        # Login link
        login_frame = ctk.CTkFrame(signup_frame, fg_color="transparent")
        login_frame.grid(row=11, column=0, columnspan=2, pady=10)
        ctk.CTkLabel(login_frame, text="Already have an account? ", font=("Century Gothic", 12)).grid(row=0, column=0)

        login_link = ctk.CTkLabel(login_frame, text="Login", font=("Century Gothic", 12, "bold"),
                                  text_color="#1F6AA5", cursor="hand2")
        login_link.bind("<Button-1>", lambda e: controller.show_frame(LoginPage))
        login_link.grid(row=0, column=1)

        self.on_role_change("Student")

    def on_role_change(self, role):
        if role == "Faculty":
            self.student_id_entry.delete(0, tk.END)
            self.student_id_entry.insert(0, "Faculty")
        elif self.student_id_entry.get().lower() == "faculty":
            self.student_id_entry.delete(0, tk.END)

    def validate_student_id(self, new_value):
        role = self.role_var.get()

        if role == "Faculty":
            return new_value.lower() in ["", "faculty", "f"] or new_value.lower().startswith("faculty")
        else:
            return new_value == "" or (new_value.isdigit() and len(new_value) <= 8)

    def validate_contact(self, new_value):
        return new_value == "" or (new_value.isdigit() and len(new_value) <= 11)

    def signup(self):
        data = {
            "role": self.role_var.get(),
            "student_id": self.student_id_entry.get(),
            "name": self.name_entry.get(),
            "username": self.username_entry.get(),
            "password": self.password_entry.get(),
            "email": self.email_entry.get(),
            "contact": self.contact_entry.get(),
            "address": self.address_entry.get(),
            "age": self.age_entry.get()
        }

        # validation
        if not all(data.values()):
            messagebox.showerror("Error", "All fields must be filled!")
            return

        # student ID validation
        if data["role"] == "Student" and (len(data["student_id"]) != 8 or not data["student_id"].isdigit()):
            messagebox.showerror("Error", "Student ID must be 8 digits!")
            return
        elif data["role"] == "Faculty" and data["student_id"].lower() != "faculty":
            messagebox.showerror("Error", "Faculty members should use 'Faculty' as their ID!")
            return

        # email validation
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', data["email"]):
            messagebox.showerror("Error", "Invalid email format!")
            return

        # contact number validation
        if len(data["contact"]) != 11 or not data["contact"].isdigit():
            messagebox.showerror("Error", "Contact number must be 11 digits!")
            return

        # username validation
        if data["username"] in ["admin", "1"]:
            messagebox.showerror("Error", "Username taken!")
            return

        # check for existing username
        users = []
        if os.path.exists("users.json"):
            try:
                with open("users.json", "r") as file:
                    users = json.load(file)
                    if any(user.get("username") == data["username"] for user in users):
                        messagebox.showerror("Error", "Username taken!")
                        return
            except json.JSONDecodeError:
                pass

        # add new user and save
        users.append(data)
        with open("users.json", "w") as file:
            json.dump(users, file, indent=4)

        messagebox.showinfo("Success", "Account created successfully!")
        self.controller.show_frame(LoginPage)

class AdminDashboard(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_book_isbn = None

        # frame responsive
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")

        ctk.CTkLabel(sidebar, text="Administrator", font=("Century Gothic", 20, "bold")).pack(padx=20, pady=20)

        nav_buttons = [
            ("Library", self.show_library),
            ("Add Book", self.show_add_book),
            ("Edit Book", self.show_edit_book),
            ("Borrowed Books", self.show_borrowed),
            ("Users", self.show_users)
        ]

        for text, command in nav_buttons:
            ctk.CTkButton(sidebar, text=text, command=command).pack(padx=20, pady=10, fill="x")

        ctk.CTkButton(sidebar, text="Logout", fg_color="#D35B58", hover_color="#C77C78",
                      command=lambda: controller.show_frame(LoginPage)).pack(
            padx=20, pady=10, side="bottom", fill="x")

        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(1, weight=1)

        self.content_frame = ctk.CTkScrollableFrame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky="nsew")

        self.refresh_content()

    def refresh_content(self):
        self.show_library()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def search_books(self, search_entry=None):
        query = search_entry.get().lower() if search_entry else ""

        books = self._load_books()

        if query:
            results = [book for book in books if
                       query in book.get("title", "").lower() or
                       query in book.get("author", "").lower() or
                       query in book.get("isbn", "").lower() or
                       query in book.get("genre", "").lower()]
        else:
            results = books

        for widget in self.content_frame.winfo_children():
            if widget != self.content_frame.winfo_children()[0]:
                widget.destroy()

        if query:
            results_label = ctk.CTkLabel(self.content_frame,
                                         text=f"Found {len(results)} matching books for '{query}'")
            results_label.pack(pady=(10, 5))

            back_btn = ctk.CTkButton(self.content_frame, text="← Show All Books",
                                     fg_color="transparent", text_color=("#1F6AA5"),
                                     hover_color=("#E5E5E5"), width=150,
                                     command=lambda: self.show_library())
            back_btn.pack(pady=(0, 10))

        if not results:
            ctk.CTkLabel(self.content_frame, text="No matching books found").pack(pady=20)
            return

        self._display_books(results)

    def show_library(self):
        self._clear_content()

        library_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        library_frame.pack(fill="x", padx=10, pady=10)

        header_frame = ctk.CTkFrame(library_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 10))

        title_label = ctk.CTkLabel(header_frame, text="Library", font=("Century Gothic", 24, "bold"))
        title_label.grid(row=0, column=0, sticky="w")

        # Search bar
        search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_frame.grid(row=0, column=1, sticky="e")

        search_entry = ctk.CTkEntry(search_frame, width=200, placeholder_text="Search books...")
        search_entry.pack(side="left", padx=(285, 10), pady=(10, 0))

        def on_search(*args):
            self.search_books(search_entry)

        search_entry.bind("<KeyRelease>", on_search)

        ctk.CTkButton(search_frame, text="Search", width=80,
                      command=lambda: self.search_books(search_entry)).pack(anchor="e", padx=(0, 10), pady=(10, 0))

        books = self._load_books()
        if not books:
            ctk.CTkLabel(self.content_frame, text="No books available in the library").pack(pady=20)
            return

        sorted_books = sorted(books, key=lambda x: x.get('title', '').lower())

        self._display_books(sorted_books)

    def _display_books(self, books):
        books_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        books_frame.pack(fill="both", expand=True)

        columns = 3
        for i in range(columns):
            books_frame.columnconfigure(i, weight=1)

        for i, book in enumerate(books):
            row, col = divmod(i, columns)

            card = ctk.CTkFrame(books_frame, corner_radius=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            ctk.CTkLabel(card, text=book.get("title", ""),
                         font=("Century Gothic", 16, "bold")).pack(pady=(10, 5), padx=10)
            ctk.CTkLabel(card, text=f"Author: {book.get('author', 'Unknown')}").pack(pady=2, padx=10, anchor="w")
            ctk.CTkLabel(card, text=f"ISBN: {book.get('isbn', 'N/A')}").pack(pady=2, padx=10, anchor="w")
            ctk.CTkLabel(card, text=f"Genre: {book.get('genre', 'N/A')}").pack(pady=2, padx=10, anchor="w")

            availability = book.get("available", True)
            status_text = "Status: Available" if availability else "Status: Borrowed"
            status_color = "#28a745" if availability else "#dc3545"

            ctk.CTkLabel(card, text=status_text, text_color=status_color).pack(pady=2, padx=10, anchor="w")

            if availability:
                ctk.CTkButton(card, text="Borrow", width=120,
                              command=lambda isbn=book.get("isbn"): self.borrow_book(isbn)).pack(pady=10, padx=10)
            else:
                ctk.CTkFrame(card, height=38, fg_color="transparent").pack(pady=10, padx=10)

    def show_add_book(self):
        self._clear_content()

        add_book_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        add_book_frame.pack(fill="x", padx=10, pady=10)

        header_frame = ctk.CTkFrame(add_book_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 10))

        ctk.CTkLabel(header_frame, text="Add Book",
                     font=("Century Gothic", 24, "bold")).pack(anchor="w")

        form_frame = ctk.CTkFrame(self.content_frame)
        form_frame.pack(pady=20, padx=20, fill="x")

        fields = [
            ("Title:", "title_entry"),
            ("Author:", "author_entry"),
            ("ISBN:", "isbn_entry"),
            ("Genre:", "genre_entry")
        ]

        self.book_entries = {}
        for i, (label_text, entry_name) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=label_text).grid(row=i, column=0, padx=10, pady=10, sticky="e")
            entry = ctk.CTkEntry(form_frame, width=300)
            entry.grid(row=i, column=1, padx=10, pady=10, sticky="w")
            self.book_entries[entry_name] = entry

        ctk.CTkButton(form_frame, text="Add Book", command=self.add_book).grid(
            row=len(fields) + 1, column=0, columnspan=2, pady=20)

    def add_book(self):
        # collect all information from the form
        data = {
            "title": self.book_entries["title_entry"].get(),
            "author": self.book_entries["author_entry"].get(),
            "isbn": self.book_entries["isbn_entry"].get(),
            "genre": self.book_entries["genre_entry"].get(),
            "available": True,
            "date_added": datetime.now().strftime("%Y-%m-%d")
        }

        if not all([data["title"], data["author"], data["isbn"]]):
            messagebox.showerror("Error", "Title, Author and ISBN are required fields!")
            return

        if not data["isbn"].isdigit():
            messagebox.showerror("Error", "ISBN must contain only numbers!")
            return

        books = self._load_books()

        if any(book.get("isbn") == data["isbn"] for book in books):
            messagebox.showerror("Error", "A book with this ISBN already exists!")
            return

        books.append(data)

        self._save_books(books)

        messagebox.showinfo("Success", "Book added successfully!")

        self.show_library()

    def show_edit_book(self):
        self._clear_content()

        edit_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        edit_frame.pack(fill="x", padx=10, pady=10)

        header_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 10))

        title_label = ctk.CTkLabel(header_frame, text="Edit Books", font=("Century Gothic", 24, "bold"))
        title_label.grid(row=0, column=0, sticky="w")

        # Search bar
        search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_frame.grid(row=0, column=1, sticky="e")

        search_entry = ctk.CTkEntry(search_frame, width=200, placeholder_text="Search books to edit...")
        search_entry.pack(side="left", padx=(285, 10), pady=(10, 0))

        def on_search(*args):
            self.search_books_to_edit(search_entry)

        search_entry.bind("<KeyRelease>", on_search)

        ctk.CTkButton(search_frame, text="Search", width=80,
                      command=lambda: self.search_books_to_edit(search_entry)).pack(anchor="e", padx=(0, 10),
                                                                                    pady=(10, 0))

        self.display_books_for_editing()

    def search_books_to_edit(self, search_entry=None):
        query = search_entry.get().lower() if search_entry else ""

        books = self._load_books()

        if query:
            results = [book for book in books if
                       query in book.get("title", "").lower() or
                       query in book.get("author", "").lower() or
                       query in book.get("isbn", "").lower() or
                       query in book.get("genre", "").lower()]
        else:
            results = books

        for widget in self.content_frame.winfo_children():
            if len(self.content_frame.winfo_children()) > 1 and widget != self.content_frame.winfo_children()[0]:
                widget.destroy()

        if query:
            results_label = ctk.CTkLabel(self.content_frame,
                                         text=f"Found {len(results)} matching books for '{query}'")
            results_label.pack(pady=(10, 5))

        if not results:
            ctk.CTkLabel(self.content_frame, text="No matching books found").pack(pady=20)
            return

        self.display_books_for_editing(results)

    def display_books_for_editing(self, books=None):
        if books is None:
            books = self._load_books()

        if not books:
            ctk.CTkLabel(self.content_frame, text="No books available in the library").pack(pady=20)
            return

        books_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        books_frame.pack(fill="both", expand=True)

        columns = 3
        for i in range(columns):
            books_frame.columnconfigure(i, weight=1)

        for i, book in enumerate(books):
            row, col = divmod(i, columns)

            card = ctk.CTkFrame(books_frame, corner_radius=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            ctk.CTkLabel(card, text=book.get("title", ""),
                         font=("Century Gothic", 16, "bold")).pack(pady=(10, 5), padx=10)
            ctk.CTkLabel(card, text=f"Author: {book.get('author', 'Unknown')}").pack(pady=2, padx=10, anchor="w")
            ctk.CTkLabel(card, text=f"ISBN: {book.get('isbn', 'N/A')}").pack(pady=2, padx=10, anchor="w")
            ctk.CTkLabel(card, text=f"Genre: {book.get('genre', 'N/A')}").pack(pady=2, padx=10, anchor="w")

            availability = book.get("available", True)
            status_text = "Status: Available" if availability else "Status: Borrowed"
            status_color = "#28a745" if availability else "#dc3545"

            ctk.CTkLabel(card, text=status_text, text_color=status_color).pack(pady=2, padx=10, anchor="w")

            buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
            buttons_frame.pack(pady=10, padx=10, fill="x")

            ctk.CTkButton(buttons_frame, text="Edit",
                          command=lambda isbn=book.get("isbn"): self.edit_book(isbn),
                          width=80).pack(side="left", padx=(0, 5))

            ctk.CTkButton(buttons_frame, text="Delete",
                          command=lambda isbn=book.get("isbn"): self.delete_book(isbn),
                          fg_color="#D35B58", hover_color="#C77C78",
                          width=80).pack(side="right", padx=(5, 0))

    def edit_book(self, isbn):
        if not isbn:
            messagebox.showerror("Error", "Please enter a valid ISBN!")
            return

        books = self._load_books()
        book = next((b for b in books if b.get("isbn") == isbn), None)

        if not book:
            messagebox.showerror("Error", "Book not found!")
            return

        self.current_book_isbn = isbn

        self._clear_content()

        form_frame = ctk.CTkFrame(self.content_frame)
        form_frame.pack(pady=20, padx=20, fill="x")

        fields = [
            ("Title:", "title_entry", book.get("title", "")),
            ("Author:", "author_entry", book.get("author", "")),
            ("ISBN:", "isbn_entry", book.get("isbn", "")),
            ("Genre:", "genre_entry", book.get("genre", "")),
        ]

        self.book_entries = {}
        for i, (label_text, entry_name, value) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=label_text).grid(row=i, column=0, padx=10, pady=10, sticky="e")
            entry = ctk.CTkEntry(form_frame, width=300)
            entry.insert(0, value)
            entry.grid(row=i, column=1, padx=10, pady=10, sticky="w")
            self.book_entries[entry_name] = entry

        ctk.CTkButton(form_frame, text="Update Book", command=self.update_book).grid(
            row=len(fields) + 1, column=0, columnspan=2, pady=20)

    def update_book(self):
        if not self.current_book_isbn:
            messagebox.showerror("Error", "No book selected for editing!")
            return

        data = {
            "title": self.book_entries["title_entry"].get(),
            "author": self.book_entries["author_entry"].get(),
            "isbn": self.book_entries["isbn_entry"].get(),
            "genre": self.book_entries["genre_entry"].get(),
        }

        # Validation
        if not all([data["title"], data["author"], data["isbn"]]):
            messagebox.showerror("Error", "Title, Author and ISBN are required fields!")
            return

        if not data["isbn"].isdigit():
            messagebox.showerror("Error", "ISBN must contain only numbers!")
            return

        books = self._load_books()

        # check for ISBN conflict
        if data["isbn"] != self.current_book_isbn and any(book.get("isbn") == data["isbn"] for book in books):
            messagebox.showerror("Error", "A book with this ISBN already exists!")
            return

        for book in books:
            if book.get("isbn") == self.current_book_isbn:
                data["available"] = book.get("available", True)
                data["date_added"] = book.get("date_added", datetime.now().strftime("%Y-%m-%d"))
                for key, value in data.items():
                    book[key] = value
                break

        self._save_books(books)

        messagebox.showinfo("Success", "Book updated successfully!")
        self.show_library()

    def delete_book(self, isbn):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this book?"):
            books = self._load_books()

            index = next((i for i, book in enumerate(books) if book.get("isbn") == isbn), -1)

            if index >= 0:
                book = books[index]
                if not book.get("available", True):
                    messagebox.showerror("Error", "Cannot delete a book that is currently borrowed!")
                    return

                books.pop(index)
                self._save_books(books)
                messagebox.showinfo("Success", "Book deleted successfully!")
                self.show_library()
            else:
                messagebox.showerror("Error", "Book not found!")

    def borrow_book(self, isbn):
        # Load users for selection
        users = self._load_users()
        if not users:
            messagebox.showerror("Error", "No users found in the system!")
            return

        book = self._get_book_by_isbn(isbn)
        if not book:
            messagebox.showerror("Error", "Book not found!")
            return

        if not book.get("available", True):
            messagebox.showerror("Error", "This book is not available for borrowing!")
            return

        user_dialog = ctk.CTkToplevel(self)
        user_dialog.title("Select User")
        user_dialog.geometry("400x500")
        user_dialog.grab_set()  # Make dialog modal

        dialog_frame = ctk.CTkFrame(user_dialog)
        dialog_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(dialog_frame,
                     text=f"Select a user to borrow '{book.get('title', '')}'",
                     font=("Century Gothic", 16, "bold")).pack(pady=(0, 20))

        search_frame = ctk.CTkFrame(dialog_frame)
        search_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=(0, 10))
        search_entry = ctk.CTkEntry(search_frame, width=200)
        search_entry.pack(side="left", fill="x", expand=True)

        users_frame = ctk.CTkScrollableFrame(dialog_frame)
        users_frame.pack(fill="both", expand=True)

        selected_username = None

        def select_user(username):
            nonlocal selected_username
            selected_username = username
            user_dialog.destroy()

        def display_users(search_text=""):
            for widget in users_frame.winfo_children():
                widget.destroy()

            filtered_users = [
                user for user in users
                if search_text.lower() in user.get("username", "").lower() or
                   search_text.lower() in user.get("name", "").lower()
            ]

            if not filtered_users:
                ctk.CTkLabel(users_frame, text="No matching users found").pack(pady=20)
                return

            for user in filtered_users:
                user_frame = ctk.CTkFrame(users_frame)
                user_frame.pack(fill="x", pady=5)

                info_frame = ctk.CTkFrame(user_frame, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

                ctk.CTkLabel(info_frame,
                             text=user.get("name", ""),
                             font=("Century Gothic", 14, "bold")).pack(anchor="w")

                ctk.CTkLabel(info_frame,
                             text=f"Username: {user.get('username', '')}").pack(anchor="w")

                borrows = self._load_borrows()
                user_borrows = [b for b in borrows if b.get("username") == user.get("username")]
                borrow_count = len(user_borrows)

                status_text = f"Borrowed: {borrow_count}/3 books"
                status_color = "#28a745" if borrow_count < 3 else "#dc3545"

                ctk.CTkLabel(info_frame,
                             text=status_text,
                             text_color=status_color).pack(anchor="w")

                select_btn = ctk.CTkButton(
                    user_frame,
                    text="Select",
                    width=80,
                    state="normal" if borrow_count < 3 else "disabled",
                    command=lambda u=user.get("username"): select_user(u)
                )
                select_btn.pack(side="right", padx=10, pady=10)

        def on_search(*args):
            display_users(search_entry.get())

        search_entry.bind("<KeyRelease>", on_search)

        display_users()

        self.wait_window(user_dialog)

        # If no user was selected, return
        if not selected_username:
            return

        today = datetime.now()
        due_date = today + timedelta(days=14)  # 2 weeks borrowing period

        borrow_record = {
            "isbn": isbn,
            "username": selected_username,
            "borrow_date": today.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d")
        }

        # Update book availability
        books = self._load_books()
        for b in books:
            if b.get("isbn") == isbn:
                b["available"] = False
                break

        self._save_books(books)
        borrows = self._load_borrows()
        borrows.append(borrow_record)
        self._save_borrows(borrows)

        user = self._get_user_by_username(selected_username)
        user_name = user.get("name", selected_username) if user else selected_username

        messagebox.showinfo("Success",
                            f"Book borrowed successfully by {user_name}!\nDue date: {borrow_record['due_date']}")
        self.show_library()

    def show_borrowed(self):
        self._clear_content()

        borrowed_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        borrowed_frame.pack(fill="x", padx=10, pady=10)

        title_frame = ctk.CTkFrame(borrowed_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(10, 10))

        ctk.CTkLabel(title_frame, text="Borrowed Books",
                     font=("Century Gothic", 24, "bold")).pack(anchor="w")

        borrows = self._load_borrows()
        if not borrows:
            ctk.CTkLabel(self.content_frame, text="No books are currently borrowed").pack(pady=20)
            return

        headers = ["Book Title", "Borrowed By", "Borrow Date", "Due Date", "Actions"]
        widths = [0.3, 0.2, 0.15, 0.15, 0.2]

        table_container = ctk.CTkFrame(self.content_frame)
        table_container.pack(fill="both", expand=True, pady=50)

        for i, width in enumerate(widths):
            table_container.columnconfigure(i, weight=int(width * 100))

        for i, header in enumerate(headers):
            ctk.CTkLabel(
                table_container,
                text=header,
                font=("Century Gothic", 12, "bold"),
            ).grid(row=0, column=i, sticky="ew", padx=4, pady=(5, 10))

        for row_idx, record in enumerate(borrows):
            book = self._get_book_by_isbn(record.get("isbn", ""))
            book_title = book.get("title", "Unknown") if book else "Unknown"

            user = self._get_user_by_username(record.get("username", ""))
            user_name = user.get("name", record.get("username", "Unknown")) if user else record.get("username",
                                                                                                    "Unknown")

            row_color = "#F0F0F0" if row_idx % 2 == 0 else "#FFFFFF"

            cell_data = [book_title, user_name, record.get("borrow_date", ""), record.get("due_date", "")]
            for col_idx, text in enumerate(cell_data):
                ctk.CTkLabel(
                    table_container,
                    text=text,
                    fg_color=row_color
                ).grid(row=row_idx + 1, column=col_idx, sticky="ew", padx=2, pady=3)

            actions_frame = ctk.CTkFrame(table_container, fg_color=row_color)
            actions_frame.grid(row=row_idx + 1, column=4, sticky="ew", padx=2, pady=3)

            ctk.CTkButton(
                actions_frame,
                text="Return",
                width=80,
                command=lambda isbn=record.get("isbn", ""), username=record.get("username", ""):
                self.return_book(isbn, username)
            ).pack(anchor="center", padx=5, pady=3)

    def return_book(self, isbn, username):
        if not isbn or not username:
            messagebox.showerror("Error", "Invalid book or user!")
            return

        books = self._load_books()
        book_updated = False

        for book in books:
            if book.get("isbn") == isbn:
                book["available"] = True
                book_updated = True
                break

        if book_updated:
            self._save_books(books)

            borrows = self._load_borrows()
            borrows = [b for b in borrows if not (b.get("isbn") == isbn and b.get("username") == username)]
            self._save_borrows(borrows)

            messagebox.showinfo("Success", "Book returned successfully!")
            self.show_borrowed()
        else:
            messagebox.showerror("Error", "Book not found!")

    def show_users(self):
        self._clear_content()

        users = self._load_users()
        if not users:
            ctk.CTkLabel(self.content_frame, text="No users registered").pack(pady=20)
            return

        grid_frame = ctk.CTkFrame(self.content_frame)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)

        widths = [0.25, 0.15, 0.1, 0.2, 0.15, 0.15]
        headers = ["Name", "Username", "Role", "Email", "Contact", "Actions"]

        for i, width in enumerate(widths):
            grid_frame.columnconfigure(i, weight=int(width * 100))

        for i, header in enumerate(headers):
            ctk.CTkLabel(
                grid_frame,
                text=header,
                font=("Century Gothic", 12, "bold")
            ).grid(row=0, column=i, sticky="w", padx=5, pady=(5, 10))

        separator = ctk.CTkFrame(grid_frame, height=1, fg_color="#CCCCCC")
        separator.grid(row=1, column=0, columnspan=len(headers), sticky="ew", pady=(0, 5))

        for i, user in enumerate(users):
            row_index = i + 2  # +2 because row 0 is headers and row 1 is separator

            row_color = "#F0F0F0" if i % 2 == 0 else "#FFFFFF"

            user_data = [
                user.get("name", ""),
                user.get("username", ""),
                user.get("role", ""),
                user.get("email", ""),
                user.get("contact", "")
            ]

            for j, data in enumerate(user_data):
                cell_frame = ctk.CTkFrame(grid_frame, fg_color=row_color)
                cell_frame.grid(row=row_index, column=j, sticky="ew", padx=2, pady=2)

                ctk.CTkLabel(
                    cell_frame,
                    text=data,
                    fg_color=row_color
                ).pack(anchor="w", padx=5, pady=5)

            actions_frame = ctk.CTkFrame(grid_frame, fg_color=row_color)
            actions_frame.grid(row=row_index, column=5, sticky="ew", padx=2, pady=2)

            ctk.CTkButton(
                actions_frame,
                text="Delete",
                width=80,
                fg_color="#D35B58",
                hover_color="#C77C78",
                command=lambda username=user.get("username", ""): self.delete_user(username)
            ).pack(anchor="center", padx=5, pady=5)

            if i < len(users) - 1:  # don't add separator after the last row
                row_sep = ctk.CTkFrame(grid_frame, height=1, fg_color="#EEEEEE")
                row_sep.grid(row=row_index + 1, column=0, columnspan=len(headers), sticky="ew")

    def delete_user(self, username):
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete user '{username}'?"):
            borrows = self._load_borrows()
            if any(b.get("username") == username for b in borrows):
                messagebox.showerror("Error", "Cannot delete user with borrowed books!")
                return

            users = self._load_users()
            users = [u for u in users if u.get("username") != username]
            self._save_users(users)

            messagebox.showinfo("Success", "User deleted successfully!")
            self.show_users()

    def _load_books(self):
        books = []
        try:
            with open("books.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return[]

    def _save_books(self, books):
        with open("books.json", "w", encoding="utf-8") as f:
            json.dump(books, f, indent=4)

    def _load_borrows(self):
        if os.path.exists("borrows.json"):
            try:
                with open("borrows.json", "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return []
        return []

    def _save_borrows(self, borrows):
        with open("borrows.json", "w") as file:
            json.dump(borrows, file, indent=4)

    def _load_users(self):
        if os.path.exists("users.json"):
            try:
                with open("users.json", "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return []
        return []

    def _save_users(self, users):
        with open("users.json", "w") as file:
            json.dump(users, file, indent=4)

    def _get_book_by_isbn(self, isbn):
        books = self._load_books()
        return next((book for book in books if book.get("isbn") == isbn), None)

    def _get_user_by_username(self, username):
        users = self._load_users()
        return next((user for user in users if user.get("username") == username), None)

class UserDashboard(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db = Database()

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")

        self.username_label = ctk.CTkLabel(sidebar, text="User", font=("Century Gothic", 20, "bold"))
        self.username_label.pack(padx=20, pady=20)

        nav_buttons = [
            ("Browse Books", self.show_library),
            ("My Favorites", self.show_favorites),
            ("My Borrowed Books", self.show_borrowed),
            ("My Account", self.show_account)
        ]

        for text, command in nav_buttons:
            ctk.CTkButton(sidebar, text=text, command=command).pack(padx=20, pady=10, fill="x")

        ctk.CTkButton(sidebar, text="Logout", fg_color="#D35B58", hover_color="#C77C78",
                      command=lambda: controller.show_frame(LoginPage)).pack(
            padx=20, pady=10, side="bottom", fill="x")

        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(1, weight=1)

        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.columnconfigure(1, weight=1)

        # # Title label (will be updated based on current view)
        # self.title_label = ctk.CTkLabel(self.header_frame, text="", font=("Century Gothic", 24, "bold"))
        # self.title_label.grid(row=0, column=0, sticky="w")#diri img

        # Search bar
        self.search_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.search_frame.grid(row=0, column=1, sticky="e")

        self.search_entry = ctk.CTkEntry(self.search_frame, width=200, placeholder_text="Search books...")
        self.search_entry.pack(side="left", padx=(0, 10), pady=(10,0))
        self.search_entry.bind("<Return>", lambda e: self.search_books())

        ctk.CTkButton(self.search_frame, text="Search", width=80,
                      command=self.search_books).pack(side="left", padx=(0, 10), pady=(10,0))

        self.content_frame = ctk.CTkScrollableFrame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky="nsew")

    def refresh_content(self):
        if self.controller.current_user:
            self.username_label.configure(text=self.controller.current_user.get("name",
                                                                                self.controller.current_user.get(
                                                                                    "username", "User")))

        self.show_library()

    def _clear_content(self):
        """Clear the content area"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def search_books(self):
        self._clear_content()
        """Search books based on entry field"""
        query = self.search_entry.get().lower()
        if not query:
            self.show_library()
            return

        self._clear_content()

        back_btn = ctk.CTkButton(self.content_frame, text="← Back to Library",
                                 fg_color="transparent", text_color=("#1F6AA5"),
                                 hover_color=("#E5E5E5"), width=150,
                                 command=self.show_library)
        back_btn.pack(anchor="w", pady=(0, 10))

        books = self._load_books()
        results = [book for book in books if
                   query in book.get("title", "").lower() or
                   query in book.get("author", "").lower() or
                   query in book.get("isbn", "").lower() or
                   query in book.get("genre", "").lower()]

        if not results:
            ctk.CTkLabel(self.content_frame, text="No matching books found").pack(pady=20)
            return

        self._display_books(results)

    def show_library(self):
        self._clear_content()

        books = self._load_books()
        if not books:
            ctk.CTkLabel(self.content_frame, text="No books available in the library").pack(pady=20)
            return

        self._display_books(books)

    def _display_books(self, books, is_favorites=False):
        books_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        books_frame.pack(fill="both", expand=True)

        columns = 3
        for i in range(columns):
            books_frame.columnconfigure(i, weight=1)

        for i, book in enumerate(books):
            row, col = divmod(i, columns)

            card = ctk.CTkFrame(books_frame, corner_radius=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            ctk.CTkLabel(card, text=book.get("title", ""),
                         font=("Century Gothic", 16, "bold")).pack(pady=(10, 5), padx=10)
            ctk.CTkLabel(card, text=f"Author: {book.get('author', 'Unknown')}").pack(pady=2, padx=10, anchor="w")
            ctk.CTkLabel(card, text=f"ISBN: {book.get('isbn', 'N/A')}").pack(pady=2, padx=10, anchor="w")
            ctk.CTkLabel(card, text=f"Genre: {book.get('genre', 'N/A')}").pack(pady=2, padx=10, anchor="w")

            availability = book.get("available", True)
            status_text = "Status: Available" if availability else "Status: Not Available"
            status_color = "#28a745" if availability else "#dc3545"

            ctk.CTkLabel(card, text=status_text, text_color=status_color).pack(pady=2, padx=10, anchor="w")

            book_isbn = book.get("isbn", "")
            if is_favorites:
                ctk.CTkButton(
                    card,
                    text="Remove from favorites",
                    width=150,
                    fg_color="#dc3545",
                    hover_color="#c82333",
                    command=lambda isbn=book_isbn: self.remove_from_favorites(isbn)
                ).pack(pady=10, padx=10)
            else:
                ctk.CTkButton(
                    card,
                    text="Add to favorites",
                    width=120,
                    command=lambda isbn=book_isbn: self.add_to_favorites(isbn)
                ).pack(pady=10, padx=10)

    def add_to_favorites(self, isbn):
        book = self.db.get_book_by_isbn(isbn)
        if not book:
            messagebox.showerror("Error", "Book not found in database")
            return

        if self.db.is_book_in_favorites(isbn):
            messagebox.showinfo("Info", "This book is already in your favorites")
            return

        if self.db.add_book_to_favorites(isbn):
            messagebox.showinfo("Success", "Book added to favorites")
        else:
            messagebox.showerror("Error", "Failed to add book to favorites")

    def remove_from_favorites(self, isbn):
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to remove this book from favorites?")
        if not confirm:
            return

        if self.db.remove_book_from_favorites(isbn):
            messagebox.showinfo("Success", "Book removed from favorites")
        else:
            messagebox.showerror("Error", "Failed to remove book from favorites")

        self.show_favorites()

    def show_favorites(self):
        self._clear_content()

        favorites_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        favorites_frame.pack(fill="x", padx=10, pady=10)

        header_frame = ctk.CTkFrame(favorites_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 10))

        ctk.CTkLabel(header_frame, text="My Favorites",
                     font=("Century Gothic", 18, "bold")).pack(anchor="w")

        favorite_books = self.db.get_favorite_books()

        if not favorite_books:
            empty_label = ctk.CTkLabel(
                self.content_frame,
                text="You don't have any favorite books yet",
                font=("Century Gothic", 16)
            )
            empty_label.pack(pady=50)
            return

        self._display_books(favorite_books, is_favorites=True)

    def show_borrowed(self):
        if not self.controller.current_user:
            messagebox.showerror("Error", "You must be logged in to view borrowed books!")
            return

        self._clear_content()

        borrows = self._load_borrows()
        user_borrows = [b for b in borrows if b.get("username") == self.controller.current_user.get("username")]

        if not user_borrows:
            ctk.CTkLabel(self.content_frame, text="You have not borrowed any books").pack(pady=20)
            return

        for borrow in user_borrows:
            book = self._get_book_by_isbn(borrow.get("isbn"))
            if not book:
                continue

            card = ctk.CTkFrame(self.content_frame, corner_radius=10)
            card.pack(fill="x", padx=10, pady=10)

            details_frame = ctk.CTkFrame(card, fg_color="transparent")
            details_frame.pack(fill="x", padx=15, pady=15)
            details_frame.columnconfigure(1, weight=1)

            ctk.CTkLabel(details_frame, text=book.get("title", "Unknown"),
                         font=("Century Gothic", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w",
                                                                   pady=(0, 5))
            ctk.CTkLabel(details_frame, text=f"by {book.get('author', 'Unknown')}").grid(
                row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

            ctk.CTkLabel(details_frame, text="Borrowed:").grid(row=2, column=0, sticky="w", pady=2)
            ctk.CTkLabel(details_frame, text=borrow.get("borrow_date", "")).grid(row=2, column=1, sticky="w", pady=2)

            ctk.CTkLabel(details_frame, text="Due date:").grid(row=3, column=0, sticky="w", pady=2)
            due_date_label = ctk.CTkLabel(details_frame, text=borrow.get("due_date", ""))
            due_date_label.grid(row=3, column=1, sticky="w", pady=2)

            if datetime.strptime(borrow.get("due_date", ""), "%Y-%m-%d") < datetime.now():
                due_date_label.configure(text_color="#D35B58")


    def show_account(self):
        if not self.controller.current_user:
            messagebox.showerror("Error", "You must be logged in to view account details!")
            return

        self._clear_content()

        account_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        account_frame.pack(fill="x", padx=10, pady=10)

        header_frame = ctk.CTkFrame(account_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 10))

        ctk.CTkLabel(header_frame, text="Account Information",
                     font=("Century Gothic", 18, "bold")).pack(anchor="w")

        details_frame = ctk.CTkFrame(account_frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=20, pady=10)

        fields = [
            ("Full Name:", self.controller.current_user.get("name", "")),
            ("Username:", self.controller.current_user.get("username", "")),
            ("Role:", self.controller.current_user.get("role", "")),
            ("Student ID:", self.controller.current_user.get("student_id", "")),
            ("Email:", self.controller.current_user.get("email", "")),
            ("Contact:", self.controller.current_user.get("contact", "")),
            ("Address:", self.controller.current_user.get("address", ""))
        ]

        for i, (label, value) in enumerate(fields):
            ctk.CTkLabel(details_frame, text=label, font=("Century Gothic", 12, "bold")).grid(
                row=i, column=0, sticky="w", padx=5, pady=8)
            ctk.CTkLabel(details_frame, text=value).grid(
                row=i, column=1, sticky="w", padx=20, pady=8)

        stats_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        stats_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(stats_frame, text="Library Statistics",
                     font=("Century Gothic", 18, "bold")).pack(anchor="w", padx=20, pady=(20, 10))

        borrows = self._load_borrows()
        user_borrows = [b for b in borrows if b.get("username") == self.controller.current_user.get("username")]

        current_borrows = len(user_borrows)
        remaining = 3 - current_borrows  # Max 3 books

        stats_details = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_details.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(stats_details, text="Currently Borrowed:").grid(
            row=0, column=0, sticky="w", padx=5, pady=8)
        ctk.CTkLabel(stats_details, text=str(current_borrows)).grid(
            row=0, column=1, sticky="w", padx=20, pady=8)

        ctk.CTkLabel(stats_details, text="Remaining Borrowing Slots:").grid(
            row=1, column=0, sticky="w", padx=5, pady=8)
        ctk.CTkLabel(stats_details, text=str(remaining)).grid(
            row=1, column=1, sticky="w", padx=20, pady=8)

    def _load_books(self):
        if os.path.exists("books.json"):
            try:
                with open("books.json", "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return []
        return []

    def _save_books(self, books):
        with open("books.json", "w") as file:
            json.dump(books, file, indent=4)

    def _load_borrows(self):
        if os.path.exists("borrows.json"):
            try:
                with open("borrows.json", "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return []
        return []

    def _save_borrows(self, borrows):
        with open("borrows.json", "w") as file:
            json.dump(borrows, file, indent=4)

    def _get_book_by_isbn(self, isbn):
        books = self._load_books()
        return next((book for book in books if book.get("isbn") == isbn), None)

if __name__ == "__main__":
    app = App()
    app.mainloop()