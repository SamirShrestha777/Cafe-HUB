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