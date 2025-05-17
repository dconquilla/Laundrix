import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import re
import datetime
import os
import time

# ---------------- DATABASE SETUP ----------------
def initialize_db():
    # Force reset database to ensure correct schema
    # Comment out after first run if you want to keep data
    # if os.path.exists("laundry.db"):
    #     os.remove("laundry.db")

    conn = sqlite3.connect("laundry.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys=off;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'customer'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            service TEXT,
            date TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS laundry_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            item TEXT NOT NULL,
            status TEXT NOT NULL,
            updated_at DATETIME,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            seen INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dryer_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dryer_number INTEGER NOT NULL,
            username TEXT NOT NULL,
            start_time DATETIME,
            status TEXT DEFAULT 'In Progress',
            timer_minutes INTEGER DEFAULT 0,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS washer_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            washer_number INTEGER NOT NULL,
            username TEXT NOT NULL,
            start_time DATETIME,
            status TEXT DEFAULT 'In Progress',
            timer_minutes INTEGER DEFAULT 0,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    cursor.execute("INSERT OR IGNORE INTO users (username, email, phone, password, role) VALUES (?, ?, ?, ?, ?)",
                   ('admin', 'admin@example.com', '1234567890', 'adminpass', 'admin'))

    conn.commit()
    conn.close()

# ---------------- USER FUNCTIONS ----------------
def register_user(username, email, phone, password):
    try:
        conn = sqlite3.connect("laundry.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, phone, password, role) VALUES (?, ?, ?, ?, 'customer')",
                       (username, email, phone, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect("laundry.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

# ---------------- CUSTOMER DASHBOARD ----------------
def open_dashboard(username):
    dash = tk.Tk()
    dash.title("Laundrix - Customer Dashboard")
    dash.geometry("600x500")
    dash.config(bg="white")

    tk.Label(dash, text=f"🧺 Welcome, {username}", font=("Arial", 20, "bold"), fg="#00bfff", bg="white").pack(pady=10)

    def make_appointment():
        top = tk.Toplevel(dash)
        top.title("Make Appointment")
        tk.Label(top, text="Service Type:").pack()
        service_entry = tk.Entry(top)
        service_entry.pack()
        tk.Label(top, text="Date (YYYY-MM-DD):").pack()
        date_entry = tk.Entry(top)
        date_entry.pack()

        def save_appointment():
            service = service_entry.get()
            date = date_entry.get()
            conn = sqlite3.connect("laundry.db")
            c = conn.cursor()
            c.execute("INSERT INTO appointments (username, service, date) VALUES (?, ?, ?)",
                      (username, service, date))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Appointment made successfully.")
            top.destroy()

        tk.Button(top, text="Submit", command=save_appointment).pack(pady=10)

    def view_status():
        top = tk.Toplevel(dash)
        top.title("Laundry Status")
        conn = sqlite3.connect("laundry.db")
        c = conn.cursor()
        c.execute("SELECT item, status, updated_at FROM laundry_status WHERE username=?", (username,))
        records = c.fetchall()
        conn.close()
        if not records:
            tk.Label(top, text="No laundry status found.").pack()
        else:
            for item, status, updated_at in records:
                tk.Label(top, text=f"{item}: {status} (Updated on {updated_at})").pack()

    def track_history():
        top = tk.Toplevel(dash)
        top.title("Item History")
        conn = sqlite3.connect("laundry.db")
        c = conn.cursor()
        c.execute("SELECT item, status, updated_at FROM laundry_status WHERE username=?", (username,))
        records = c.fetchall()
        conn.close()
        if not records:
            tk.Label(top, text="No item history found.").pack()
        else:
            for item, status, updated_at in records:
                tk.Label(top, text=f"{item}: {status} on {updated_at}").pack()

    def view_notifications():
        top = tk.Toplevel(dash)
        top.title("Notifications")
        conn = sqlite3.connect("laundry.db")
        c = conn.cursor()
        c.execute("SELECT message FROM notifications WHERE username=? AND seen=0", (username,))
        notes = c.fetchall()
        c.execute("UPDATE notifications SET seen=1 WHERE username=?", (username,))
        conn.commit()
        conn.close()
        if not notes:
            tk.Label(top, text="No new notifications.").pack()
        else:
            for (msg,) in notes:
                tk.Label(top, text=f"• {msg}").pack(anchor='w')

    options = [
        ("Make Appointment", make_appointment),
        ("View Laundry Status", view_status),
        ("Track Item History", track_history),
        ("Notifications", view_notifications)
    ]

    frame = tk.Frame(dash, bg="white")
    frame.pack(pady=20)

    for (text, cmd) in options:
        tk.Button(frame, text=text, command=cmd, bg="#00bfff", fg="white", font=("Arial", 12), width=25).pack(pady=5)

    dash.mainloop()

# ---------------- ADMIN DASHBOARD ----------------
def open_admin_dashboard(username):
    dash = tk.Tk()
    dash.title("Laundrix - Admin Dashboard")
    dash.geometry("700x500")
    dash.config(bg="lightblue")

    tk.Label(dash, text=f"🧺 Welcome Admin: {username}", font=("Arial", 20, "bold"), bg="lightblue").pack(pady=10)

    def dashboard_overview():
        top = tk.Toplevel(dash)
        top.title("Dashboard Overview")

        conn = sqlite3.connect("laundry.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE role='customer'")
        users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM appointments")
        appts = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM laundry_status WHERE status != 'Delivered'")
        in_progress = c.fetchone()[0]
        conn.close()

        tk.Label(top, text=f"Total Customers: {users}", font=("Arial", 12)).pack(pady=5)
        tk.Label(top, text=f"Total Appointments: {appts}", font=("Arial", 12)).pack(pady=5)
        tk.Label(top, text=f"Laundry in Progress: {in_progress}", font=("Arial", 12)).pack(pady=5)

    def check_in_laundry():
        top = tk.Toplevel(dash)
        top.title("Check in Laundry")

        tk.Label(top, text="Customer Username:").pack()
        user_entry = tk.Entry(top)
        user_entry.pack()

        tk.Label(top, text="Laundry Item Description:").pack()
        item_entry = tk.Entry(top)
        item_entry.pack()

        def checkin():
            username = user_entry.get()
            item = item_entry.get()
            status = "Received"
            updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = sqlite3.connect("laundry.db")
            c = conn.cursor()
            
            c.execute("SELECT id FROM users WHERE username=?", (username,))
            if not c.fetchone():
                messagebox.showerror("Error", "User not found.")
                conn.close()
                return

            c.execute("INSERT INTO laundry_status (username, item, status, updated_at) VALUES (?, ?, ?, ?)",
                      (username, item, status, updated_at))
            
            c.execute("SELECT washer_number FROM washer_assignments WHERE status='In Progress'")
            used_washers = [row[0] for row in c.fetchall()]
            
            for i in range(1, 4):
                if i not in used_washers:
                    c.execute("INSERT INTO washer_assignments (washer_number, username, start_time, status, timer_minutes) VALUES (?, ?, ?, ?, ?)",
                             (i, username, updated_at, 'In Progress', 0))
                    break
            else:
                c.execute("SELECT washer_number FROM washer_assignments ORDER BY start_time ASC LIMIT 1")
                oldest_washer = c.fetchone()
                if oldest_washer:
                    c.execute("UPDATE washer_assignments SET username=?, start_time=?, status='In Progress', timer_minutes=0 WHERE washer_number=?",
                             (username, updated_at, oldest_washer[0]))

            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Laundry item checked in and assigned to washer.")
            top.destroy()

        tk.Button(top, text="Submit", command=checkin).pack(pady=10)

    def manage_queues(machine_type):
        top = tk.Toplevel(dash)
        top.title(f"Manage {machine_type} Queues")
        top.geometry("600x400")

        status_frame = tk.Frame(top)
        status_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(status_frame, columns=('Machine', 'Username', 'Start Time', 'Status', 'Timer'), show='headings')
        tree.heading('Machine', text=f'{machine_type} #')
        tree.heading('Username', text='Username')
        tree.heading('Start Time', text='Start Time')
        tree.heading('Status', text='Status')
        tree.heading('Timer', text='Timer (min:sec)')
        tree.column('Machine', width=80)
        tree.column('Username', width=120)
        tree.column('Start Time', width=150)
        tree.column('Status', width=100)
        tree.column('Timer', width=100)
        tree.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        style.map('Treeview', 
                 background=[('selected', '#e1f5fe')],
                 foreground=[('selected', 'black')])

        timers = {}  # Store timer end times: {machine_number: {'end_time': float, 'username': str}}

        def update_timers():
            try:
                current_time = time.time()
                for machine_number, data in list(timers.items()):
                    remaining = max(0, data['end_time'] - current_time)
                    mins = int(remaining // 60)
                    secs = int(remaining % 60)
                    timer_display = f"{mins:02d}:{secs:02d}"
                    
                    for item in tree.get_children():
                        if tree.item(item)['values'][0] == machine_number:
                            try:
                                current_values = list(tree.item(item)['values'])
                                current_values[4] = timer_display  # Update Timer column
                                tree.item(item, values=current_values)
                            except tk.TclError:
                                return  # Window closed

                    if remaining <= 0:
                        del timers[machine_number]
                        conn = sqlite3.connect("laundry.db")
                        c = conn.cursor()
                        c.execute(f"UPDATE {machine_type.lower()}_assignments SET status='Done', timer_minutes=0 WHERE {machine_type.lower()}_number=?", (machine_number,))
                        status = 'Washed' if machine_type == 'Washer' else 'Dried'
                        c.execute("UPDATE laundry_status SET status=?, updated_at=? WHERE username=? AND status='Received'",
                                 (status, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['username']))
                        conn.commit()
                        conn.close()
                        refresh_tree()

                tree.update()  # Force Treeview refresh
                top.update()   # Force window refresh
                top.after(1000, update_timers)
            except tk.TclError:
                pass  # Window closed

        def refresh_tree():
            for item in tree.get_children():
                tree.delete(item)
            
            conn = sqlite3.connect("laundry.db")
            c = conn.cursor()
            try:
                c.execute(f"SELECT {machine_type.lower()}_number, username, start_time, status, timer_minutes FROM {machine_type.lower()}_assignments")
                assignments = c.fetchall()
            except sqlite3.OperationalError as e:
                messagebox.showerror("Database Error", f"Error accessing {machine_type} assignments: {e}")
                conn.close()
                return
            conn.close()

            timers.clear()  # Reset timers on refresh
            for machine_number, username, start_time, status, timer_minutes in assignments:
                timer_display = "00:00"
                if status == 'In Progress' and timer_minutes > 0:
                    timers[machine_number] = {
                        'end_time': time.time() + timer_minutes * 60,
                        'username': username
                    }
                    timer_display = f"{timer_minutes:02d}:00"
                tree.insert('', tk.END, values=(machine_number, username, start_time, status or 'In Progress', timer_display),
                           tags=(status or 'In Progress',))
            
            tree.tag_configure('In Progress', foreground='orange')
            tree.tag_configure('Done', foreground='green')
            tree.update()  # Force Treeview refresh

        refresh_tree()
        top.after(1000, update_timers)  # Start timer updates

        button_frame = tk.Frame(top)
        button_frame.pack(pady=10)

        def add_assignment():
            add_win = tk.Toplevel(top)
            add_win.title(f"Add {machine_type} Assignment")
            
            tk.Label(add_win, text="Username:").pack()
            user_entry = tk.Entry(add_win)
            user_entry.pack()

            def submit_add():
                username = user_entry.get()
                updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                conn = sqlite3.connect("laundry.db")
                c = conn.cursor()
                
                c.execute("SELECT id FROM users WHERE username=?", (username,))
                if not c.fetchone():
                    messagebox.showerror("Error", "User not found.")
                    conn.close()
                    return

                c.execute(f"SELECT {machine_type.lower()}_number FROM {machine_type.lower()}_assignments WHERE status='In Progress'")
                used_machines = [row[0] for row in c.fetchall()]
                
                for i in range(1, 4):
                    if i not in used_machines:
                        c.execute(f"INSERT INTO {machine_type.lower()}_assignments ({machine_type.lower()}_number, username, start_time, status, timer_minutes) VALUES (?, ?, ?, ?, ?)",
                                 (i, username, updated_at, 'In Progress', 0))
                        break
                else:
                    c.execute(f"SELECT {machine_type.lower()}_number FROM {machine_type.lower()}_assignments ORDER BY start_time ASC LIMIT 1")
                    oldest_machine = c.fetchone()
                    if oldest_machine:
                        c.execute(f"UPDATE {machine_type.lower()}_assignments SET username=?, start_time=?, status='In Progress', timer_minutes=0 WHERE {machine_type.lower()}_number=?",
                                 (username, updated_at, oldest_machine[0]))
                
                conn.commit()
                conn.close()
                refresh_tree()
                add_win.destroy()

            tk.Button(add_win, text="Submit", command=submit_add).pack(pady=10)

        def delete_assignment():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", f"Please select a {machine_type.lower()} assignment.")
                return
            
            machine_number = tree.item(selected[0])['values'][0]
            if machine_number in timers:
                del timers[machine_number]
            
            conn = sqlite3.connect("laundry.db")
            c = conn.cursor()
            c.execute(f"DELETE FROM {machine_type.lower()}_assignments WHERE {machine_type.lower()}_number=?", (machine_number,))
            conn.commit()
            conn.close()
            
            refresh_tree()
            messagebox.showinfo("Success", f"{machine_type} assignment removed.")

        def set_timer():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", f"Please select a {machine_type.lower()} assignment.")
                return
            
            timer_win = tk.Toplevel(top)
            timer_win.title("Set Timer")
            
            tk.Label(timer_win, text="Minutes:").pack()
            minutes_entry = tk.Entry(timer_win)
            minutes_entry.pack()

            def submit_timer():
                try:
                    minutes = int(minutes_entry.get())
                    if minutes <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid number of minutes.")
                    return
                
                machine_number = tree.item(selected[0])['values'][0]
                username = tree.item(selected[0])['values'][1]
                
                timers[machine_number] = {
                    'end_time': time.time() + minutes * 60,
                    'username': username
                }
                
                conn = sqlite3.connect("laundry.db")
                c = conn.cursor()
                c.execute(f"UPDATE {machine_type.lower()}_assignments SET status='In Progress', timer_minutes=? WHERE {machine_type.lower()}_number=?",
                         (minutes, machine_number))
                conn.commit()
                conn.close()
                
                refresh_tree()  # Force immediate refresh
                timer_win.destroy()

            tk.Button(timer_win, text="Set Timer", command=submit_timer).pack(pady=10)

        def mark_done():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", f"Please select a {machine_type.lower()} assignment.")
                return
            
            machine_number = tree.item(selected[0])['values'][0]
            username = tree.item(selected[0])['values'][1]
            
            if machine_number in timers:
                del timers[machine_number]
            
            conn = sqlite3.connect("laundry.db")
            c = conn.cursor()
            c.execute(f"DELETE FROM {machine_type.lower()}_assignments WHERE {machine_type.lower()}_number=?", (machine_number,))
            status = 'Washed' if machine_type == 'Washer' else 'Dried'
            c.execute("UPDATE laundry_status SET status=?, updated_at=? WHERE username=? AND status='Received'",
                     (status, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
            conn.commit()
            conn.close()
            
            refresh_tree()
            messagebox.showinfo("Success", f"{machine_type} marked as done and removed from queue.")

        tk.Button(button_frame, text="Add", command=add_assignment, bg="#00bfff").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete", command=delete_assignment, bg="#ff4444").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Set Timer", command=set_timer, bg="#44ff44").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Done", command=mark_done, bg="#ffaa00").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Refresh", command=refresh_tree, bg="#aaaaaa").pack(side=tk.LEFT, padx=5)

    def generate_reports():
        top = tk.Toplevel(dash)
        top.title("Generate Reports")

        conn = sqlite3.connect("laundry.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM appointments")
        total_appointments = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM laundry_status")
        total_items = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM laundry_status WHERE status='Delivered'")
        delivered = c.fetchone()[0]
        conn.close()

        report = (
            f"📋 Total Appointments: {total_appointments}\n"
            f"🧺 Total Laundry Items: {total_items}\n"
            f"✅ Delivered Items: {delivered}\n"
        )

        tk.Label(top, text=report, justify="left", font=("Courier", 12)).pack(padx=20, pady=20)

    def manage_customers():
        top = tk.Toplevel(dash)
        top.title("Manage Customer Info")

        tk.Label(top, text="Username:").pack()
        username_entry = tk.Entry(top)
        username_entry.pack()
        tk.Label(top, text="Email:").pack()
        email_entry = tk.Entry(top)
        email_entry.pack()
        tk.Label(top, text="Phone:").pack()
        phone_entry = tk.Entry(top)
        phone_entry.pack()

        def save_customer():
            uname = username_entry.get()
            email = email_entry.get()
            phone = phone_entry.get()

            conn = sqlite3.connect("laundry.db")
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=?", (uname,))
            existing = c.fetchone()

            if existing:
                c.execute("UPDATE users SET email=?, phone=? WHERE username=?", (email, phone, uname))
                msg = "Customer updated."
            else:
                c.execute("INSERT INTO users (username, email, phone, password, role) VALUES (?, ?, ?, ?, 'customer')",
                          (uname, email, phone, "default123"))
                msg = "Customer added with default password: default123"

            conn.commit()
            conn.close()
            messagebox.showinfo("Success", msg)
            top.destroy()

        tk.Button(top, text="Save", command=save_customer).pack(pady=10)

    def view_appointments(user):
        top = tk.Toplevel()
        top.title("Appointments")
        tk.Label(top, text="Appointments").pack(pady=5)

        conn = sqlite3.connect("laundry.db")
        c = conn.cursor()
        if user == "all":
            c.execute("SELECT username, service, date, status FROM appointments")
        else:
            c.execute("SELECT service, date, status FROM appointments WHERE username=?", (user,))
        rows = c.fetchall()
        conn.close()

        if not rows:
            tk.Label(top, text="No appointments found.").pack()
        else:
            for row in rows:
                tk.Label(top, text=" | ".join(map(str, row))).pack(anchor='w')

    def view_laundry_records(user):
        top = tk.Toplevel()
        top.title("Laundry Records")
        tk.Label(top, text="Laundry Records").pack(pady=5)

        conn = sqlite3.connect("laundry.db")
        c = conn.cursor()
        if user == "all":
            c.execute("SELECT username, item, status, updated_at FROM laundry_status")
        else:
            c.execute("SELECT item, status, updated_at FROM laundry_status WHERE username=?", (user,))
        rows = c.fetchall()
        conn.close()

        if not rows:
            tk.Label(top, text="No laundry records found.").pack()
        else:
            for row in rows:
                tk.Label(top, text=" | ".join(map(str, row))).pack(anchor='w')

    def send_notifications(admin_user):
        top = tk.Toplevel()
        top.title("Send Notification")

        tk.Label(top, text="To (username):").pack()
        to_entry = tk.Entry(top)
        to_entry.pack()
        tk.Label(top, text="Message:").pack()
        msg_entry = tk.Entry(top)
        msg_entry.pack()

        def send():
            to_user = to_entry.get()
            msg = msg_entry.get()
            conn = sqlite3.connect("laundry.db")
            c = conn.cursor()
            c.execute("INSERT INTO notifications (username, message) VALUES (?, ?)", (to_user, msg))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sent", "Notification sent successfully.")
            top.destroy()

        tk.Button(top, text="Send", command=send).pack(pady=10)

    features = [
        ("Dashboard Overview", dashboard_overview),
        ("View Customer Appointments", lambda: view_appointments("all")),
        ("View All Laundry Records", lambda: view_laundry_records("all")),
        ("Generate Reports", generate_reports),
        ("Check in Laundry", check_in_laundry),
        ("Manage Washer Queues", lambda: manage_queues("Washer")),
        ("Manage Dryer Queues", lambda: manage_queues("Dryer")),
        ("Add/Edit Customer Info", manage_customers),
        ("Send Notifications", lambda: send_notifications(username)),
        ("Log Out", dash.destroy)
    ]

    frame = tk.Frame(dash, bg="lightblue")
    frame.pack(pady=10)

    for idx, (label, cmd) in enumerate(features):
        btn = tk.Button(frame, text=label, command=cmd, width=30, bg="#0080ff", fg="white", font=("Arial", 11))
        btn.grid(row=idx//2, column=idx%2, padx=10, pady=5)

    dash.mainloop()

# ---------------- GUI SETUP ----------------
def show_frame(frame):
    frame.tkraise()

def clear_entries(entries):
    for entry in entries.values():
        entry.delete(0, tk.END)

initialize_db()

root = tk.Tk()
root.title("Laundrix Login/Register")
root.geometry("400x500")
root.configure(bg="#ccf5ff")

register_frame = tk.Frame(root, bg="#ccf5ff")
login_frame = tk.Frame(root, bg="#ccf5ff")
for frame in (register_frame, login_frame):
    frame.place(relwidth=1, relheight=1)

# ---------------- REGISTER ----------------
tk.Label(register_frame, text="Register", font=("Arial", 20, "bold"), bg="#ccf5ff").pack(pady=10)

fields = ["Username", "Email", "Phone Number", "Password", "Confirm Password"]
register_entries = {}

for field in fields:
    tk.Label(register_frame, text=field, bg="#ccf5ff").pack()
    show = '*' if "Password" in field else ''
    entry = tk.Entry(register_frame, show=show)
    entry.pack()
    register_entries[field] = entry

def confirm_registration():
    u = register_entries["Username"].get()
    e = register_entries["Email"].get()
    p = register_entries["Phone Number"].get()
    pw1 = register_entries["Password"].get()
    pw2 = register_entries["Confirm Password"].get()

    if not all([u, e, p, pw1, pw2]):
        messagebox.showwarning("Warning", "All fields are required.")
        return
    if not re.match(r"[^@]+@[^@]+\.[^@]+", e):
        messagebox.showerror("Error", "Invalid email format.")
        return
    if not p.isdigit() or len(p) < 7:
        messagebox.showerror("Error", "Invalid phone number.")
        return
    if pw1 != pw2:
        messagebox.showerror("Error", "Passwords do not match.")
        return
    if not register_user(u, e, p, pw1):
        messagebox.showerror("Error", "Username already exists.")
        return

    messagebox.showinfo("Success", "Registration successful!")
    clear_entries(register_entries)
    show_frame(login_frame)

tk.Button(register_frame, text="Register", bg="#00ccff", command=confirm_registration).pack(pady=10)
tk.Button(register_frame, text="Go to Login", command=lambda: show_frame(login_frame)).pack()

# ---------------- LOGIN ----------------
tk.Label(login_frame, text="Login", font=("Arial", 20, "bold"), bg="#ccf5ff").pack(pady=20)

tk.Label(login_frame, text="Username", bg="#ccf5ff").pack()
login_user_entry = tk.Entry(login_frame)
login_user_entry.pack()

tk.Label(login_frame, text="Password", bg="#ccf5ff").pack()
login_pass_entry = tk.Entry(login_frame, show="*")
login_pass_entry.pack()

def perform_login():
    u = login_user_entry.get()
    p = login_pass_entry.get()

    result = login_user(u, p)

    if result:
        role = result[0]
        messagebox.showinfo("Success", f"Welcome, {u} ({role})!")
        root.destroy()
        if role == 'admin':
            open_admin_dashboard(u)
        else:
            open_dashboard(u)
    else:
        messagebox.showerror("Error", "Invalid login credentials.")

tk.Button(login_frame, text="Login", bg="#00ccff", command=perform_login).pack(pady=10)
tk.Button(login_frame, text="Go to Register", command=lambda: show_frame(register_frame)).pack()

# ---------------- START ----------------
show_frame(register_frame)
root.mainloop()