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
    """this function is for creating login.db and the users table."""
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
    """this function is for creating orders.db and the orders / order_items tables."""
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

    cards_container = tk.Frame(actions_frame, bg=BG_CREAM)
    cards_container.pack()

    for emoji, text, page_key, color in actions:
        card = tk.Frame(cards_container, bg=WHITE,
                        highlightbackground=GRAY_LIGHT,
                        highlightthickness=2,
                        cursor="hand2")
        card.pack(side="left", padx=15, pady=10)

        # Card content
        content = tk.Frame(card, bg=WHITE)
        content.pack(padx=30, pady=25)

        tk.Label(content, text=emoji,
                 font=("Arial", 48),
                 bg=WHITE).pack()
        tk.Label(content, text=text,
                 font=("Georgia", 14, "bold"),
                 bg=WHITE, fg=color).pack(pady=(10, 0))

        # Bind click event
        def make_click_handler(key):
            return lambda e: app["navigate"](key)

        card.bind("<Button-1>", make_click_handler(page_key))
        content.bind("<Button-1>", make_click_handler(page_key))
        for child in content.winfo_children():
            child.bind("<Button-1>", make_click_handler(page_key))

        # Hover effects
        def on_enter(e, c=card):
            c.configure(highlightbackground=color, highlightthickness=3)

        def on_leave(e, c=card):
            c.configure(highlightbackground=GRAY_LIGHT, highlightthickness=2)

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    # Bottom section with logout
    bottom = tk.Frame(f, bg=BG_CREAM)
    bottom.pack(side="bottom", pady=40)

    tk.Button(bottom, text="🚪  Log Out",
              font=("Georgia", 13, "bold"),
              bg=MENU_RED, fg=WHITE,
              activebackground="#6b1010", activeforeground=WHITE,
              relief="flat", cursor="hand2",
              padx=40, pady=12,
              command=lambda: logout(app)).pack()

    def logout(app):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            app["_logged_in_user"] = None
            app["_login_email"] = None
            app["navigate"]("home")

    def set_user(name: str):
        name_var.set(f"Hello, {name}! 👋")

    f.set_user = set_user
    return f
# Home page where : login and signup + About us is also includeed 🔒


def make_home_page(parent, app):
    MODE_LOGIN = "login"
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

    # Reset Code field (hidden in login mode)
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

    # Right: About Us
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

# Interactive

    def toggle_mode():
        if mode[0] == MODE_LOGIN:
            mode[0] = MODE_SIGNUP
            form_title.configure(text="Sign Up")
            submit_btn.configure(text="Sign Up")
            toggle_lbl.configure(text="Already have an account? Log In")
            name_frame.place(x=60, y=100, width=340, height=42)
            code_frame.place(x=60, y=154, width=340, height=42)
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
            code_frame.place_forget()
            email_frame.place(x=60, y=100, width=340, height=42)
            pw_frame.place(x=60, y=154, width=340, height=42)
            show_pw_frame.place(x=60, y=202)
            rem_frame.place(x=60, y=228)
            submit_btn.place(x=60, y=276, width=340, height=44)
            forgot_lbl.place(x=280, y=332)
        # Reset password visibility
        show_pw_var.set(False)
        for e in (entry_name, entry_email, entry_pw, entry_code):
            e._active = False
            e.configure(show="")
            e.delete(0, tk.END)
            e._on_focus_out()

    def on_submit():
        email = entry_email.real_value().strip()
        pw = entry_pw.real_value()

        if mode[0] == MODE_SIGNUP:
            name = entry_name.real_value().strip()
            reset_code = entry_code.real_value().strip()

            if not name:
                messagebox.showwarning(
                    "Missing fields", "Please enter your name.")
                return

            # Validate email
            email_valid, email_msg = validate_email(email)
            if not email_valid:
                messagebox.showerror("Invalid Email", email_msg)
                return

            # Validate password
            pw_valid, pw_msg = validate_password(pw)
            if not pw_valid:
                messagebox.showerror("Invalid Password", pw_msg)
                return

            # Validate reset code (must be exactly 6 digits)
            if not reset_code:
                messagebox.showwarning(
                    "Missing fields", "Please enter a 6-digit reset code.")
                return
            if len(reset_code) != 6 or not reset_code.isdigit():
                messagebox.showerror(
                    "Invalid Code", "Reset code must be exactly 6 digits.")
                return

            ok, msg = db_register(name, email, pw, reset_code)
            if ok:
                messagebox.showinfo("Success",
                                    msg + "\nYou can now log in.\n\n" +
                                    "IMPORTANT: Remember your 6-digit code for password reset!")
                toggle_mode()
            else:
                messagebox.showerror("Registration failed", msg)
        else:
            # Login mode
            if not email or not pw:
                messagebox.showwarning(
                    "Missing fields", "Please fill in all required fields.")
                return

            ok, msg = db_login(email, pw)
            if ok:
                app["_login_email"] = email
                app["_logged_in_user"] = msg

                # Welcome popup
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

        # New password field hidden at first
        new_pw_label = tk.Label(form, text="New Password:",
                                font=("Georgia", 10, "bold"),
                                bg=BG_CREAM, fg=BROWN, anchor="w")
        new_pw_var = tk.StringVar()
        new_pw_entry = tk.Entry(form, textvariable=new_pw_var,
                                font=("Georgia", 11),
                                relief="solid", bd=1, show="•")

        # Confirm password field hidden at first
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

            # Validate new password
            pw_valid, pw_msg = validate_password(new_pw)
            if not pw_valid:
                messagebox.showerror("Invalid Password", pw_msg)
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

    return f
 # Menu Page


