import tkinter as tk
from tkinter import messagebox
import json
import hashlib
import mysql.connector
import os
import webbrowser

def md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def offne_info():
    webbrowser.open("https://py-setup.buch-archiv20-software.de/python_setup.php")

def teste_db_verbindung(host, user, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        conn.close()
        return True
    except mysql.connector.Error as err:
        return str(err)

def setup_speichern():
    host = ein_host.get()
    user = ein_user.get()
    password = ein_pass.get()
    database = ein_db.get()
    inhaberid = ein_inhaberid.get()
    inhaber = ein_inhaber.get()
    adminuser = ein_adminuser.get()
    adminpass = ein_adminpass.get()

    if not all([host, user, password, database, inhaberid, inhaber, adminuser, adminpass]):
        messagebox.showerror("Fehler", "Bitte alle Felder ausfüllen!")
        return

    test = teste_db_verbindung(host, user, password, database)
    if test != True:
        messagebox.showerror("Verbindung fehlgeschlagen", f"Fehler: {test}")
        return

    # Daten speichern
    config = {
        "host": host,
        "user": user,
        "password": password,
        "database": database,
        "inhaberid": inhaberid,
        "inhaber": inhaber
    }

    users = {
        adminuser: md5_hash(adminpass)
    }

    try:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)

        messagebox.showinfo("Fertig", "Setup abgeschlossen! Die Daten wurden gespeichert.")
        fenster.destroy()
    except Exception as e:
        messagebox.showerror("Fehler beim Speichern", str(e))

# GUI Fenster
fenster = tk.Tk()
fenster.title("📦 Setup-Assistent")

# Layout
labels = [
    "MySQL Host:", "MySQL Benutzer:", "MySQL Passwort:",
    "MySQL Datenbank:", "Inhaber ID:", "Inhaber Name:",
    "Admin Benutzername:", "Admin Passwort:"
]
entries = []

for i, text in enumerate(labels):
    tk.Label(fenster, text=text).grid(row=i, column=0, sticky="e", padx=5, pady=2)

ein_host = tk.Entry(fenster)
ein_user = tk.Entry(fenster)
ein_pass = tk.Entry(fenster, show="*")
ein_db = tk.Entry(fenster)
ein_inhaberid = tk.Entry(fenster)
ein_inhaber = tk.Entry(fenster)
ein_adminuser = tk.Entry(fenster)
ein_adminpass = tk.Entry(fenster, show="*")

ein_host.grid(row=0, column=1)
ein_user.grid(row=1, column=1)
ein_pass.grid(row=2, column=1)
ein_db.grid(row=3, column=1)
ein_inhaberid.grid(row=4, column=1)
ein_inhaber.grid(row=5, column=1)
ein_adminuser.grid(row=6, column=1)
ein_adminpass.grid(row=7, column=1)

# Button
tk.Button(fenster, text="ℹ️ Mehr Informationen", command=offne_info).grid(row=16, column=0, columnspan=3, pady=10)
tk.Button(fenster, text="💾 Setup speichern", command=setup_speichern).grid(row=8, column=0, columnspan=2, pady=10)

fenster.mainloop()

