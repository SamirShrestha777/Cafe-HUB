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


# Colors

BG_CREAM = "#fdf8f3"
BG_FORM = "#fdf4e7"
GREEN_DARK = "#2d5a27"
GREEN_MED = "#4a7c40"
BROWN = "#3b1f0a"
ORANGE = "#f5a623"
ORANGE_HOV = "#e09420"
GRAY_LIGHT = "#e8e0d6"
GRAY_TEXT = "#888"
WHITE = "#ffffff"
MENU_RED = "#8b1a1a"
SPEC_RED = "#8b1a1a"
STAR_CLR = "#f5a623"
BAG_BG = "#f5f5f5"

# image helper


def make_circle_image(path: str, size: int):
    """Create a circular cropped image. Returns PhotoImage or None."""
    if not os.path.exists(path):
        if DEBUG_IMAGES:
            print(f"⚠️  Circle image not found: {path}")
        return None
    try:
        img = Image.open(path).convert("RGBA").resize(
            (size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(img, mask=mask)
        return ImageTk.PhotoImage(result)
    except Exception as e:
        if DEBUG_IMAGES:
            print(f"❌ Error loading circle image {path}: {e}")
        return None


def load_img_wh(filename, w, h, circle=False, cache=None):
    """Load an image resized to w×h, optionally circular cropped. Uses cache dict."""
    key = (filename, w, h, circle)
    if cache is not None and key in cache:
        return cache[key]

    path = asset(filename)
    if not os.path.exists(path):
        if cache is not None:
            cache[key] = None
        if DEBUG_IMAGES:
            print(f"⚠️  Image not found: {filename}")
        return None

    try:
        img = Image.open(path).convert("RGBA").resize((w, h), Image.LANCZOS)
        if circle:
            mask = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, w, h), fill=255)
            out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            out.paste(img, mask=mask)
            img = out
        ph = ImageTk.PhotoImage(img)
        if cache is not None:
            cache[key] = ph
        if DEBUG_IMAGES:
            print(f"✓ Loaded image: {filename}")
        return ph
    except Exception as e:
        if cache is not None:
            cache[key] = None
        if DEBUG_IMAGES:
            print(f"❌ Error loading image {filename}: {e}")
        return None

# place_holder entry wg

class PlaceholderEntry(tk.Entry):
    def __init__(self, master, placeholder, icon="", show_char="", **kw):
        super().__init__(master, **kw)
        self.placeholder = placeholder
        self.show_char = show_char
        self._active = False
        self.configure(fg=GRAY_TEXT, font=("Georgia", 11))
        self.insert(
            0, f"  {icon}  {placeholder}" if icon else f"  {placeholder}")
        self.bind("<FocusIn>",  self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _=None):
        if not self._active:
            self.delete(0, tk.END)
            self.configure(fg=BROWN, show=self.show_char)
            self._active = True

    def _on_focus_out(self, _=None):
        if not self.get():
            self._active = False
            self.configure(show="")
            icon_map = {"Name": "👤", "Email": "✉", "Password": "🔒"}
            icon = icon_map.get(self.placeholder, "")
            self.insert(0, f"  {icon}  {self.placeholder}" if icon
                        else f"  {self.placeholder}")
            self.configure(fg=GRAY_TEXT)

    def real_value(self) -> str:
        return self.get() if self._active else ""