def make_menu_page(parent, app):
    '''This is for the menu page here the menu
    is made'''
    f = tk.Frame(parent, bg=WHITE)
    cart = {}   # name -> {price, qty, emoji}
    img_cache = {}

    # Right panel:
    bag_panel = tk.Frame(f, bg=BAG_BG, width=260,
                         highlightbackground=GRAY_LIGHT, highlightthickness=1)
    bag_panel.pack(side="right", fill="y")
    bag_panel.pack_propagate(False)

    # Left: scrollable menu:
    left = tk.Frame(f, bg=WHITE)
    left.pack(side="left", fill="both", expand=True)

    canvas = tk.Canvas(left, bg=WHITE, highlightthickness=0)
    vsb = tk.Scrollbar(left, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    scroll_frame = tk.Frame(canvas, bg=WHITE)
    cwin = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    scroll_frame.bind("<Configure>",
                      lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(
        cwin, width=e.width))
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    # Bag widget refs stored in a dict for closure access
    bag_refs = {}

    def refresh_bag():
        for w in bag_refs["inner"].winfo_children():
            w.destroy()
        if not cart:
            tk.Label(bag_refs["inner"], text="Your bag is empty",
                     font=("Georgia", 10, "italic"),
                     bg=BAG_BG, fg=GRAY_TEXT).pack(pady=20)
            bag_refs["subtotal"].configure(text="NRS 0")
            return
        subtotal = 0
        for name, data in cart.items():
            qty, price = data["qty"], data["price"]
            line_total = qty * price
            subtotal += line_total
            short = (name[:22] + "…") if len(name) > 24 else name

            hdr = tk.Frame(bag_refs["inner"], bg=BAG_BG)
            hdr.pack(fill="x", padx=10, pady=(8, 0))
            tk.Label(hdr, text=f"{short}:", font=("Georgia", 9, "bold"),
                     bg=BAG_BG, fg=BROWN, anchor="w").pack(side="left")
            tk.Label(hdr, text=f"  {price}.00", font=("Georgia", 9, "bold"),
                     bg=BAG_BG, fg=GREEN_MED).pack(side="left")
            tk.Label(hdr, text=f"({qty} items)", font=("Georgia", 9),
                     bg=BAG_BG, fg=GRAY_TEXT).pack(side="left", padx=(4, 0))

            # More prominent remove button with hover effect
            rm_frame = tk.Frame(hdr, bg="#ffebee", cursor="hand2",
                                highlightbackground="#ef5350", highlightthickness=1)
            rm_frame.pack(side="right")
            rm = tk.Label(rm_frame, text="🗑️", font=("Segoe UI Emoji", 10),
                          bg="#ffebee", fg="#c62828", cursor="hand2", padx=4, pady=2)
            rm.pack()

            def remove_hover_in(e, f=rm_frame):
                f.configure(
                    bg="#ffcdd2", highlightbackground="#e53935", highlightthickness=2)

            def remove_hover_out(e, f=rm_frame):
                f.configure(
                    bg="#ffebee", highlightbackground="#ef5350", highlightthickness=1)

            rm_frame.bind("<Button-1>", lambda e, n=name: remove_item(n))
            rm.bind("<Button-1>", lambda e, n=name: remove_item(n))
            rm_frame.bind("<Enter>", remove_hover_in)
            rm_frame.bind("<Leave>", remove_hover_out)
            rm.bind("<Enter>", remove_hover_in)
            rm.bind("<Leave>", remove_hover_out)

            detail = tk.Frame(bag_refs["inner"], bg=BAG_BG)
            detail.pack(fill="x", padx=10, pady=(2, 4))
            tk.Label(detail, text=f"{qty}x", font=("Georgia", 9, "bold"),
                     bg=BAG_BG, fg=GRAY_TEXT, width=3, anchor="w").pack(side="left")
            tk.Label(detail, text=short, font=("Georgia", 9),
                     bg=BAG_BG, fg=BROWN, anchor="w").pack(side="left")
            tk.Label(detail, text=str(line_total), font=("Georgia", 9, "bold"),
                     bg=BAG_BG, fg=BROWN).pack(side="right")
            tk.Frame(bag_refs["inner"], bg=GRAY_LIGHT,
                     height=1).pack(fill="x", padx=8)

        bag_refs["subtotal"].configure(text=f"NRS {subtotal}")

    def remove_item(name):
        """CRUD Delete operation - Remove item from bag"""
        if name in cart:
            # Confirmation dialog before removing
            if messagebox.askyesno("Remove Item",
                                   f"Remove {name} from your bag?"):
                del cart[name]
                refresh_bag()

    #  Product popup
    def open_popup(item, category):
        popup = tk.Toplevel(app["root"])
        popup.title(item["name"])
        popup.geometry("720x420")
        popup.resizable(False, False)
        popup.configure(bg=WHITE)
        popup.grab_set()
        popup.focus()

        close_btn = tk.Label(popup, text="✕",
                             font=("Arial", 16, "bold"),
                             bg=WHITE, fg=GRAY_TEXT, cursor="hand2")
        close_btn.place(relx=1.0, y=10, anchor="ne", x=-14)
        close_btn.bind("<Button-1>", lambda e: popup.destroy())

        # Left: circular image
        left_p = tk.Frame(popup, bg=WHITE)
        left_p.place(x=30, y=30, width=300, height=360)
        pop_photo = load_img_wh(
            item["img"], 260, 260, circle=True, cache=img_cache)
        if pop_photo:
            pop_lbl = tk.Label(left_p, image=pop_photo, bg=WHITE)
            pop_lbl.image = pop_photo
            pop_lbl.pack(pady=(30, 0))
        else:
            cv = tk.Canvas(left_p, width=280, height=280,
                           bg=WHITE, bd=0, highlightthickness=0)
            cv.pack(pady=(30, 0))
            cv.create_oval(10, 10, 270, 270, fill="#f5ede0",
                           outline=GRAY_LIGHT, width=2)
            cv.create_text(140, 140, text=item["emoji"],
                           font=("Segoe UI Emoji", 90), fill=MENU_RED)

        # Right: details
        right_p = tk.Frame(popup, bg=WHITE)
        right_p.place(x=350, y=20, width=350, height=380)

        tk.Label(right_p, text=item["name"].upper(),
                 font=("Georgia", 18, "bold"),
                 bg=WHITE, fg=BROWN,
                 justify="left", wraplength=330, anchor="w").pack(anchor="w", pady=(10, 4))

        star_row = tk.Frame(right_p, bg=WHITE)
        star_row.pack(anchor="w")
        tk.Label(star_row, text="★★★★☆", font=("Arial", 13),
                 bg=WHITE, fg=STAR_CLR).pack(side="left")
        tk.Label(star_row, text="  (0 customer reviews)", font=("Georgia", 9),
                 bg=WHITE, fg=GRAY_TEXT).pack(side="left")

        tk.Label(right_p, text=f"NRS {item['price']}.00",
                 font=("Georgia", 20, "bold"),
                 bg=WHITE, fg=MENU_RED).pack(anchor="w", pady=(14, 0))
        tk.Frame(right_p, bg=GRAY_LIGHT, height=1).pack(fill="x", pady=10)
        tk.Label(right_p, text=item["desc"], font=("Georgia", 11),
                 bg=WHITE, fg=GRAY_TEXT,
                 justify="left", wraplength=330, anchor="w").pack(anchor="w", pady=(0, 16))

        ctrl = tk.Frame(right_p, bg=WHITE)
        ctrl.pack(anchor="w", pady=(0, 12))
        qty_var = tk.IntVar(value=1)

        qty_box = tk.Frame(ctrl, bg=WHITE,
                           highlightbackground=MENU_RED, highlightthickness=1)
        qty_box.pack(side="left", padx=(0, 12))
        tk.Button(qty_box, text="−", font=("Georgia", 14, "bold"),
                  bg=WHITE, fg=MENU_RED, relief="flat", bd=0, cursor="hand2", width=2,
                  command=lambda: qty_var.set(max(1, qty_var.get() - 1))).pack(side="left", padx=4, pady=4)
        tk.Label(qty_box, textvariable=qty_var, font=("Georgia", 13, "bold"),
                 bg=WHITE, fg=BROWN, width=3).pack(side="left")
        tk.Button(qty_box, text="+", font=("Georgia", 14, "bold"),
                  bg=WHITE, fg=MENU_RED, relief="flat", bd=0, cursor="hand2", width=2,
                  command=lambda: qty_var.set(qty_var.get() + 1)).pack(side="left", padx=4, pady=4)

        def add_to_cart():
            qty = qty_var.get()
            name = item["name"]
            if name in cart:
                cart[name]["qty"] += qty
            else:
                cart[name] = {"price": item["price"],
                              "qty": qty, "emoji": item["emoji"]}
            refresh_bag()
            popup.destroy()
            messagebox.showinfo(
                "Added to Bag ✅", f"{qty}x {name} added to your bag!")

        tk.Button(ctrl, text="ADD TO CART",
                  font=("Georgia", 11, "bold"),
                  bg=MENU_RED, fg=WHITE,
                  activebackground="#6b1010", activeforeground=WHITE,
                  relief="flat", bd=0, cursor="hand2",
                  padx=20, pady=10,
                  command=add_to_cart).pack(side="left")

        meta = tk.Frame(right_p, bg=WHITE)
        meta.pack(anchor="w", pady=(4, 0))
        tk.Label(meta, text=f"SKU:  {item['sku']}",
                 font=("Georgia", 9), bg=WHITE, fg=GRAY_TEXT).pack(anchor="w")
        tk.Label(meta, text=f"Category:  {category}",
                 font=("Georgia", 9), bg=WHITE, fg=GRAY_TEXT).pack(anchor="w")

    # Build for the item card
    def make_item_card(par, item, category):
        card = tk.Frame(par, bg=WHITE)
        card.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=6)
        row = tk.Frame(card, bg=WHITE)
        row.pack(fill="x")

        IMG_SZ = 80
        photo = load_img_wh(item["img"], IMG_SZ, IMG_SZ,
                            circle=True, cache=img_cache)
        if photo:
            img_lbl = tk.Label(row, image=photo, bg=WHITE,
                               width=IMG_SZ, height=IMG_SZ)
            img_lbl.image = photo
            img_lbl.pack(side="left", padx=(0, 10))
        else:
            cv = tk.Canvas(row, width=IMG_SZ, height=IMG_SZ,
                           bg=WHITE, bd=0, highlightthickness=0)
            cv.pack(side="left", padx=(0, 10))
            cv.create_oval(2, 2, IMG_SZ - 2, IMG_SZ -
                           2, fill=MENU_RED, outline="")
            cv.create_text(IMG_SZ // 2, IMG_SZ // 2, text=item["emoji"],
                           font=("Segoe UI Emoji", 26), fill=WHITE)

        info = tk.Frame(row, bg=WHITE)
        info.pack(side="left", fill="both", expand=True)
        tk.Label(info, text=item["name"], font=("Georgia", 11, "bold"),
                 bg=WHITE, fg=BROWN, anchor="w", wraplength=200).pack(anchor="w")
        tk.Label(info, text=item["short"], font=("Georgia", 9),
                 bg=WHITE, fg=GRAY_TEXT, anchor="w").pack(anchor="w")
        tk.Label(info, text="★", font=("Arial", 11),
                 bg=WHITE, fg=STAR_CLR).pack(anchor="w")

        right_col = tk.Frame(row, bg=WHITE)
        right_col.pack(side="right", padx=(8, 0))
        price_box = tk.Frame(right_col, bg=WHITE,
                             highlightbackground=MENU_RED, highlightthickness=1)
        price_box.pack(anchor="e")
        tk.Label(price_box, text=f"NRs.{item['price']}.00",
                 font=("Georgia", 10, "bold"),
                 bg=WHITE, fg=MENU_RED, padx=6, pady=2).pack()

        cart_cv = tk.Canvas(right_col, width=34, height=34,
                            bg=WHITE, bd=0, highlightthickness=0, cursor="hand2")
        cart_cv.pack(anchor="e", pady=(6, 0))
        cart_cv.create_oval(1, 1, 33, 33, fill=MENU_RED, outline="")
        cart_cv.create_text(17, 17, text="🛒", font=(
            "Segoe UI Emoji", 13), fill=WHITE)
        cart_cv.bind("<Button-1>",
                     lambda e, it=item, cat=category: open_popup(it, cat))

        tk.Frame(card, bg=GRAY_LIGHT, height=1).pack(fill="x", pady=(8, 0))

    # Populate categories
    for cat_name, items in MENU_DATA:
        hdr = tk.Frame(scroll_frame, bg=WHITE)
        hdr.pack(fill="x", padx=24, pady=(22, 6))
        tk.Label(hdr, text=cat_name, font=("Georgia", 16, "bold"),
                 bg=WHITE, fg=MENU_RED).pack(anchor="w")
        tk.Frame(hdr, bg=GRAY_LIGHT, height=1).pack(fill="x", pady=(4, 0))
        row_frame = None
        for i, item in enumerate(items):
            if i % 2 == 0:
                row_frame = tk.Frame(scroll_frame, bg=WHITE)
                row_frame.pack(fill="x", padx=24, pady=2)
            make_item_card(row_frame, item, cat_name)

    # Build My Bag panel widgets
    tk.Label(bag_panel, text="MY BAG", font=("Georgia", 13, "bold"),
             bg=BAG_BG, fg=BROWN).pack(anchor="w", padx=16, pady=(16, 8))
    tk.Frame(bag_panel, bg=GRAY_LIGHT, height=1).pack(fill="x", padx=8)

    bag_canvas = tk.Canvas(bag_panel, bg=BAG_BG, highlightthickness=0)
    bag_vsb = tk.Scrollbar(bag_panel, orient="vertical",
                           command=bag_canvas.yview)
    bag_canvas.configure(yscrollcommand=bag_vsb.set)
    bag_vsb.pack(side="right", fill="y")
    bag_canvas.pack(fill="both", expand=True)

    bag_inner = tk.Frame(bag_canvas, bg=BAG_BG)
    bag_win = bag_canvas.create_window((0, 0), window=bag_inner, anchor="nw")
    bag_inner.bind("<Configure>",
                   lambda e: bag_canvas.configure(scrollregion=bag_canvas.bbox("all")))
    bag_canvas.bind("<Configure>",
                    lambda e: bag_canvas.itemconfig(bag_win, width=e.width))
    tk.Label(bag_inner, text="Your bag is empty",
             font=("Georgia", 10, "italic"),
             bg=BAG_BG, fg=GRAY_TEXT).pack(pady=20)

    sub_frame = tk.Frame(bag_panel, bg=BAG_BG)
    sub_frame.pack(fill="x", side="bottom")
    tk.Frame(sub_frame, bg=GRAY_LIGHT, height=1).pack(fill="x")
    sub_row = tk.Frame(sub_frame, bg=BAG_BG)
    sub_row.pack(fill="x", padx=14, pady=6)
    tk.Label(sub_row, text="SUB TOTAL", font=("Georgia", 10, "bold"),
             bg=BAG_BG, fg=BROWN).pack(side="left")
    subtotal_lbl = tk.Label(sub_row, text="NRS 0", font=("Georgia", 10, "bold"),
                            bg=BAG_BG, fg=MENU_RED)
    subtotal_lbl.pack(side="right")

    bag_refs["inner"] = bag_inner
    bag_refs["subtotal"] = subtotal_lbl

    # Checkout with option for editable order
    def on_checkout():
        if not cart:
            messagebox.showwarning(
                "Empty Bag", "Please add items to your bag first!")
            return
        if not app["is_logged_in"]():
            messagebox.showinfo("Login Required",
                                "You need to be logged in to proceed to checkout.\n"
                                "Redirecting you to the login page…")
            app["navigate"]("home")
            return

        # Show editable order confirmation popup
        show_order_confirmation()

    def show_order_confirmation():
        """
        CRUD Update/Delete operation popup
        - Display popup with all items and editable quantities (+/- buttons)
        - Items with quantity 0 are automatically removed
        - Shows live total calculations
        """
        popup = tk.Toplevel(app["root"])
        popup.title("🛒 Confirm Your Order")
        popup.geometry("600x700")
        popup.resizable(False, False)
        popup.configure(bg=WHITE)
        popup.grab_set()
        popup.focus()

        # Header
        hdr = tk.Frame(popup, bg=MENU_RED)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🛒  CONFIRM YOUR ORDER",
                 font=("Georgia", 16, "bold"),
                 bg=MENU_RED, fg=WHITE, pady=14).pack()

        # Scrollable items area
        items_frame = tk.Frame(popup, bg=WHITE)
        items_frame.pack(fill="both", expand=True, padx=20, pady=10)

        items_canvas = tk.Canvas(items_frame, bg=WHITE, highlightthickness=0)
        items_vsb = tk.Scrollbar(
            items_frame, orient="vertical", command=items_canvas.yview)
        items_canvas.configure(yscrollcommand=items_vsb.set)
        items_vsb.pack(side="right", fill="y")
        items_canvas.pack(side="left", fill="both", expand=True)

        items_inner = tk.Frame(items_canvas, bg=WHITE)
        items_canvas.create_window(
            (0, 0), window=items_inner, anchor="nw", width=550)
        items_inner.bind("<Configure>",
                         lambda e: items_canvas.configure(scrollregion=items_canvas.bbox("all")))

        # Track quantity variables for each item
        qty_vars = {}
        item_frames = {}

        def update_totals():
            """Recalculate and update totals"""
            subtotal = 0
            for name, var in qty_vars.items():
                qty = var.get()
                if qty > 0 and name in cart:
                    subtotal += qty * cart[name]["price"]

            vat = round(subtotal * 0.13, 2)
            service_tax = round(subtotal * 0.10, 2)
            grand = round(subtotal + vat + service_tax, 2)

            subtotal_lbl.configure(text=f"NRS {subtotal:.2f}")
            vat_lbl.configure(text=f"NRS {vat:.2f}")
            service_lbl.configure(text=f"NRS {service_tax:.2f}")
            grand_lbl.configure(text=f"NRS {grand:.2f}")

        def change_qty(name, delta):
            """
            CRUD Update operation - Change quantity
            CRUD Delete operation - When quantity reaches 0, item is removed
            """
            var = qty_vars[name]
            new_qty = max(0, var.get() + delta)
            var.set(new_qty)

            # If quantity becomes 0, remove from cart and hide row
            if new_qty == 0:
                if name in cart:
                    del cart[name]
                item_frames[name].pack_forget()

                # If all items removed, show empty message
                if not any(v.get() > 0 for v in qty_vars.values()):
                    tk.Label(items_inner, text="All items removed! 🛒",
                             font=("Georgia", 12, "italic"),
                             bg=WHITE, fg=GRAY_TEXT).pack(pady=30)
            else:
                # Update cart quantity
                if name in cart:
                    cart[name]["qty"] = new_qty

            update_totals()

        # Display each cart item
        for name, data in cart.items():
            qty_var = tk.IntVar(value=data["qty"])
            qty_vars[name] = qty_var

            item_row = tk.Frame(items_inner, bg=WHITE)
            item_row.pack(fill="x", pady=8, padx=5)
            item_frames[name] = item_row

            # Item name and price
            left_col = tk.Frame(item_row, bg=WHITE)
            left_col.pack(side="left", fill="x", expand=True)

            short_name = (name[:30] + "…") if len(name) > 32 else name
            tk.Label(left_col, text=short_name,
                     font=("Georgia", 11, "bold"),
                     bg=WHITE, fg=BROWN, anchor="w").pack(anchor="w")
            tk.Label(left_col, text=f"NRS {data['price']}.00 each",
                     font=("Georgia", 9),
                     bg=WHITE, fg=GRAY_TEXT, anchor="w").pack(anchor="w")

            # Quantity controls with +/- buttons
            right_col = tk.Frame(item_row, bg=WHITE)
            right_col.pack(side="right")

            qty_frame = tk.Frame(right_col, bg=WHITE,
                                 highlightbackground=MENU_RED, highlightthickness=1)
            qty_frame.pack(side="right")

            tk.Button(qty_frame, text="−", font=("Georgia", 12, "bold"),
                      bg=WHITE, fg=MENU_RED, relief="flat", bd=0,
                      cursor="hand2", width=2,
                      command=lambda n=name: change_qty(n, -1)).pack(side="left", padx=3, pady=3)

            tk.Label(qty_frame, textvariable=qty_var,
                     font=("Georgia", 11, "bold"),
                     bg=WHITE, fg=BROWN, width=3).pack(side="left")

            tk.Button(qty_frame, text="+", font=("Georgia", 12, "bold"),
                      bg=WHITE, fg=MENU_RED, relief="flat", bd=0,
                      cursor="hand2", width=2,
                      command=lambda n=name: change_qty(n, 1)).pack(side="left", padx=3, pady=3)

            # Line total
            line_total = data["qty"] * data["price"]
            tk.Label(right_col, text=f"NRS {line_total:.2f}",
                     font=("Georgia", 10, "bold"),
                     bg=WHITE, fg=MENU_RED).pack(side="right", padx=(0, 10))

            # Separator
            tk.Frame(items_inner, bg=GRAY_LIGHT,
                     height=1).pack(fill="x", pady=2)

        # Totals section
        totals_frame = tk.Frame(popup, bg=WHITE)
        totals_frame.pack(fill="x", padx=20, pady=10)

        tk.Frame(totals_frame, bg=MENU_RED, height=2).pack(fill="x", pady=5)

        subtotal = sum(d["qty"] * d["price"] for d in cart.values())
        vat = round(subtotal * 0.13, 2)
        service_tax = round(subtotal * 0.10, 2)
        grand_total = round(subtotal + vat + service_tax, 2)

        def total_row(label, initial_value):
            r = tk.Frame(totals_frame, bg=WHITE)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label, font=("Georgia", 11),
                     bg=WHITE, fg=BROWN, anchor="w").pack(side="left")
            lbl = tk.Label(r, text=f"NRS {initial_value:.2f}",
                           font=("Georgia", 11, "bold"),
                           bg=WHITE, fg=BROWN, anchor="e")
            lbl.pack(side="right")
            return lbl

        subtotal_lbl = total_row("Subtotal:", subtotal)
        vat_lbl = total_row("VAT (13%):", vat)
        service_lbl = total_row("Service Charge (10%):", service_tax)

        tk.Frame(totals_frame, bg=MENU_RED, height=2).pack(fill="x", pady=5)

        grand_row = tk.Frame(totals_frame, bg=WHITE)
        grand_row.pack(fill="x", pady=5)
        tk.Label(grand_row, text="GRAND TOTAL:", font=("Georgia", 13, "bold"),
                 bg=WHITE, fg=MENU_RED, anchor="w").pack(side="left")
        grand_lbl = tk.Label(grand_row, text=f"NRS {grand_total:.2f}",
                             font=("Georgia", 13, "bold"),
                             bg=WHITE, fg=MENU_RED, anchor="e")
        grand_lbl.pack(side="right")

        # Buttons
        btn_frame = tk.Frame(popup, bg=WHITE)
        btn_frame.pack(pady=15)

        def proceed_to_pay():
            # Check if cart is empty
            if not cart or not any(v.get() > 0 for v in qty_vars.values()):
                messagebox.showwarning("Empty Order",
                                       "Your order is empty! Please add items to proceed.")
                popup.destroy()
                return

            # Update cart with final quantities
            for name in list(cart.keys()):
                if name in qty_vars:
                    final_qty = qty_vars[name].get()
                    if final_qty > 0:
                        cart[name]["qty"] = final_qty
                    else:
                        del cart[name]

            popup.destroy()
            finalize_order()

        def finalize_order():
            """Save order to database and show receipt"""
            user_email = app.get("_login_email") or app["_logged_in_user"]
            order_id = db_save_order(user_email, cart)

            subtotal = sum(d["qty"] * d["price"] for d in cart.values())
            vat = round(subtotal * 0.13, 2)
            service_tax = round(subtotal * 0.10, 2)
            grand_total = round(subtotal + vat + service_tax, 2)

            show_receipt(order_id, subtotal, vat, service_tax, grand_total)
            cart.clear()
            refresh_bag()

        tk.Button(btn_frame, text="✅  Proceed to Pay",
                  font=("Georgia", 12, "bold"),
                  bg=GREEN_DARK, fg=WHITE,
                  activebackground=GREEN_MED, activeforeground=WHITE,
                  relief="flat", cursor="hand2",
                  padx=30, pady=12,
                  command=proceed_to_pay).pack(side="left", padx=10)

        tk.Button(btn_frame, text="Cancel",
                  font=("Georgia", 11),
                  bg=GRAY_LIGHT, fg=BROWN,
                  relief="flat", cursor="hand2",
                  padx=30, pady=12,
                  command=popup.destroy).pack(side="left", padx=10)

    def show_receipt(order_id, subtotal, vat, service_tax, grand_total):
        """Display final receipt after payment"""
        win = tk.Toplevel(app["root"])
        win.title("🧾 Order Receipt")
        win.geometry("480x560")
        win.resizable(False, False)
        win.configure(bg=WHITE)
        win.grab_set()

        hdr = tk.Frame(win, bg=MENU_RED)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🧾  ORDER RECEIPT",
                 font=("Georgia", 16, "bold"),
                 bg=MENU_RED, fg=WHITE, pady=14).pack()

        body = tk.Frame(win, bg=WHITE)
        body.pack(fill="both", expand=True, padx=30, pady=16)

        now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")
        tk.Label(body, text=f"Order #:   {order_id}",
                 font=("Georgia", 10), bg=WHITE, fg=GRAY_TEXT, anchor="w").pack(anchor="w")
        tk.Label(body, text=f"Customer:  {app['_logged_in_user']}",
                 font=("Georgia", 10), bg=WHITE, fg=GRAY_TEXT, anchor="w").pack(anchor="w")
        tk.Label(body, text=f"Date:      {now}",
                 font=("Georgia", 10), bg=WHITE, fg=GRAY_TEXT, anchor="w").pack(anchor="w", pady=(0, 10))
        tk.Frame(body, bg=GRAY_LIGHT, height=1).pack(fill="x", pady=4)

        col_hdr = tk.Frame(body, bg=WHITE)
        col_hdr.pack(fill="x", pady=(4, 2))
        tk.Label(col_hdr, text="Item",  font=("Georgia", 10, "bold"),
                 bg=WHITE, fg=BROWN, anchor="w", width=24).pack(side="left")
        tk.Label(col_hdr, text="Qty",   font=("Georgia", 10, "bold"),
                 bg=WHITE, fg=BROWN, width=5).pack(side="left")
        tk.Label(col_hdr, text="Price", font=("Georgia", 10, "bold"),
                 bg=WHITE, fg=BROWN, width=8).pack(side="left")
        tk.Label(col_hdr, text="Total", font=("Georgia", 10, "bold"),
                 bg=WHITE, fg=BROWN, anchor="e").pack(side="right")
        tk.Frame(body, bg=GRAY_LIGHT, height=1).pack(fill="x")

        # Re-read from orders.db
        conn = sqlite3.connect(ORDERS_DB)
        rows = conn.execute(
            "SELECT item_name, qty, unit_price, line_total FROM order_items WHERE order_id=?",
            (order_id,)).fetchall()
        conn.close()

        for item_name, qty, unit_price, line_total in rows:
            row = tk.Frame(body, bg=WHITE)
            row.pack(fill="x", pady=1)
            short = (item_name[:20] +
                     "…") if len(item_name) > 22 else item_name
            tk.Label(row, text=short, font=("Georgia", 10),
                     bg=WHITE, fg=BROWN, anchor="w", width=24).pack(side="left")
            tk.Label(row, text=str(qty), font=("Georgia", 10),
                     bg=WHITE, fg=GRAY_TEXT, width=5).pack(side="left")
            tk.Label(row, text=f"NRS {int(unit_price)}", font=("Georgia", 10),
                     bg=WHITE, fg=GRAY_TEXT, width=8).pack(side="left")
            tk.Label(row, text=f"NRS {int(line_total)}", font=("Georgia", 10, "bold"),
                     bg=WHITE, fg=BROWN, anchor="e").pack(side="right")

        tk.Frame(body, bg=GRAY_LIGHT, height=1).pack(fill="x", pady=8)

        def total_row(label, amount, bold=False, color=BROWN):
            r = tk.Frame(body, bg=WHITE)
            r.pack(fill="x", pady=1)
            fnt = ("Georgia", 11, "bold") if bold else ("Georgia", 10)
            tk.Label(r, text=label, font=fnt, bg=WHITE,
                     fg=color, anchor="w").pack(side="left")
            tk.Label(r, text=f"NRS {amount:.2f}", font=fnt,
                     bg=WHITE, fg=color, anchor="e").pack(side="right")

        total_row("Subtotal", subtotal)
        total_row("VAT (13 %)", vat)
        total_row("Service Charge (10 %)", service_tax)
        tk.Frame(body, bg=MENU_RED, height=2).pack(fill="x", pady=6)
        total_row("GRAND TOTAL", grand_total, bold=True, color=MENU_RED)

        tk.Label(win, text="Thank you for dining with CafeHub! ☕",
                 font=("Georgia", 10, "italic"), bg=WHITE, fg=GREEN_MED).pack(pady=(0, 6))
        tk.Button(win, text="Close", font=("Georgia", 11, "bold"),
                  bg=MENU_RED, fg=WHITE, relief="flat",
                  cursor="hand2", padx=24, pady=8,
                  command=win.destroy).pack(pady=(0, 16))

    tk.Button(sub_frame, text="PROCEED TO CHECKOUT",
              font=("Georgia", 10, "bold"),
              bg=MENU_RED, fg=WHITE,
              activebackground="#6b1010", activeforeground=WHITE,
              relief="flat", bd=0, cursor="hand2", pady=12,
              command=on_checkout).pack(fill="x", padx=14, pady=(4, 14))

    # Store reference to image cache to prevent GC
    f._img_cache = img_cache

    # Expose cart and refresh for SpecialPage add-to-bag
    f._cart = cart
    f._refresh_bag = refresh_bag
    return f

