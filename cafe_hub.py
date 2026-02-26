import tkinter as tk
from tkinter import messagebox
import sqlite3
import os
import hashlib
import datetime
from PIL import Image, ImageTk, ImageDraw
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG_IMAGES = True  # Set to False to disable image debug messages


def asset(filename: str) -> str:
    path = os.path.join(BASE_DIR, filename)
    if DEBUG_IMAGES and not os.path.exists(path):
        print(f"⚠️  Image not found: {path}")
        print(f"   Looking in: {BASE_DIR}")
    return path
# Validation


def validate_email(email: str) -> tuple:
    """Validate email must contain @gmail.com"""
    if not email:
        return False, "Email is required."
    if "@gmail.com" not in email.lower():
        return False, "Email must be a Gmail address (@gmail.com)."
    # Basic email format check
    email_pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    if not re.match(email_pattern, email.lower()):
        return False, "Invalid email format. Use format: username@gmail.com"
    return True, ""


def validate_password(password: str) -> tuple:
    """
    Validate password:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one number
    - At least one special character
    """
    if not password:
        return False, "Password is required."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)."

    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number (0-9)."

    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~]', password):
        return False, "Password must contain at least one special character (!@#$%^&* etc.)."

    return True, ""


# 2 database one for login and another for order so that the data doesnt conflict
LOGIN_DB = os.path.join(BASE_DIR, "login.db")
ORDERS_DB = os.path.join(BASE_DIR, "orders.db")


def init_login_db():
    """Create login.db and the users table."""
    conn = sqlite3.connect(LOGIN_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            reset_code TEXT,
            created    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
