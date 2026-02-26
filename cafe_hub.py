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