# specail page


def make_special_page(parent, app):
    f = tk.Frame(parent, bg=WHITE)

    selected = [0]
    img_cache = {}
    thumb_lbls = []

    # Top section
    top = tk.Frame(f, bg=WHITE)
    top.pack(fill="both", expand=True)

    info_frame = tk.Frame(top, bg=WHITE)
    info_frame.place(x=50, rely=0.1, width=500, relheight=0.8)

    hero_lbl = tk.Label(top, bg=WHITE)
    hero_lbl.place(relx=1.0, x=-30, y=10, anchor="ne")

    tk.Frame(f, bg=GRAY_LIGHT, height=1).pack(fill="x", padx=40)

    # Thumbnail strip
    thumb_strip = tk.Frame(f, bg=WHITE)
    thumb_strip.pack(fill="x", padx=40, pady=20)

    # Qty + bag bar
    bag_bar = tk.Frame(f, bg=WHITE)
    bag_bar.pack(pady=(0, 24))
    qty_var = tk.IntVar(value=1)

    def select(idx):
        selected[0] = idx
        item = SPECIAL_ITEMS[idx]

        for w in info_frame.winfo_children():
            w.destroy()

        tk.Label(info_frame, text=item["name"],
                 font=("PixelPurl", 36, "bold"),
                 bg=WHITE, fg=SPEC_RED, anchor="w").place(relx=0, rely=0.28, anchor="sw")
        tk.Label(info_frame, text=f"Rs.{item['price']}",
                 font=("PixelPurl", 30, "bold"),
                 bg=WHITE, fg=SPEC_RED, anchor="w").place(relx=0, rely=0.44, anchor="sw")
        tk.Label(info_frame, text=item["desc"],
                 font=("Georgia", 13),
                 bg=WHITE, fg=GRAY_TEXT,
                 justify="left", wraplength=440, anchor="nw").place(relx=0, rely=0.48, anchor="nw")

        ph = load_img_wh(item["img"], 420, 390, cache=img_cache)
        if ph:
            hero_lbl.configure(image=ph, text="")
            hero_lbl.image = ph
        else:
            hero_lbl.configure(image="", text=item["emoji"],
                               font=("Segoe UI Emoji", 100), bg=WHITE)

        for i, border in enumerate(thumb_lbls):
            border.configure(
                highlightbackground=SPEC_RED if i == idx else GRAY_LIGHT,
                highlightthickness=3 if i == idx else 2)

        qty_var.set(1)

    # Build thumbnails
    for i, item in enumerate(SPECIAL_ITEMS):
        holder = tk.Frame(thumb_strip, bg=WHITE, cursor="hand2")
        holder.pack(side="left", padx=16)
        border = tk.Frame(holder, bg=WHITE,
                          highlightbackground=GRAY_LIGHT, highlightthickness=2)
        border.pack()

        ph = load_img_wh(item["img"], 110, 90, cache=img_cache)
        if ph:
            lbl = tk.Label(border, image=ph, bg=WHITE, cursor="hand2")
            lbl.image = ph
        else:
            lbl = tk.Label(border, text=item["emoji"],
                           font=("Segoe UI Emoji", 36),
                           bg=WHITE, cursor="hand2", width=5, height=2)
        lbl.pack(padx=4, pady=4)
        lbl.bind("<Button-1>", lambda e, idx=i: select(idx))
        border.bind("<Button-1>", lambda e, idx=i: select(idx))
        thumb_lbls.append(border)

    def add_to_bag():
        item = SPECIAL_ITEMS[selected[0]]
        qty = qty_var.get()
        name = item["name"]
        menu_page = app["pages"].get("menu")
        if menu_page is None:
            messagebox.showwarning("Error", "Menu page not available.")
            return
        if name in menu_page._cart:
            menu_page._cart[name]["qty"] += qty
        else:
            menu_page._cart[name] = {
                "price": item["price"], "qty": qty, "emoji": item["emoji"]}
        menu_page._refresh_bag()
        messagebox.showinfo(
            "Added to Bag ✅", f"{qty}x {name} added to your bag!")

    # ADD TO BAG button
    tk.Button(bag_bar, text="➕  ADD TO BAG",
              font=("Georgia", 12, "bold"),
              bg=SPEC_RED, fg=WHITE,
              activebackground="#6b1010", activeforeground=WHITE,
              relief="flat", bd=0, cursor="hand2",
              padx=28, pady=10,
              command=add_to_bag).pack(side="left", padx=(0, 16))

    # Qty control
    qty_box = tk.Frame(bag_bar, bg=WHITE,
                       highlightbackground=SPEC_RED, highlightthickness=1)
    qty_box.pack(side="left")
    tk.Button(qty_box, text="−", font=("Georgia", 13, "bold"),
              bg=WHITE, fg=SPEC_RED, relief="flat", bd=0, cursor="hand2", width=2,
              command=lambda: qty_var.set(max(1, qty_var.get() - 1))).pack(side="left", padx=4, pady=4)
    tk.Label(qty_box, textvariable=qty_var, font=("Georgia", 12, "bold"),
             bg=WHITE, fg=BROWN, width=3).pack(side="left")
    tk.Button(qty_box, text="+", font=("Georgia", 13, "bold"),
              bg=WHITE, fg=SPEC_RED, relief="flat", bd=0, cursor="hand2", width=2,
              command=lambda: qty_var.set(qty_var.get() + 1)).pack(side="left", padx=4, pady=4)

    # Store image cache
    f._img_cache = img_cache

    select(0)
    return f