# Menu
MENU_DATA = [
    ("MO:MO", [
        {"name": "Chicken Mo:Mo",  "emoji": "🥟", "img": "chickenmomo.jpg",      "price": 180,
         "short": "Steamed chicken dumplings...",
         "desc":  "Steamed chicken dumplings filled with minced chicken, ginger & spices, served with spicy tomato sauce.",
         "sku": "MM-CHK-001"},
        {"name": "Veg Mo:Mo",      "emoji": "🥟", "img": "vegmomo.jpg",           "price": 150,
         "short": "Steamed vegetable dumplings...",
         "desc":  "Steamed dumplings packed with fresh cabbage, carrot, onion & spices with tangy dipping sauce.",
         "sku": "MM-VEG-002"},
    ]),
    ("CHOWMEIN", [
        {"name": "Chicken Chowmein", "emoji": "🍜", "img": "chickenchowmein.jpg", "price": 220,
         "short": "Stir-fried noodles with chicken...",
         "desc":  "Wok-tossed egg noodles with tender chicken strips, bell peppers, carrots & soy-based sauce.",
         "sku": "CW-CHK-001"},
    ]),
    ("PIZZA", [
        {"name": "Margherita Pizza", "emoji": "🍕", "img": "margheritapizza.jpg", "price": 650,
         "short": "Classic tomato base, mozzarella...",
         "desc":  "Classic tomato sauce base with fresh mozzarella cheese and fragrant basil leaves.",
         "sku": "PZ-MAR-001"},
        {"name": "Chicken Pizza",    "emoji": "🍕", "img": "chickenpizza.jpg",    "price": 780,
         "short": "Grilled chicken, bell peppers...",
         "desc":  "Juicy grilled chicken with colorful bell peppers, red onions and a generous layer of mozzarella.",
         "sku": "PZ-CHK-002"},
    ]),
    ("TACO", [
        {"name": "Chicken Taco", "emoji": "🌮", "img": "chickentaco.jpg",         "price": 350,
         "short": "Crispy shell, grilled chicken...",
         "desc":  "Golden crispy taco shell filled with grilled chicken, fresh lettuce, salsa & sour cream.",
         "sku": "TC-CHK-001"},
        {"name": "Veg Taco",    "emoji": "🌮", "img": "vegtaco.jpg",              "price": 300,
         "short": "Crispy shell, fresh veggies...",
         "desc":  "Crispy shell loaded with seasoned mixed vegetables, guacamole, cheese & a tangy sauce.",
         "sku": "TC-VEG-002"},
    ]),
    ("FRENCH FRIES", [
        {"name": "French Fries", "emoji": "🍟", "img": "frenchfries.jpg",         "price": 180,
         "short": "Golden crispy fries, ketchup...",
         "desc":  "Perfectly golden and crispy shoestring fries seasoned with sea salt. Served with ketchup.",
         "sku": "FF-REG-001"},
    ]),
    ("COLD DRINKS", [
        {"name": "Fanta",  "emoji": "🍊", "img": "fanta.jpg",                     "price": 80,
         "short": "Chilled orange soft drink...",
         "desc":  "Refreshing chilled orange-flavored carbonated soft drink. 330ml can.",
         "sku": "CD-FAN-001"},
        {"name": "Sprite", "emoji": "🍋", "img": "sprite.jpg",                    "price": 80,
         "short": "Chilled lemon-lime soft drink...",
         "desc":  "Crisp lemon-lime flavored carbonated soft drink. 330ml can.",
         "sku": "CD-SPR-002"},
        {"name": "Coke",   "emoji": "🥤", "img": "coke.jpg",                      "price": 80,
         "short": "Classic cola, chilled...",
         "desc":  "The original refreshing classic cola. Chilled 330ml can.",
         "sku": "CD-COK-003"},
    ]),
    ("BURGER", [
        {"name": "Chicken Burger", "emoji": "🍔", "img": "chickenburger.jpg",     "price": 380,
         "short": "Grilled chicken patty, lettuce...",
         "desc":  "Juicy grilled chicken patty stacked with crisp lettuce, ripe tomato and signature mayo in a brioche bun.",
         "sku": "BG-CHK-001"},
        {"name": "Veg Burger",    "emoji": "🍔", "img": "vegburger.jpg",          "price": 320,
         "short": "Crispy veggie patty, sauce...",
         "desc":  "Wholesome veggie patty with fresh lettuce, tomato, pickles and our house signature sauce.",
         "sku": "BG-VEG-002"},
    ]),
]

SPECIAL_ITEMS = [
    {"name": "TACO",         "price": 350, "img": "chickentaco.jpg",  "emoji": "🌮",
     "desc": ("A focus on variety, personalisation, and sustainability. Our Taco is not just "
              "about delivering meals – it's about creating memorable moments around food. "
              "Crispy shell loaded with seasoned grilled chicken, fresh lettuce, salsa & sour cream.")},
    {"name": "PIZZA",        "price": 780, "img": "pizza.jpg",        "emoji": "🍕",
     "desc": ("Stone-baked perfection with a golden crust, rich tomato sauce, stretchy mozzarella "
              "and your favourite toppings. Every bite is a flavour journey you won't forget.")},
    {"name": "FRENCH FRIES", "price": 180, "img": "frenchfries.jpg",  "emoji": "🍟",
     "desc": ("Golden, crispy shoestring fries seasoned with sea salt and our secret spice blend. "
              "The perfect companion to any meal or a satisfying snack on their own.")},
    {"name": "BURGER",       "price": 380, "img": "chickenburger.jpg", "emoji": "🍔",
     "desc": ("A towering juicy chicken patty with crisp lettuce, ripe tomato, gherkins and our "
              "signature mayo sauce, all tucked inside a toasted brioche bun. Pure comfort in every bite.")},
]

