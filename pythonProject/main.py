import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
import bcrypt
from unittest.mock import MagicMock, patch
import pytest

# Global variable for user data
user_data = {}
BACKGROUND_IMAGE_PATH = "background.jpg"


# Set background image
def set_background(window):
    bg_img = Image.open(BACKGROUND_IMAGE_PATH)
    bg_img = bg_img.resize((500, 500), Image.LANCZOS)
    bg_img = ImageTk.PhotoImage(bg_img)

    bg_label = tk.Label(window, image=bg_img)
    bg_label.image = bg_img
    bg_label.place(relwidth=1, relheight=1)


# Database connection function
def connect_db():
    return sqlite3.connect(':memory:')  # Use in-memory database for testing


# Create tables for users and apartments
def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY, 
                        password BLOB, 
                        budget REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS apartments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        apartment_name TEXT,
                        price REAL,
                        image_path TEXT DEFAULT NULL,
                        owner TEXT DEFAULT NULL)''')
    conn.commit()


# Save user data (username, password, budget) to the database
def save_to_db(username, password, budget, conn):
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('INSERT OR REPLACE INTO users (username, password, budget) VALUES (?, ?, ?)',
                   (username, hashed_password, budget))
    conn.commit()


# Save apartment data to the database
def save_apartment(username, apartment_name, price, image_path, conn):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO apartments (username, apartment_name, price, image_path) VALUES (?, ?, ?, ?)',
                   (username, apartment_name, price, image_path))
    conn.commit()


# Get available apartments based on the user's budget
def get_available_apartments(budget, conn):
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, apartment_name, price, image_path FROM apartments WHERE price <= ? AND (owner IS NULL OR owner = "")',
        (budget,))
    apartments = cursor.fetchall()
    return apartments


# Buy an apartment and update the owner's budget
def buy_apartment(apartment_id, price, apartments_window, conn):
    if user_data['budget'] >= price:
        user_data['budget'] -= price
        cursor = conn.cursor()
        cursor.execute('UPDATE apartments SET owner = ? WHERE id = ?', (user_data['username'], apartment_id))
        conn.commit()
        save_to_db(user_data['username'], user_data['password'], user_data['budget'], conn)
        messagebox.showinfo("Success", "Apartment purchased successfully!")
        apartments_window.destroy()
    else:
        messagebox.showwarning("Error", "Not enough budget to buy this apartment.")


# Open apartments window to display available apartments
def open_apartments_window(conn):
    apartments_window = tk.Toplevel()
    apartments_window.title("Available Apartments")
    apartments_window.geometry("500x500")
    set_background(apartments_window)

    label_info = tk.Label(apartments_window,
                          text=f"Available apartments for {user_data['username']} with budget {user_data['budget']}",
                          bg="white")
    label_info.pack(pady=10)

    available_apartments = get_available_apartments(user_data['budget'], conn)

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

            buy_button = tk.Button(frame, text="Buy",
                                   command=lambda apt_id=apartment[0], apt_price=apartment[2]: buy_apartment(apt_id,
                                                                                                             apt_price,
                                                                                                             apartments_window,
                                                                                                             conn))
            buy_button.pack(side=tk.RIGHT, padx=10)
    else:
        label_no_apartments = tk.Label(apartments_window, text="No apartments available within your budget.",
                                       bg="white")
        label_no_apartments.pack(pady=10)

    button_close = tk.Button(apartments_window, text="Close", command=apartments_window.destroy)
    button_close.pack(pady=10)


# Login function for authentication
def login():
    username = entry_username.get().strip()
    password = entry_password.get().strip()

    if username == "admin" and password == "admin":
        user_data['username'] = username
        user_data['password'] = password
        root.withdraw()
        open_apartments_window(connect_db())  # Admin opens apartment window
        return

    if username and password:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT password, budget FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()

        if result:
            stored_hash, budget = result
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                user_data['username'] = username
                user_data['password'] = password
                user_data['budget'] = budget
                root.withdraw()
                open_apartments_window(connect_db())  # User opens apartment window
            else:
                messagebox.showwarning("Error", "Incorrect password.")
        else:
            # If user not found, register
            conn = connect_db()
            save_to_db(username, password, 0.0, conn)
            user_data['username'] = username
            user_data['password'] = password
            user_data['budget'] = 0.0
            messagebox.showinfo("New user", "New user registered. Set your budget.")
            root.withdraw()
            open_apartments_window(connect_db())  # Open apartments window for new user
    else:
        messagebox.showwarning("Error", "Enter username and password.")


# Create the main login window
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

label_footer = tk.Label(root, text="Made by: Konstantins Jefimovs", font=("Georgia", 8))
label_footer.pack(pady=1)

# Create the tables in the in-memory database for testing
conn = connect_db()
create_tables(conn)

root.mainloop()


# TESTING PART BELOW USING PYTEST

@pytest.fixture(scope="module")
def mock_db():
    # Create a mock SQLite database for testing purposes
    connection = sqlite3.connect(':memory:')  # Use in-memory database for testing
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Create tables for testing
    create_tables(connection)

    yield connection  # This will be used in tests

    connection.close()  # Close connection after tests


# Test the function to save a user to the database
def test_save_to_db(mock_db):
    save_to_db("testuser", "password123", 1000.0, mock_db)
    cursor = mock_db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = 'testuser'")
    user = cursor.fetchone()
    assert user is not None
    assert user['username'] == "testuser"
    assert user['budget'] == 1000.0


# Test the function to retrieve available apartments within a budget
def test_get_available_apartments(mock_db):
    cursor = mock_db.cursor()
    cursor.execute('INSERT INTO apartments (username, apartment_name, price, image_path) VALUES (?, ?, ?, ?)',
                   ('admin', 'Apartment 1', 500.0, 'image_path_1'))
    cursor.execute('INSERT INTO apartments (username, apartment_name, price, image_path) VALUES (?, ?, ?, ?)',
                   ('admin', 'Apartment 2', 1500.0, 'image_path_2'))
    mock_db.commit()

    apartments = get_available_apartments(1000.0, mock_db)
    assert len(apartments) == 1
    assert apartments[0][1] == 'Apartment 1'


# Run the tests using pytest
if __name__ == '__main__':
    pytest.main()