# Main App build starts from here!


def build_header(root, logo_img, plate_img):
    header = tk.Frame(root, bg=BG_CREAM, height=140)
    header.pack(fill="x")
    header.pack_propagate(False)

    left = tk.Frame(header, bg=BG_CREAM)
    left.place(x=24, y=14)
    tk.Label(left, text="Healthy & Tasty Food  ——",
             font=("Georgia", 10, "italic"), bg=BG_CREAM, fg=GREEN_MED).pack(anchor="w")
    tk.Label(left, text="Where Tasty Bites\nMeet Happy Moments.",
             font=("Georgia", 28, "bold"),
             bg=BG_CREAM, fg=BROWN, justify="left").pack(anchor="w", pady=(2, 0))

    center = tk.Frame(header, bg=BG_CREAM)
    center.place(relx=0.5, rely=0.5, anchor="center")
    if logo_img:
        tk.Label(center, image=logo_img, bg=BG_CREAM).pack()
    else:
        tk.Label(center, text="☕  cafe\nhub",
                 font=("Georgia", 20, "bold"),
                 bg=BG_CREAM, fg=BROWN, justify="center").pack()

    if plate_img:
        tk.Label(header, image=plate_img, bg=BG_CREAM).place(
            relx=1.0, rely=0, anchor="ne", x=-10, y=0)
    else:
        tk.Label(header, text="🥗", font=("Arial", 60), bg=BG_CREAM).place(
            relx=1.0, rely=0.1, anchor="ne", x=-20)


