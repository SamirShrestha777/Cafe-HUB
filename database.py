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

    def init_orders_db():
    """Create orders.db and the orders / order_items tables."""
    conn = sqlite3.connect(ORDERS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email   TEXT    NOT NULL,
            subtotal     REAL    NOT NULL,
            vat          REAL    NOT NULL,
            service_tax  REAL    NOT NULL,
            grand_total  REAL    NOT NULL,
            placed_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL REFERENCES orders(id),
            item_name  TEXT    NOT NULL,
            qty        INTEGER NOT NULL,
            unit_price REAL    NOT NULL,
            line_total REAL    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()
# login DB


def db_register(name: str, email: str, password: str, reset_code: str = ""):
    try:
        conn = sqlite3.connect(LOGIN_DB)
        c = conn.cursor()
        c.execute("INSERT INTO users (name, email, password, reset_code) VALUES (?, ?, ?, ?)",
                  (name, email, hash_password(password), reset_code))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        try:
            conn.close()
        except Exception:
            pass


def db_login(email: str, password: str):
    conn = sqlite3.connect(LOGIN_DB)
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE email=? AND password=?",
              (email, hash_password(password)))
    row = c.fetchone()
    conn.close()
    if row:
        return True, row[0]
    return False, "Invalid email or password."


def db_verify_reset_code(email: str, reset_code: str):
    """Verify if the email and reset code match."""
    conn = sqlite3.connect(LOGIN_DB)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE email=? AND reset_code=?",
              (email, reset_code))
    row = c.fetchone()
    conn.close()
    return row is not None


def db_update_password(email: str, new_password: str):
    """Update user's password."""
    try:
        conn = sqlite3.connect(LOGIN_DB)
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE email=?",
                  (hash_password(new_password), email))
        conn.commit()
        conn.close()
        return True, "Password updated successfully!"
    except Exception as e:
        return False, f"Error updating password: {e}"


# Database helper

def db_save_order(user_email: str, cart: dict) -> int:
    """Persist order to orders.db and return the new order id."""
    subtotal = sum(d["qty"] * d["price"] for d in cart.values())
    vat = round(subtotal * 0.13, 2)
    service_tax = round(subtotal * 0.10, 2)
    grand_total = round(subtotal + vat + service_tax, 2)

    conn = sqlite3.connect(ORDERS_DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO orders (user_email, subtotal, vat, service_tax, grand_total) VALUES (?, ?, ?, ?, ?)",
        (user_email, subtotal, vat, service_tax, grand_total))
    order_id = c.lastrowid
    for name, data in cart.items():
        line = data["qty"] * data["price"]
        c.execute(
            "INSERT INTO order_items (order_id, item_name, qty, unit_price, line_total) VALUES (?, ?, ?, ?, ?)",
            (order_id, name, data["qty"], data["price"], line))
    conn.commit()
    conn.close()
    return order_id
