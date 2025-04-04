import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
import os

user_data = {}
BACKGROUND_IMAGE_PATH = "background.jpg"

def set_background(window):
    bg_img = Image.open(BACKGROUND_IMAGE_PATH)
    bg_img = bg_img.resize((500, 500), Image.LANCZOS)
    bg_img = ImageTk.PhotoImage(bg_img)

    bg_label = tk.Label(window, image=bg_img)
    bg_label.image = bg_img
    bg_label.place(relwidth=1, relheight=1)

def connect_db():
    return sqlite3.connect('apartments.db')

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY, 
                        password TEXT, 
                        budget REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS apartments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        apartment_name TEXT,
                        price REAL,
                        image_path TEXT DEFAULT NULL,
                        owner TEXT DEFAULT NULL)''')
    conn.commit()
    conn.close()

def save_to_db(username, password, budget):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users (username, password, budget) VALUES (?, ?, ?)',
                   (username, password, budget))
    conn.commit()
    conn.close()

def save_apartment(username, apartment_name, price, image_path):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO apartments (username, apartment_name, price, image_path) VALUES (?, ?, ?, ?)',
                   (username, apartment_name, price, image_path))
    conn.commit()
    conn.close()

def get_available_apartments(budget):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, apartment_name, price, image_path FROM apartments WHERE price <= ? AND (owner IS NULL OR owner = "")',
                   (budget,))
    apartments = cursor.fetchall()
    conn.close()
    return apartments

def buy_apartment(apartment_id, price, apartments_window):
    if user_data['budget'] >= price:
        user_data['budget'] -= price
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE apartments SET owner = ? WHERE id = ?', (user_data['username'], apartment_id))
        conn.commit()
        conn.close()
        save_to_db(user_data['username'], user_data['password'], user_data['budget'])
        messagebox.showinfo("Success", "Apartment purchased successfully!")
        apartments_window.destroy()
    else:
        messagebox.showwarning("Error", "Not enough budget to buy this apartment.")

def open_apartments_window():
    apartments_window = tk.Toplevel()
    apartments_window.title("Available Apartments")
    apartments_window.geometry("500x500")
    set_background(apartments_window)

    label_info = tk.Label(apartments_window, text=f"Available apartments for {user_data['username']} with budget {user_data['budget']}", bg="white")
    label_info.pack(pady=10)

    available_apartments = get_available_apartments(user_data['budget'])

    if available_apartments:
        for apartment in available_apartments:
            frame = tk.Frame(apartments_window, relief=tk.RAISED, borderwidth=2)
            frame.pack(pady=10, padx=10, fill="x")

            img_label = tk.Label(frame)
            img_label.pack(side=tk.LEFT, padx=10)

            try:
                img = Image.open(apartment[3])
                img = img.resize((100, 100), Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                img_label.config(image=img)
                img_label.image = img
            except:
                img_label.config(text="No Image")

            details = tk.Label(frame, text=f"{apartment[1]} - ${apartment[2]}")
            details.pack(side=tk.LEFT, padx=10)

            buy_button = tk.Button(frame, text="Buy", command=lambda apt_id=apartment[0], apt_price=apartment[2]: buy_apartment(apt_id, apt_price, apartments_window))
            buy_button.pack(side=tk.RIGHT, padx=10)
    else:
        label_no_apartments = tk.Label(apartments_window, text="No apartments available within your budget.", bg="white")
        label_no_apartments.pack(pady=10)

    button_close = tk.Button(apartments_window, text="Close", command=apartments_window.destroy)
    button_close.pack(pady=10)

def open_admin_apartment_window():
    admin_window = tk.Toplevel()
    admin_window.title("Add Apartment")
    admin_window.geometry("400x400")
    set_background(admin_window)

    label_info = tk.Label(admin_window, text="Add a new apartment:", bg="white")
    label_info.pack(pady=10)

    entry_apartment_name = tk.Entry(admin_window)
    entry_apartment_name.pack(pady=5)

    entry_price = tk.Entry(admin_window)
    entry_price.pack(pady=5)

    selected_image_path = tk.StringVar()
    entry_image_path = tk.Entry(admin_window, textvariable=selected_image_path, state='readonly', width=30)
    entry_image_path.pack(pady=5)

    def select_image():
        filename = filedialog.askopenfilename(title="Select Apartment Image",
                                              filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if filename:
            selected_image_path.set(filename)

    button_browse = tk.Button(admin_window, text="Browse", command=select_image)
    button_browse.pack(pady=5)

    def submit_apartment():
        apartment_name = entry_apartment_name.get().strip()
        price = entry_price.get().strip()
        image_path = selected_image_path.get().strip()

        if apartment_name and price.replace('.', '', 1).isdigit() and image_path:
            save_apartment('admin', apartment_name, float(price), image_path)
            messagebox.showinfo("Success", "Apartment added successfully!")
            admin_window.destroy()
        else:
            messagebox.showwarning("Error", "Please enter valid details and select an image.")

    button_submit = tk.Button(admin_window, text="Add Apartment", command=submit_apartment)
    button_submit.pack(pady=10)

def open_budget_window():
    budget_window = tk.Toplevel()
    budget_window.title("Enter budget")
    budget_window.geometry("300x200")
    set_background(budget_window)

    label_info = tk.Label(budget_window, text=f"{user_data['username']}, Enter your budget:", bg="white", font=("Georgia", 14))
    label_info.pack(pady=10)
    entry_budget = tk.Entry(budget_window)
    entry_budget.pack(pady=5)

    def submit_budget():
        budget = entry_budget.get().strip()
        if budget.replace('.', '', 1).isdigit():
            user_data['budget'] = float(budget)
            budget_window.destroy()
            save_to_db(user_data['username'], user_data['password'], user_data['budget'])
            open_apartments_window()
        else:
            messagebox.showwarning("Error", "Enter a valid budget")

    button_submit = tk.Button(budget_window, text="Next", command=submit_budget, font=("Georgia", 10))
    button_submit.pack(pady=15)

def login():
    username = entry_username.get().strip()
    password = entry_password.get().strip()
    if username == "admin" and password == "admin":
        user_data['username'] = username
        user_data['password'] = password
        root.withdraw()
        open_admin_apartment_window()
    elif username and password:
        user_data['username'] = username
        user_data['password'] = password
        root.withdraw()
        open_budget_window()
    else:
        messagebox.showwarning("Error", "Enter username and password.")

root = tk.Tk()
root.title("Buying Apartment")
root.geometry("300x250")
set_background(root)


label_welcome = tk.Label(root, text="Welcome to SIA Istaba", font=("Georgia", 15))
label_welcome.pack(pady=10)



label_username = tk.Label(root, text="Username:", bg="white", font=("Georgia", 10))
label_username.pack(pady=5)
entry_username = tk.Entry(root)
entry_username.pack(pady=5)

label_password = tk.Label(root, text="Password:", bg="white", font=("Georgia", 10))
label_password.pack(pady=5)
entry_password = tk.Entry(root, show="*")
entry_password.pack(pady=5)

button_login = tk.Button(root, text="Log in", command=login)
button_login.pack(pady=20)

label_welcome = tk.Label(root, text="Made by: Konstantins Jefimovs", font=("Georgia", 8))
label_welcome.pack(pady=1, padx=1)

create_tables()
root.mainloop()