def build_navbar(root, app):
    nav_frame = tk.Frame(root, bg=BG_CREAM)
    nav_frame.pack(fill="x")
    tk.Frame(nav_frame, bg=GRAY_LIGHT, height=1).pack(fill="x")

    inner = tk.Frame(nav_frame, bg=BG_CREAM)
    inner.pack(anchor="center", pady=4)

    for text, key in [("Home", "home"), ("Menu", "menu"), ("About", "about"),
                      ("Contact", "contact"), ("Special", "special")]:
        lbl = tk.Label(inner, text=text,
                       font=("Georgia", 12),
                       bg=BG_CREAM, fg=BROWN, cursor="hand2",
                       padx=14, pady=4)
        lbl.pack(side="left")
        lbl.bind("<Button-1>", lambda e, k=key: app["navigate"](k))
        lbl.bind("<Enter>", lambda e, l=lbl: l.configure(fg=GREEN_DARK))
        lbl.bind("<Leave>", lambda e, l=lbl, k=key: (
            l.configure(fg=GREEN_DARK, font=("Georgia", 12, "underline"))
            if app["_current_page"] == k
            else l.configure(fg=BROWN, font=("Georgia", 12))
        ))
        app["_nav_labels"][key] = lbl

    tk.Frame(nav_frame, bg=GRAY_LIGHT, height=1).pack(fill="x")


