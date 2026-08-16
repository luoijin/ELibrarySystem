"""
styles.py
=========

Central style configuration for the ELibrary System.

This module is the SINGLE source of truth for every colour, font and
dimension used throughout the application. No widget in the codebase
should hard-code a colour, font family/size or padding value directly;
instead it must import the relevant constant from this module.

Rationale
---------
Centralising the visual language makes it possible to re-theme the
whole application (e.g. change the accent colour or font) by editing
a single file, keeps the UI visually consistent across every screen,
and satisfies the requirement that colours/fonts/dimensions must not
be hard-coded on individual widgets.
"""

import customtkinter as ctk

# ---------------------------------------------------------------------------
# Base CustomTkinter configuration
# ---------------------------------------------------------------------------
# The application always starts in light appearance mode with the built-in
# "blue" colour theme as a sane baseline. All of the constants below then
# override/extend that baseline where the specification requires a more
# specific value (e.g. an exact hex colour for the primary accent).
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
PRIMARY_COLOR = "#1F6AA5"          # Primary blue accent (buttons, headers)
PRIMARY_HOVER_COLOR = "#15507F"    # Slightly darker blue used on hover
SECONDARY_COLOR = "#4C7EA8"        # Secondary accent for less prominent actions
BUTTON_HOVER_COLOR = "#15507F"     # Standard hover colour for all buttons

BG_COLOR = "#F4F6F8"               # Main application background (light grey)
SURFACE_COLOR = "#FFFFFF"          # Cards / panels / frames sitting on BG_COLOR
SIDEBAR_COLOR = "#1B3A57"          # Dark-blue sidebar / navigation background

TEXT_COLOR = "#1A1A1A"             # Primary body text colour
TEXT_MUTED_COLOR = "#5A6472"       # Secondary / helper text colour
TEXT_ON_PRIMARY_COLOR = "#FFFFFF"  # Text placed on top of PRIMARY_COLOR
TEXT_ON_SIDEBAR_COLOR = "#E8EEF4"  # Text placed on top of SIDEBAR_COLOR

SUCCESS_COLOR = "#2E7D32"          # Positive status (e.g. "Available")
WARNING_COLOR = "#B8860B"          # Cautionary status (e.g. "Due Soon")
DANGER_COLOR = "#B3261E"           # Negative status (e.g. "Overdue", delete)
DANGER_HOVER_COLOR = "#7F1B16"     # Hover colour for destructive buttons
BORDER_COLOR = "#D6DCE2"           # Standard border / separator colour

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
# Century Gothic is used per the specification. CustomTkinter/Tkinter will
# silently fall back to a comparable system font if Century Gothic is not
# installed on the host operating system, so no additional handling is
# required here.
FONT_FAMILY = "Century Gothic"

FONT_SIZES = {
    "heading": 26,      # Page / dashboard titles
    "subheading": 18,   # Section titles
    "body": 14,         # Standard body text / widget labels
    "small": 12,        # Helper / caption text
}

FONT_WEIGHTS = {
    "regular": "normal",
    "bold": "bold",
}


def get_font(size_key: str = "body", weight_key: str = "regular") -> ctk.CTkFont:
    """Return a CTkFont built from the global font configuration.

    Args:
        size_key: One of the keys in ``FONT_SIZES`` ("heading",
            "subheading", "body", "small").
        weight_key: One of the keys in ``FONT_WEIGHTS`` ("regular", "bold").

    Returns:
        A configured ``customtkinter.CTkFont`` instance.
    """
    return ctk.CTkFont(
        family=FONT_FAMILY,
        size=FONT_SIZES.get(size_key, FONT_SIZES["body"]),
        weight=FONT_WEIGHTS.get(weight_key, FONT_WEIGHTS["regular"]),
    )


# ---------------------------------------------------------------------------
# Spacing & geometry
# ---------------------------------------------------------------------------
PADDING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
}

CORNER_RADIUS = {
    "sm": 4,
    "md": 8,
    "lg": 12,
}

BORDER_WIDTH = 1

# ---------------------------------------------------------------------------
# Window geometry
# ---------------------------------------------------------------------------
WINDOW_TITLE = "ELibrary System - University Library Management"
WINDOW_SIZE = "1100x700"
WINDOW_MIN_SIZE = (1000, 650)

# ---------------------------------------------------------------------------
# Widget sizing defaults
# ---------------------------------------------------------------------------
BUTTON_HEIGHT = 36
ENTRY_HEIGHT = 36
SIDEBAR_WIDTH = 220


def configure_ttk_style() -> None:
    """Re-style ttk.Treeview widgets to match the global visual language.

    ``tkinter.ttk.Treeview`` (used for tabular data such as book and
    patron lists) is part of the standard library, not CustomTkinter,
    so it does not automatically pick up CustomTkinter's theme. This
    function applies the same colour and font constants defined above
    to ttk so tables look consistent with the rest of the UI.

    Safe to call multiple times; each call simply re-applies the same
    configuration.
    """
    from tkinter import ttk

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Elib.Treeview",
        background=SURFACE_COLOR,
        fieldbackground=SURFACE_COLOR,
        foreground=TEXT_COLOR,
        rowheight=28,
        borderwidth=0,
        font=(FONT_FAMILY, FONT_SIZES["small"]),
    )
    style.configure(
        "Elib.Treeview.Heading",
        background=SIDEBAR_COLOR,
        foreground=TEXT_ON_SIDEBAR_COLOR,
        font=(FONT_FAMILY, FONT_SIZES["small"], "bold"),
        borderwidth=0,
    )
    style.map(
        "Elib.Treeview",
        background=[("selected", PRIMARY_COLOR)],
        foreground=[("selected", TEXT_ON_PRIMARY_COLOR)],
    )