# About page


def make_about_page(parent):
    BODY = (
        "Located in Block A of Softwarica College, Dillibazar, Kathmandu, "
        "our restaurant is a perfect spot for students, staff, and visitors "
        "looking for tasty yet wholesome meals. We believe in promoting a "
        "healthy life by serving food that is both nutritious and delicious. "
        "Our menu features a variety of freshly prepared chicken and vegetarian "
        "dishes made using quality ingredients and hygienic cooking practices. "
        "With affordable prices, quick service, and a friendly atmosphere, we "
        "aim to be your go-to place for enjoying good food every day."
    )
    BULLETS = [
        "Food Items management",
        "Table reservation",
        "Customer feedback portal",
        "Location-based services",
    ]

    f = tk.Frame(parent, bg=WHITE)

    # About us label
    tk.Label(f, text="ABOUT US",
             font=("PixelPurl", 22, "bold"),
             bg=WHITE, fg="#8b0000",
             anchor="w").place(x=800, y=20)

    # Thin divider
    tk.Frame(f, bg=GRAY_LIGHT, height=1).place(x=0, y=62, relwidth=1)

    # Left photo
    img_lbl = tk.Label(f, bg="#2a2a2a")
    img_lbl.place(x=16, y=80, width=390, height=460)
    fallback = tk.Label(img_lbl, text="🍽️", bg="#2a2a2a",
                        font=("Segoe UI Emoji", 60))
    fallback.place(relx=.5, rely=.5, anchor="center")

    # Keep PhotoImage alive via frame attribute
    photo_ref = [None]
    path = asset("soft.jpg")
    if os.path.exists(path):
        try:
            img = Image.open(path).convert(
                "RGB").resize((390, 460), Image.LANCZOS)
            photo_ref[0] = ImageTk.PhotoImage(img)
            img_lbl.configure(image=photo_ref[0])
            fallback.place_forget()
            if DEBUG_IMAGES:
                print("✓ Loaded about page image: soft.jpg")
        except Exception as e:
            if DEBUG_IMAGES:
                print(f"❌ Error loading about page image: {e}")
    f._about_photo = photo_ref  # prevents GC

    # Right panel
    right = tk.Frame(f, bg=WHITE)
    right.place(x=430, y=80, relwidth=1, width=-446, relheight=1, height=-90)

    body_lbl = tk.Label(right, text=BODY, font=("Georgia", 14), bg=WHITE, fg=BROWN,
                        justify="left", wraplength=560, anchor="nw")
    body_lbl.pack(anchor="nw", fill="x", padx=10, pady=(18, 30))
    right.bind("<Configure>",
               lambda e, lbl=body_lbl: lbl.configure(wraplength=max(200, e.width - 30)))

    tk.Frame(right, bg=GRAY_LIGHT, height=1).pack(
        fill="x", padx=10, pady=(0, 18))

    for item in BULLETS:
        row = tk.Frame(right, bg=WHITE)
        row.pack(anchor="w", fill="x", padx=10, pady=10)
        tk.Label(row, text="✦", font=("Georgia", 14, "bold"),
                 bg=WHITE, fg="#8b0000").pack(side="left", padx=(0, 10))
        tk.Label(row, text=item, font=("Georgia", 14),
                 bg=WHITE, fg=BROWN, anchor="w").pack(side="left")

    return f

# contact page