def set_active_nav(app, key):
    for k, lbl in app["_nav_labels"].items():
        if k == key:
            lbl.configure(fg=GREEN_DARK, font=("Georgia", 12, "underline"))
        else:
            lbl.configure(fg=BROWN, font=("Georgia", 12))


def run_app():
    # DB initalization
    init_login_db()
    init_orders_db()

    # Print startup info
    if DEBUG_IMAGES:
        print("\n" + "="*60)
        print("  CAFEHUB APPLICATION STARTING")
        print("="*60)
        print(f" Working directory: {BASE_DIR}")
        print(f" Debug mode: {DEBUG_IMAGES}")
        print("="*60 + "\n")

    root = tk.Tk()
    root.title("CafeHub – Where Tasty Bites Meet Happy Moments")
    iconpath = asset('cafehub.ico')
    root.iconbitmap(iconpath)
    root.resizable(True, True)
    root.minsize(900, 600)
    root.state("zoomed")
    root.configure(bg=BG_CREAM)

    app = {
        "root":             root,
        "_logged_in_user":  None,
        "_login_email":     None,
        "_current_page":    None,
        "pages":            {},
        "_nav_labels":      {},
    }

    def navigate(key: str, user_name: str = ""):
        # If user clicks "home" and is logged in, go to dashboard
        if key == "home" and app["_logged_in_user"]:
            key = "dashboard"

        if key == "dashboard":
            if user_name:
                app["_logged_in_user"] = user_name
                if not app["_login_email"]:
                    app["_login_email"] = user_name
                app["pages"]["dashboard"].set_user(user_name)
            elif app["_logged_in_user"]:
                # Refresh with current user
                app["pages"]["dashboard"].set_user(app["_logged_in_user"])

        # Reset user session when going to actual home (logged out)
        if key == "home" and not app["_logged_in_user"]:
            app["_login_email"] = None

        # Show/hide pages
        for k, p in app["pages"].items():
            if k == key:
                p.lift()
            else:
                p.lower()

        app["_current_page"] = key

        # Update navbar - show "home" as active when on dashboard
        nav_key = "home" if key == "dashboard" else key
        if nav_key in app["_nav_labels"]:
            set_active_nav(app, nav_key)

    def is_logged_in():
        return app["_logged_in_user"] is not None

    app["navigate"] = navigate
    app["is_logged_in"] = is_logged_in

    # Load the assets
    logo_img = plate_img = None
    logo_path = asset("cafehub.png")
    plate_path = asset("plate.jpg")

    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert(
                "RGBA").resize((220, 220), Image.LANCZOS)
            logo_img = ImageTk.PhotoImage(logo)
            if DEBUG_IMAGES:
                print("✓ Loaded header logo: cafehub.png")
        except Exception as e:
            if DEBUG_IMAGES:
                print(f" Error loading header logo: {e}")

    if os.path.exists(plate_path):
        plate_img = make_circle_image(plate_path, 160)
        if plate_img and DEBUG_IMAGES:
            print("✓ Loaded header plate image: plate.jpg")

    # UI building
    build_header(root, logo_img, plate_img)
    build_navbar(root, app)

    page_container = tk.Frame(root, bg=BG_CREAM)
    page_container.pack(fill="both", expand=True)

    # Build every page
    if DEBUG_IMAGES:
        print("\nBuilding pages...")

    app["pages"]["home"] = make_home_page(page_container, app)
    app["pages"]["menu"] = make_menu_page(page_container, app)
    app["pages"]["about"] = make_about_page(page_container)
    app["pages"]["contact"] = make_contact_page(page_container)
    app["pages"]["special"] = make_special_page(page_container, app)
    app["pages"]["dashboard"] = make_dashboard_page(page_container, app)

    for p in app["pages"].values():
        p.place(x=0, y=0, relwidth=1, relheight=1)

    if DEBUG_IMAGES:
        print("\n" + "="*60)
        print(" Application initialized successfully!")
        print("="*60 + "\n")

    navigate("home")
    root.mainloop()


# Entry point
if __name__ == "__main__":
    try:
        from PIL import Image, ImageTk, ImageDraw
    except ImportError:
        print("Installing Pillow …")
        import subprocess
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image, ImageTk, ImageDraw
    run_app()
