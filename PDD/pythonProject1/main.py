# Importējam nepieciešamās bibliotēkas
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
import bcrypt
import pytest
from unittest.mock import patch, MagicMock

# Globālā mainīgā lietotāja datu glabāšanai
user_data = {}
# Ceļš uz fona attēlu lietotnē
BACKGROUND_IMAGE_PATH = "background.jpg"

# Funkcija, lai iestatītu fona attēlu Tkinter logam
def set_background(window):
    bg_img = Image.open(BACKGROUND_IMAGE_PATH)  # Atver attēlu
    bg_img = bg_img.resize((500, 500), Image.LANCZOS)  # Maina attēla izmēru
    bg_img = ImageTk.PhotoImage(bg_img)  # Konvertē attēlu, lai tas būtu saderīgs ar Tkinter
    bg_label = tk.Label(window, image=bg_img)  # Izveido label ar attēlu
    bg_label.image = bg_img  # Saglabā attēlu atsauci, lai novērstu atmiņas noplūdes
    bg_label.place(relwidth=1, relheight=1)  # Ievieto attēlu uz visu loga platumu un augstumu

# Funkcija, lai izveidotu savienojumu ar SQLite datubāzi
def connect_db():
    return sqlite3.connect('apartments.db')

# Funkcija, lai izveidotu nepieciešamās tabulas datubāzē
def create_tables():
    conn = connect_db()  # Savienojamies ar datubāzi
    cursor = conn.cursor()  # Izveidojam kursoru, lai veiktu vaicājumus
    # Izveidojam lietotāju tabulu, ja tā vēl nepastāv
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY, 
                        password BLOB, 
                        budget REAL)''')
    # Izveidojam dzīvokļu tabulu, ja tā vēl nepastāv
    cursor.execute('''CREATE TABLE IF NOT EXISTS apartments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        apartment_name TEXT,
                        price REAL,
                        image_path TEXT DEFAULT NULL,
                        owner TEXT DEFAULT NULL)''')
    conn.commit()  # Saglabājam izmaiņas datubāzē
    conn.close()  # Aizveram savienojumu ar datubāzi

# Funkcija, lai saglabātu lietotāja datus datubāzē
def save_to_db(username, password, budget):
    conn = connect_db()  # Savienojamies ar datubāzi
    cursor = conn.cursor()  # Izveidojam kursoru
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Iegūstam parolē šifrēto vērtību
    cursor.execute('INSERT OR REPLACE INTO users (username, password, budget) VALUES (?, ?, ?)',
                   (username, hashed_pw, budget))  # Saglabājam vai atjaunojam lietotāju
    conn.commit()  # Saglabājam izmaiņas datubāzē
    conn.close()  # Aizveram savienojumu ar datubāzi

# Funkcija, lai saglabātu dzīvokļa datus datubāzē
def save_apartment(username, apartment_name, price, image_path):
    conn = connect_db()  # Savienojamies ar datubāzi
    cursor = conn.cursor()  # Izveidojam kursoru
    cursor.execute('INSERT INTO apartments (username, apartment_name, price, image_path) VALUES (?, ?, ?, ?)',
                   (username, apartment_name, price, image_path))  # Saglabājam dzīvokļa datus
    conn.commit()  # Saglabājam izmaiņas datubāzē
    conn.close()  # Aizveram savienojumu ar datubāzi

# Funkcija, lai iegūtu pieejamos dzīvokļus, kuru cena nepārsniedz lietotāja budžetu
def get_available_apartments(budget):
    conn = connect_db()  # Savienojamies ar datubāzi
    cursor = conn.cursor()  # Izveidojam kursoru
    cursor.execute('SELECT id, apartment_name, price, image_path FROM apartments WHERE price <= ? AND (owner IS NULL OR owner = "")',
                   (budget,))  # Atlasām dzīvokļus, kas atbilst budžetam
    apartments = cursor.fetchall()  # Iegūstam visus dzīvokļus
    conn.close()  # Aizveram savienojumu ar datubāzi
    return apartments  # Atgriežam dzīvokļu sarakstu

# Funkcija, lai lietotājs varētu iegādāties dzīvokli
def buy_apartment(apartment_id, price, apartments_window):
    if user_data['budget'] >= price:  # Ja lietotājam ir pietiekami daudz līdzekļu
        user_data['budget'] -= price  # Samazinām budžetu
        conn = connect_db()  # Savienojamies ar datubāzi
        cursor = conn.cursor()  # Izveidojam kursoru
        cursor.execute('UPDATE apartments SET owner = ? WHERE id = ?', (user_data['username'], apartment_id))  # Atjauninām dzīvokļa īpašnieku
        conn.commit()  # Saglabājam izmaiņas datubāzē
        conn.close()  # Aizveram savienojumu ar datubāzi
        save_to_db(user_data['username'], user_data['password'], user_data['budget'])  # Saglabājam atjaunotos lietotāja datus
        messagebox.showinfo("Success", "Apartment purchased successfully!")  # Parādām paziņojumu par veiksmīgu pirkumu
        apartments_window.destroy()  # Aizveram dzīvokļu logu
    else:
        messagebox.showwarning("Error", "Not enough budget to buy this apartment.")  # Ja nav pietiekami daudz līdzekļu, parādām brīdinājumu

# Funkcija, lai atvērtu logu ar pieejamiem dzīvokļiem
def open_apartments_window():
    apartments_window = tk.Toplevel()  # Izveidojam jaunu logu
    apartments_window.title("Available Apartments")  # Loga nosaukums
    apartments_window.geometry("500x500")  # Loga izmērs
    set_background(apartments_window)  # Iestata fona attēlu logā

    label_info = tk.Label(apartments_window, text=f"Available apartments for {user_data['username']} with budget {user_data['budget']}", bg="white")  # Parāda lietotāja vārdu un budžetu
    label_info.pack(pady=10)

    available_apartments = get_available_apartments(user_data['budget'])  # Iegūst pieejamos dzīvokļus

    if available_apartments:  # Ja ir pieejami dzīvokļi
        for apartment in available_apartments:
            frame = tk.Frame(apartments_window, relief=tk.RAISED, borderwidth=2)  # Izveidojam ietvaru katram dzīvoklim
            frame.pack(pady=10, padx=10, fill="x")

            img_label = tk.Label(frame)  # Izveidojam label, lai parādītu attēlu
            img_label.pack(side=tk.LEFT, padx=10)

            try:
                img = Image.open(apartment[3])  # Atveram dzīvokļa attēlu
                img = img.resize((100, 100), Image.LANCZOS)  # Mainām attēla izmēru
                img = ImageTk.PhotoImage(img)  # Konvertējam attēlu, lai tas būtu saderīgs ar Tkinter
                img_label.config(image=img)  # Pievienojam attēlu label
                img_label.image = img  # Saglabājam atsauci uz attēlu
            except:
                img_label.config(text="No Image")  # Ja nav attēla, parādām tekstu

            details = tk.Label(frame, text=f"{apartment[1]} - ${apartment[2]}")  # Parāda dzīvokļa nosaukumu un cenu
            details.pack(side=tk.LEFT, padx=10)

            buy_button = tk.Button(frame, text="Buy", command=lambda apt_id=apartment[0], apt_price=apartment[2]: buy_apartment(apt_id, apt_price, apartments_window))  # Poga dzīvokļa iegādei
            buy_button.pack(side=tk.RIGHT, padx=10)
    else:
        label_no_apartments = tk.Label(apartments_window, text="No apartments available within your budget.", bg="white")  # Ziņojums, ja nav pieejamu dzīvokļu
        label_no_apartments.pack(pady=10)

    button_close = tk.Button(apartments_window, text="Close", command=apartments_window.destroy)  # Poga loga aizvēršanai
    button_close.pack(pady=10)

# Funkcija, lai atvērtu logu administrācijai un pievienotu dzīvokli
def open_admin_apartment_window():
    admin_window = tk.Toplevel()  # Izveidojam jaunu logu
    admin_window.title("Add Apartment")  # Loga nosaukums
    admin_window.geometry("400x400")  # Loga izmērs
    set_background(admin_window)  # Iestata fona attēlu logā

    label_info = tk.Label(admin_window, text="Add a new apartment:", bg="white")  # Parāda tekstu "Pievienot jaunu dzīvokli"
    label_info.pack(pady=10)

    entry_apartment_name = tk.Entry(admin_window)  # Ievades lauks dzīvokļa nosaukumam
    entry_apartment_name.pack(pady=5)

    entry_price = tk.Entry(admin_window)  # Ievades lauks dzīvokļa cenai
    entry_price.pack(pady=5)

    selected_image_path = tk.StringVar()  # Mainīgais, kas saglabā izvēlēto attēla ceļu
    entry_image_path = tk.Entry(admin_window, textvariable=selected_image_path, state='readonly', width=30)  # Ievades lauks attēla ceļam
    entry_image_path.pack(pady=5)

    def select_image():
        filename = filedialog.askopenfilename(title="Select Apartment Image",  # Atver failu izvēles logu
                                              filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])  # Atļauj izvēlēties attēlus
        if filename:
            selected_image_path.set(filename)  # Saglabā izvēlēto attēla ceļu

    button_browse = tk.Button(admin_window, text="Browse", command=select_image)  # Poga, lai izvēlētos attēlu
    button_browse.pack(pady=5)

    def submit_apartment():
        apartment_name = entry_apartment_name.get().strip()  # Iegūst dzīvokļa nosaukumu
        price = entry_price.get().strip()  # Iegūst dzīvokļa cenu
        image_path = selected_image_path.get().strip()  # Iegūst attēla ceļu

        # Ja visi dati ir pareizi
        if apartment_name and price.replace('.', '', 1).isdigit() and image_path:
            save_apartment('admin', apartment_name, float(price), image_path)  # Saglabājam dzīvokli datubāzē
            messagebox.showinfo("Success", "Apartment added successfully!")  # Parādām paziņojumu
            admin_window.destroy()  # Aizveram logu
        else:
            messagebox.showwarning("Error", "Please enter valid details and select an image.")  # Ja dati ir nepareizi, parādām brīdinājumu

    button_submit = tk.Button(admin_window, text="Add Apartment", command=submit_apartment)  # Poga dzīvokļa pievienošanai
    button_submit.pack(pady=10)

# Funkcija, lai atvērtu logu budžeta ievadei
def open_budget_window():
    budget_window = tk.Toplevel()  # Izveidojam jaunu logu
    budget_window.title("Enter budget")  # Loga nosaukums
    budget_window.geometry("300x200")  # Loga izmērs
    set_background(budget_window)  # Iestata fona attēlu logā

    label_info = tk.Label(budget_window, text=f"{user_data['username']}, Enter your budget:", bg="white", font=("Georgia", 14))  # Parāda lietotāja vārdu un budžeta ievades tekstu
    label_info.pack(pady=10)
    entry_budget = tk.Entry(budget_window)  # Ievades lauks budžeta ievadei
    entry_budget.pack(pady=5)

    def submit_budget():
        budget = entry_budget.get().strip()  # Iegūst budžetu no ievades lauka
        if budget.replace('.', '', 1).isdigit():  # Ja budžets ir derīgs skaitlis
            user_data['budget'] = float(budget)  # Saglabājam budžetu
            budget_window.destroy()  # Aizveram logu
            save_to_db(user_data['username'], user_data['password'], user_data['budget'])  # Saglabājam atjaunotos lietotāja datus datubāzē
            open_apartments_window()  # Atveram dzīvokļu logu
        else:
            messagebox.showwarning("Error", "Enter a valid budget")  # Ja budžets nav derīgs, parādām brīdinājumu

    button_submit = tk.Button(budget_window, text="Next", command=submit_budget, font=("Georgia", 10))  # Poga budžeta apstiprināšanai
    button_submit.pack(pady=15)

# Funkcija, lai apstrādātu lietotāja pieteikšanos
def login():
    username = entry_username.get().strip()  # Iegūst lietotāja vārdu
    password = entry_password.get().strip()  # Iegūst paroli

    if username == "admin" and password == "admin":  # Ja ir administrātora pieteikšanās
        user_data['username'] = username  # Saglabājam administrātora lietotāja vārdu
        user_data['password'] = password  # Saglabājam administrātora paroli
        root.withdraw()  # Slēdzam sākotnējo logu
        open_admin_apartment_window()  # Atveram administrācijas logu
    elif username and password:  # Ja ir derīgi lietotāja dati
        user_data['username'] = username  # Saglabājam lietotāja vārdu
        user_data['password'] = password  # Saglabājam paroli
        root.withdraw()  # Slēdzam sākotnējo logu
        open_budget_window()  # Atveram budžeta ievades logu
    else:
        messagebox.showwarning("Error", "Enter username and password.")  # Ja dati nav ievadīti, parādām brīdinājumu

# Galvenais loga izveides kods
root = tk.Tk()  # Izveidojam galveno logu
root.title("Buying Apartment")  # Loga nosaukums
root.geometry("300x250")  # Loga izmērs
set_background(root)  # Iestata fona attēlu galvenajā logā

# Loga komponentu izvietošana
label_welcome = tk.Label(root, text="Welcome to SIA Istaba", font=("Georgia", 15))  # Laipna uzruna
label_welcome.pack(pady=10)

label_username = tk.Label(root, text="Username:", bg="white", font=("Georgia", 10))  # Teksts "Lietotājvārds"
label_username.pack(pady=5)
entry_username = tk.Entry(root)  # Ievades lauks lietotājvārda ievadei
entry_username.pack(pady=5)

label_password = tk.Label(root, text="Password:", bg="white", font=("Georgia", 10))  # Teksts "Parole"
label_password.pack(pady=5)
entry_password = tk.Entry(root, show="*")  # Ievades lauks paroles ievadei (slēpj simbolus)
entry_password.pack(pady=5)

button_login = tk.Button(root, text="Log in", command=login)  # Poga, lai pieteiktos
button_login.pack(pady=20)

label_creator = tk.Label(root, text="Made by: Konstantins Jefimovs", font=("Georgia", 8))  # Informācija par autoru
label_creator.pack(pady=1, padx=1)

create_tables()  # Izveidojam datubāzi un tabulas
root.mainloop()  # Uzsākam Tkinter galveno cilpu, lai logi tiktu parādīti

# pytest testi
@pytest.fixture
def setup_database():
    create_tables()  # Izveidojam tabulas pirms katra testa
    yield
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")  # Dzēšam visus lietotājus pēc testa
    cursor.execute("DELETE FROM apartments")  # Dzēšam visus dzīvokļus pēc testa
    conn.commit()  # Saglabājam izmaiņas
    conn.close()

# Testa funkcija datubāzes savienojumam
def test_connect_db():
    conn = connect_db()
    assert isinstance(conn, sqlite3.Connection)  # Pārbaudām, vai savienojums ir izveidots
    print("Database connection test passed.")  # Izvade uz konsoles
    conn.close()  # Aizveram savienojumu

# Testa funkcija tabulu izveidei
def test_create_tables():
    conn = connect_db()