def make_contact_page(parent):
    CARDS = [
        ("location.png", "📍", "OUR ADDRESS",
         "Softwarica College,",       "Dillibazar, Kathmandu"),
        ("mail.png",     "✉",  "EMAIL ADDRESS", "caferica@gmail.com",         ""),
        ("phone.png",    "📞", "PHONE NUMBER",  "01–55440288 / 9878453365",   ""),
        ("clock.png",    "🕐", "OPENING TIME",  "9 AM  –  5 PM",              ""),
    ]

    f = tk.Frame(parent, bg=WHITE)

    # Contact heading
    tk.Label(f, text="CONTACT",
             font=("PixelPurl", 22, "bold"),
             bg=WHITE, fg="#8b0000",
             anchor="center").place(relx=0.5, y=20, anchor="n")

    # Thin divider (same as About page)
    tk.Frame(f, bg=GRAY_LIGHT, height=1).place(x=0, y=62, relwidth=1)

    # Cards centred in the page (same as original)
    outer = tk.Frame(f, bg=WHITE)
    outer.place(relx=0.5, rely=0.5, anchor="center")

    RED_CLR = "#e03a2e"
    CARD_BG_LOC = "#e8e4de"
    icon_refs = []   # prevent GC of PhotoImages

    for img_file, emoji, title, val1, val2 in CARDS:
        card = tk.Frame(outer, bg=CARD_BG_LOC,
                        width=240, height=290,
                        bd=0, relief="flat",
                        highlightbackground="#c8c2b8",
                        highlightthickness=1)
        card.pack(side="left", padx=18)
        card.pack_propagate(False)

        icon_path = asset(img_file)
        icon_ph = None
        if os.path.exists(icon_path):
            try:
                ico = Image.open(icon_path).convert(
                    "RGBA").resize((80, 80), Image.LANCZOS)
                icon_ph = ImageTk.PhotoImage(ico)
                icon_refs.append(icon_ph)
                if DEBUG_IMAGES:
                    print(f"✓ Loaded contact icon: {img_file}")
            except Exception as e:
                if DEBUG_IMAGES:
                    print(f"❌ Error loading contact icon {img_file}: {e}")
                icon_ph = None

        if icon_ph:
            icon_lbl = tk.Label(card, image=icon_ph, bg=CARD_BG_LOC)
            icon_lbl.image = icon_ph
            icon_lbl.pack(pady=(26, 0))
        else:
            cv_sz = 90
            cv = tk.Canvas(card, width=cv_sz, height=cv_sz,
                           bg=CARD_BG_LOC, bd=0, highlightthickness=0)
            cv.pack(pady=(22, 0))
            cv.create_oval(3, 3, cv_sz - 3, cv_sz - 3,
                           fill="#e03a2e", outline="")
            cv.create_text(cv_sz // 2, cv_sz // 2, text=emoji,
                           font=("Segoe UI Emoji", 28), fill=WHITE)

        tk.Label(card, text=title,
                 font=("PixelPurl", 18, "bold"),
                 bg=CARD_BG_LOC, fg=RED_CLR).pack(pady=(10, 6))
        tk.Label(card, text=val1,
                 font=("Georgia", 11),
                 bg=CARD_BG_LOC, fg=BROWN,
                 wraplength=210, justify="center").pack()
        if val2:
            tk.Label(card, text=val2,
                     font=("Georgia", 11),
                     bg=CARD_BG_LOC, fg=BROWN,
                     wraplength=210, justify="center").pack(pady=(2, 0))

    f._icon_refs = icon_refs   # GC guard
    return f

# Dashboard Page

def make_dashboard_page(parent, app):
    """Logged-in home page with user options"""
    f = tk.Frame(parent, bg=BG_CREAM)
    name_var = tk.StringVar(value="")

    # Header section
    header = tk.Frame(f, bg=BG_CREAM)
    header.pack(fill="x", pady=(40, 20))

    tk.Label(header, textvariable=name_var,
             font=("Georgia", 32, "bold"),
             bg=BG_CREAM, fg=BROWN).pack()
    tk.Label(header, text="Welcome back to CafeHub! ☕",
             font=("Georgia", 18),
             bg=BG_CREAM, fg=GREEN_MED).pack(pady=(5, 0))

    # Divider
    tk.Frame(f, bg=GRAY_LIGHT, height=2).pack(fill="x", padx=100, pady=30)

    # Quick actions section
    actions_frame = tk.Frame(f, bg=BG_CREAM)
    actions_frame.pack(expand=True)

    # Create action cards
    actions = [
        ("🍽️", "Browse Menu", "menu", ORANGE),
        ("⭐", "Special Offers", "special", "#e03a2e"),
        ("📞", "Contact Us", "contact", GREEN_DARK),
        ("ℹ️", "About Us", "about", "#8b1a1a"),
    ]

# HOME PAGE  
def make_home_page(parent, app):
    MODE_LOGIN  = "login"
    MODE_SIGNUP = "signup"
    mode = [MODE_LOGIN]   # mutable container for closure

    f = tk.Frame(parent, bg=BG_CREAM)

    # Left: form panel 
    left = tk.Frame(f, bg=BG_FORM, bd=0)
    left.place(relx=0.04, y=20, width=500, height=520)

    form_title = tk.Label(left, text="Log In",
                          font=("Georgia", 18, "bold"),
                          bg=BG_FORM, fg=BROWN)
    form_title.place(x=60, y=28)

    toggle_lbl = tk.Label(left,
                           text="Don't have an account? Sign Up",
                           font=("Georgia", 9),
                           bg=BG_FORM, fg=GREEN_MED, cursor="hand2")
    toggle_lbl.place(x=60, y=60)

    # Name field (hidden in login mode)
    name_frame = tk.Frame(left, bg=WHITE, bd=1, relief="solid",
                          highlightbackground=GRAY_LIGHT, highlightthickness=1)
    entry_name = PlaceholderEntry(name_frame, "Name", icon="👤",
                                   bg=WHITE, bd=0, relief="flat", highlightthickness=0)
    entry_name.place(x=4, y=4, width=330, height=34)

    # Reset Code field (hidden in login mode) - NEW
    code_frame = tk.Frame(left, bg=WHITE, bd=1, relief="solid",
                          highlightbackground=GRAY_LIGHT, highlightthickness=1)
    entry_code = PlaceholderEntry(code_frame, "6-Digit Reset Code", icon="🔐",
                                   bg=WHITE, bd=0, relief="flat", highlightthickness=0)
    entry_code.place(x=4, y=4, width=330, height=34)

    # Email field
    email_frame = tk.Frame(left, bg=WHITE, bd=0,
                            highlightbackground=GRAY_LIGHT, highlightthickness=1)
    email_frame.place(x=60, y=100, width=340, height=42)
    entry_email = PlaceholderEntry(email_frame, "Email", icon="✉",
                                    bg=WHITE, bd=0, relief="flat", highlightthickness=0)
    entry_email.place(x=4, y=4, width=330, height=34)

    # Password field
    pw_frame = tk.Frame(left, bg=WHITE, bd=0,
                         highlightbackground=GRAY_LIGHT, highlightthickness=1)
    pw_frame.place(x=60, y=154, width=340, height=42)
    entry_pw = PlaceholderEntry(pw_frame, "Password", icon="🔒", show_char="•",
                                 bg=WHITE, bd=0, relief="flat", highlightthickness=0)
    entry_pw.place(x=4, y=4, width=330, height=34)

    # Show Password checkbox
    show_pw_var = tk.BooleanVar(value=False)
    def toggle_show_password():
        if entry_pw._active:
            entry_pw.configure(show="" if show_pw_var.get() else "•")
    show_pw_frame = tk.Frame(left, bg=BG_FORM)
    show_pw_frame.place(x=60, y=202)
    show_pw_cb = tk.Checkbutton(show_pw_frame, variable=show_pw_var,
                                 bg=BG_FORM, activebackground=BG_FORM,
                                 fg=BROWN, selectcolor=ORANGE,
                                 relief="flat", cursor="hand2",
                                 command=toggle_show_password)
    show_pw_cb.pack(side="left")
    tk.Label(show_pw_frame, text="Show Password",
             font=("Georgia", 10), bg=BG_FORM, fg=BROWN).pack(side="left")

    # Remember me
    remember_var = tk.BooleanVar(value=True)
    rem_frame = tk.Frame(left, bg=BG_FORM)
    rem_frame.place(x=60, y=228)
    cb = tk.Checkbutton(rem_frame, variable=remember_var,
                         bg=BG_FORM, activebackground=BG_FORM,
                         fg=BROWN, selectcolor=ORANGE,
                         relief="flat", cursor="hand2")
    cb.pack(side="left")
    tk.Label(rem_frame, text="Remember me?",
             font=("Georgia", 10), bg=BG_FORM, fg=BROWN).pack(side="left")

    # Submit button
    submit_btn = tk.Button(left, text="Log In",
                            font=("Georgia", 13, "bold"),
                            bg=ORANGE, fg=WHITE,
                            activebackground=ORANGE_HOV, activeforeground=WHITE,
                            relief="flat", bd=0, cursor="hand2")
    submit_btn.place(x=60, y=276, width=340, height=44)
    submit_btn.bind("<Enter>", lambda e: submit_btn.configure(bg=ORANGE_HOV))
    submit_btn.bind("<Leave>", lambda e: submit_btn.configure(bg=ORANGE))

    # Forgot password
    forgot_lbl = tk.Label(left, text="Forgot password?",
                           font=("Georgia", 9, "italic"),
                           bg=BG_FORM, fg=GRAY_TEXT, cursor="hand2")
    forgot_lbl.place(x=280, y=332)

    # Right: About Us blurb 
    right = tk.Frame(f, bg=BG_CREAM)
    right.place(relx=0.46, y=20, relwidth=0.52, height=560)

    tk.Label(right, text="About us  ——",
             font=("Georgia", 10, "italic"),
             bg=BG_CREAM, fg=GREEN_MED).place(x=10, y=10)
    tk.Label(right,
             text="Brewing joy,\nserving flavor",
             font=("Georgia", 34, "bold"),
             bg=BG_CREAM, fg=BROWN,
             justify="left", wraplength=440).place(x=10, y=38)
    tk.Label(right,
             text=("Eating out at a restaurant of your choice is always an enjoyable\n"
                   "experience. Make it a memorable one by dining in with us in an\n"
                   "ambiance that boasts of a 20-year old history located in\n"
                   "Softwarica College."),
             font=("Georgia", 12),
             bg=BG_CREAM, fg=BROWN,
             justify="left", wraplength=440).place(x=10, y=170)

    # Closures for interactivity 

    def toggle_mode():
        if mode[0] == MODE_LOGIN:
            mode[0] = MODE_SIGNUP
            form_title.configure(text="Sign Up")
            submit_btn.configure(text="Sign Up")
            toggle_lbl.configure(text="Already have an account? Log In")
            name_frame.place(x=60, y=100, width=340, height=42)
            code_frame.place(x=60, y=154, width=340, height=42)  # NEW: Show reset code
            email_frame.place(x=60, y=208, width=340, height=42)
            pw_frame.place(x=60, y=262, width=340, height=42)
            show_pw_frame.place(x=60, y=310)
            rem_frame.place(x=60, y=334)
            submit_btn.place(x=60, y=362, width=340, height=44)
            forgot_lbl.place(x=280, y=416)
        else:
            mode[0] = MODE_LOGIN
            form_title.configure(text="Log In")
            submit_btn.configure(text="Log In")
            toggle_lbl.configure(text="Don't have an account? Sign Up")
            name_frame.place_forget()
            code_frame.place_forget()  # NEW: Hide reset code
            email_frame.place(x=60, y=100, width=340, height=42)
            pw_frame.place(x=60, y=154, width=340, height=42)
            show_pw_frame.place(x=60, y=202)
            rem_frame.place(x=60, y=228)
            submit_btn.place(x=60, y=276, width=340, height=44)
            forgot_lbl.place(x=280, y=332)
        # Reset password visibility
        show_pw_var.set(False)
        for e in (entry_name, entry_email, entry_pw, entry_code):  # NEW: Added entry_code
            e._active = False
            e.configure(show="")
            e.delete(0, tk.END)
            e._on_focus_out()

    def on_submit():
        email = entry_email.real_value().strip()
        pw    = entry_pw.real_value()
        if not email or not pw:
            messagebox.showwarning("Missing fields", "Please fill in all required fields.")
            return
        if mode[0] == MODE_SIGNUP:
            name = entry_name.real_value().strip()
            reset_code = entry_code.real_value().strip()
            
            if not name:
                messagebox.showwarning("Missing fields", "Please enter your name.")
                return
            
            # Validate reset code (must be exactly 6 digits)
            if not reset_code:
                messagebox.showwarning("Missing fields", "Please enter a 6-digit reset code.")
                return
            if len(reset_code) != 6 or not reset_code.isdigit():
                messagebox.showerror("Invalid Code", "Reset code must be exactly 6 digits.")
                return
            
            ok, msg = db_register(name, email, pw, reset_code)
            if ok:
                messagebox.showinfo("Success", msg + "\nYou can now log in.\n\nIMPORTANT: Remember your 6-digit code for password reset!")
                toggle_mode()
            else:
                messagebox.showerror("Registration failed", msg)
        else:
            ok, msg = db_login(email, pw)
            if ok:
                app["_login_email"]    = email
                app["_logged_in_user"] = msg
                
                # Centered Welcome popup 
                popup = tk.Toplevel(app["root"])
                popup.title("Welcome!")
                
                # Center the popup on screen
                popup_width = 400
                popup_height = 220
                screen_width = popup.winfo_screenwidth()
                screen_height = popup.winfo_screenheight()
                x = (screen_width - popup_width) // 2
                y = (screen_height - popup_height) // 2
                popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
                
                popup.resizable(False, False)
                popup.configure(bg=BG_CREAM)
                popup.grab_set()
                popup.focus()
                
                tk.Frame(popup, bg=ORANGE, height=6).pack(fill="x")
                tk.Label(popup,
                         text=f"Hello, {msg}! 👋",
                         font=("Georgia", 26, "bold"),
                         bg=BG_CREAM, fg=BROWN).pack(pady=(30, 8))
                tk.Label(popup,
                         text="Welcome back to CafeHub ☕",
                         font=("Georgia", 13, "italic"),
                         bg=BG_CREAM, fg=GREEN_MED).pack()
                
                def _close_and_go(p=popup):
                    p.destroy()
                    # Navigate to logged-in home page (dashboard)
                    app["navigate"]("dashboard", msg)
                
                tk.Button(popup, text="Let's Get Started!",
                          font=("Georgia", 12, "bold"),
                          bg=ORANGE, fg=WHITE,
                          activebackground=ORANGE_HOV, activeforeground=WHITE,
                          relief="flat", cursor="hand2",
                          padx=30, pady=10,
                          command=_close_and_go).pack(pady=(16, 0))
                
                popup.protocol("WM_DELETE_WINDOW", _close_and_go)
            else:
                messagebox.showerror("Login failed", msg)

    def forgot_password():
        win = tk.Toplevel(app["root"])
        win.title("Reset Password")
        
        # Center the window
        win_width = 420
        win_height = 340
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        win.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        win.configure(bg=BG_CREAM)
        win.resizable(False, False)
        win.grab_set()
        
        # Header
        tk.Frame(win, bg=ORANGE, height=4).pack(fill="x")
        tk.Label(win, text="🔐 Reset Password",
                 font=("Georgia", 16, "bold"),
                 bg=BG_CREAM, fg=BROWN).pack(pady=(20, 10))
        
        # Instructions
        tk.Label(win, text="Enter your email and 6-digit reset code",
                 font=("Georgia", 10),
                 bg=BG_CREAM, fg=GRAY_TEXT).pack()
        
        # Form frame
        form = tk.Frame(win, bg=BG_CREAM)
        form.pack(pady=20, padx=40, fill="x")
        
        # Email field
        tk.Label(form, text="Email:", font=("Georgia", 10, "bold"),
                 bg=BG_CREAM, fg=BROWN, anchor="w").pack(fill="x", pady=(5, 2))
        email_var = tk.StringVar()
        email_entry = tk.Entry(form, textvariable=email_var, 
                              font=("Georgia", 11),
                              relief="solid", bd=1)
        email_entry.pack(fill="x", ipady=4)
        
        # Reset code field
        tk.Label(form, text="6-Digit Reset Code:", font=("Georgia", 10, "bold"),
                 bg=BG_CREAM, fg=BROWN, anchor="w").pack(fill="x", pady=(15, 2))
        code_var = tk.StringVar()
        code_entry = tk.Entry(form, textvariable=code_var, 
                             font=("Georgia", 11),
                             relief="solid", bd=1, show="*")
        code_entry.pack(fill="x", ipady=4)
        
        # New password field (initially hidden)
        new_pw_label = tk.Label(form, text="New Password:", 
                               font=("Georgia", 10, "bold"),
                               bg=BG_CREAM, fg=BROWN, anchor="w")
        new_pw_var = tk.StringVar()
        new_pw_entry = tk.Entry(form, textvariable=new_pw_var, 
                               font=("Georgia", 11),
                               relief="solid", bd=1, show="•")
        
        # Confirm password field (initially hidden)
        confirm_pw_label = tk.Label(form, text="Confirm Password:", 
                                    font=("Georgia", 10, "bold"),
                                    bg=BG_CREAM, fg=BROWN, anchor="w")
        confirm_pw_var = tk.StringVar()
        confirm_pw_entry = tk.Entry(form, textvariable=confirm_pw_var, 
                                    font=("Georgia", 11),
                                    relief="solid", bd=1, show="•")
        
        button_frame = tk.Frame(win, bg=BG_CREAM)
        button_frame.pack(pady=10)
        
        def verify_code():
            email = email_var.get().strip()
            code = code_var.get().strip()
            
            if not email or not code:
                messagebox.showwarning("Missing Information", 
                                      "Please enter both email and reset code.")
                return
            
            if len(code) != 6 or not code.isdigit():
                messagebox.showerror("Invalid Code", 
                                    "Reset code must be exactly 6 digits.")
                return
            
            # Verify code
            if db_verify_reset_code(email, code):
                # Code is correct, show password reset fields
                email_entry.configure(state="disabled")
                code_entry.configure(state="disabled")
                
                new_pw_label.pack(fill="x", pady=(15, 2))
                new_pw_entry.pack(fill="x", ipady=4)
                confirm_pw_label.pack(fill="x", pady=(15, 2))
                confirm_pw_entry.pack(fill="x", ipady=4)
                
                verify_btn.pack_forget()
                update_btn.pack(side="left", padx=5)
                cancel_btn.configure(text="Cancel", 
                                   command=win.destroy)
                
                messagebox.showinfo("Verification Successful", 
                                   "Code verified! Now enter your new password.")
            else:
                messagebox.showerror("Verification Failed", 
                                    "Invalid email or reset code.\n\n" +
                                    "Make sure you entered the 6-digit code " +
                                    "you provided during registration.")
        
        def update_password():
            new_pw = new_pw_var.get()
            confirm_pw = confirm_pw_var.get()
            
            if not new_pw or not confirm_pw:
                messagebox.showwarning("Missing Password", 
                                      "Please enter and confirm your new password.")
                return
            
            if new_pw != confirm_pw:
                messagebox.showerror("Password Mismatch", 
                                    "Passwords do not match. Please try again.")
                new_pw_var.set("")
                confirm_pw_var.set("")
                return
            
            if len(new_pw) < 6:
                messagebox.showwarning("Weak Password", 
                                      "Password should be at least 6 characters long.")
                return
            
            # Update password in database
            email = email_var.get().strip()
            success, message = db_update_password(email, new_pw)
            
            if success:
                messagebox.showinfo("Success! ✅", 
                                   "Your password has been updated successfully!\n\n" +
                                   "You can now log in with your new password.")
                win.destroy()
            else:
                messagebox.showerror("Error", message)
        
        # Buttons
        verify_btn = tk.Button(button_frame, text="Verify Code",
                              font=("Georgia", 11, "bold"),
                              bg=ORANGE, fg=WHITE, 
                              relief="flat", cursor="hand2",
                              activebackground=ORANGE_HOV, 
                              padx=20, pady=8,
                              command=verify_code)
        verify_btn.pack(side="left", padx=5)
        
        update_btn = tk.Button(button_frame, text="Update Password",
                              font=("Georgia", 11, "bold"),
                              bg=GREEN_DARK, fg=WHITE, 
                              relief="flat", cursor="hand2",
                              activebackground=GREEN_MED, 
                              padx=20, pady=8,
                              command=update_password)
        
        cancel_btn = tk.Button(button_frame, text="Back",
                              font=("Georgia", 11),
                              bg=GRAY_LIGHT, fg=BROWN, 
                              relief="flat", cursor="hand2",
                              padx=20, pady=8,
                              command=win.destroy)
        cancel_btn.pack(side="left", padx=5)

    toggle_lbl.bind("<Button-1>", lambda e: toggle_mode())
    submit_btn.configure(command=on_submit)
    forgot_lbl.bind("<Button-1>", lambda e: forgot_password())

    return 