import json
import os
import random
import string
import hashlib
import mysql.connector
import tkinter as tk
from tkinter import messagebox, ttk
import requests
import webbrowser
from PIL import Image, ImageTk
from io import BytesIO

# Felder für Eingabeformular
felder = [
    "DBid", "Name", "Band", "Doppelband", "ISBN10", "ISBN13",
    "Preis", "Typ", "Verlag", "BilderUrl", "Standort", "Zustand"
]

# Dropdown-Optionen
doppelband_optionen = ["Ja", "Nein"]
typ_optionen = [
    "Manga", "Anime", "Comics", "Buch", "AnimeComics", "CD",
    "Schallplatte", "DVD", "VHS", "Blu-Ray", "Spiele"
]
zustand_optionen = ["Sehr Gut", "Gut", "Mittel", "Schlecht", "Sehr Schlecht"]

eintraege = {}
status_label = None
baum = None
such_eintrag = None

def google_books_isbn_suche():
    isbn = eintraege["ISBN13"].get() or eintraege["ISBN10"].get()
    if not isbn:
        status_label.config(text="❌ Bitte eine ISBN eingeben, um zu suchen!", fg="red")
        return

    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data['totalItems'] > 0:
            item = data['items'][0]['volumeInfo']
            
            # Felder mit den API-Daten befüllen
            titel = item.get('title', '')
            verlag = item.get('publisher', '')
            bilder_url = item['imageLinks']['thumbnail'] if 'imageLinks' in item and 'thumbnail' in item['imageLinks'] else ''

            eintraege["Name"].delete(0, tk.END)
            eintraege["Name"].insert(0, titel)

            eintraege["Verlag"].delete(0, tk.END)
            eintraege["Verlag"].insert(0, verlag)
            
            eintraege["BilderUrl"].delete(0, tk.END)
            eintraege["BilderUrl"].insert(0, bilder_url)

            status_label.config(text="✅ Metadaten erfolgreich von Google Books geladen!", fg="green")
        else:
            status_label.config(text="❌ Keine Ergebnisse für diese ISBN gefunden.", fg="red")

    except requests.exceptions.RequestException as e:
        status_label.config(text=f"❌ Fehler bei der API-Anfrage: {str(e)}", fg="red")
    except KeyError:
        status_label.config(text="❌ Fehler beim Parsen der API-Antwort. Daten unvollständig.", fg="red")


# ================= Update-Funktion =================
def check_for_updates():
    try:
        # Die URLs zu deinen Dateien
        version_url = "https://ddl.buch-archiv20-software.de/update/py/version.txt"
        download_url = "https://ddl.buch-archiv20-software.de/update/py/BuchArchiv_Update.zip"

        response = requests.get(version_url)
        response.raise_for_status()  # Löst einen Fehler aus, wenn der Download fehlschlägt

        remote_version = response.text.strip()
        local_version = "1.0.0"  # Hier die aktuelle lokale Version eintragen

        if remote_version > local_version:
            # Zeigt ein Fenster an, das über das Update informiert und den Download-Link bietet
            result = messagebox.askyesno(
                "Update verfügbar",
                f"Eine neue Version ({remote_version}) ist verfügbar. Möchten Sie sie herunterladen?"
            )
            if result:
                webbrowser.open(download_url) # Öffnet den Download-Link im Standardbrowser
                messagebox.showinfo(
                    "Download gestartet",
                    "Der Download sollte jetzt in Ihrem Browser starten. Bitte ersetzen Sie die alten Dateien mit den neuen aus der ZIP-Datei."
                )
        else:
            messagebox.showinfo("Kein Update", "Du hast bereits die neueste Version.")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Update-Fehler", f"Fehler beim Überprüfen auf Updates: {e}")


def zeige_details(event):
    selected_item = baum.selection()
    if not selected_item:
        return

    item_werte = baum.item(selected_item, "values")
    dbid_wert = item_werte[0]

    detail_daten = hole_vollstaendige_daten(dbid_wert)
    if not detail_daten:
        messagebox.showerror("Fehler", "Detaildaten konnten nicht geladen werden.")
        return

    details_fenster = tk.Toplevel()
    details_fenster.title(f"Details für: {detail_daten.get('name', 'N/A')}")
    details_fenster.geometry("600x400")
    details_fenster.configure(bg="#f0f0f0")

    main_frame = tk.Frame(details_fenster, bg="#f0f0f0", padx=10, pady=10)
    main_frame.pack(fill="both", expand=True)

    # Bildbereich
    bild_frame = tk.Frame(main_frame, bg="#f0f0f0")
    bild_frame.pack(side="left", padx=10)

    bild_label = tk.Label(bild_frame, bg="#f0f0f0")
    bild_label.pack()

    bilder_url = detail_daten.get("bildurl")
    if bilder_url and bilder_url.strip():
        try:
            response = requests.get(bilder_url, timeout=10)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img.thumbnail((200, 300))
            photo = ImageTk.PhotoImage(img)

            bild_label.config(image=photo)
            bild_label.image = photo
        except Exception as e:
            bild_label.config(text="Bild konnte nicht geladen werden", width=20, height=15, relief="solid", borderwidth=1)
            print(f"Fehler beim Laden des Bildes: {e}")
    else:
        bild_label.config(text="Kein Bild verfügbar", width=20, height=15, relief="solid", borderwidth=1)

    # Detailbereich
    info_frame = tk.Frame(main_frame, bg="#f0f0f0")
    info_frame.pack(side="left", padx=10, fill="both", expand=True)

    # Titel mit grid statt pack
    tk.Label(info_frame, text=detail_daten.get('name', 'N/A'), font=("Helvetica", 16, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

    detail_labels = [
        ("DBid:", 'dbid'),
        ("Inhaber:", 'inhaber'),
        ("Band:", 'band'),
        ("Doppelband:", 'doppelband'),
        ("ISBN10:", 'isbn10'),
        ("ISBN13:", 'isbn13'),
        ("Preis:", 'preis'),
        ("Typ:", 'typ'),
        ("Verlag:", 'verlag'),
        ("Standort:", 'standort'),
        ("Zustand:", 'zusand'),
    ]

    for i, (label_text, key) in enumerate(detail_labels):
        value_text = detail_daten.get(key, 'N/A')
        if key == 'preis':
            try:
                value_text = f"{float(value_text):.2f} €"
            except (ValueError, TypeError):
                value_text = 'N/A'

        tk.Label(info_frame, text=label_text, font=("Helvetica", 10, "bold"), bg="#f0f0f0").grid(row=i + 1, column=0, sticky="w", pady=1)
        tk.Label(info_frame, text=value_text, font=("Helvetica", 10), bg="#f0f0f0").grid(row=i + 1, column=1, sticky="w", padx=10, pady=1)



# ================= Hilfsfunktionen =================
def lade_config():
    with open("config.json", "r") as file:
        return json.load(file)

def lade_user():
    with open("users.json", "r") as file:
        return json.load(file)

def md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def generiere_dbid(length=16):
    zeichen = string.ascii_uppercase + string.digits
    return ''.join(random.choices(zeichen, k=length))

def neue_dbid():
    neue_id = generiere_dbid()
    eintraege["DBid"].delete(0, tk.END)
    eintraege["DBid"].insert(0, neue_id)
    status_label.config(text=f"ℹ️ Neue DBid generiert: {neue_id}", fg="blue")

def daten_in_db_speichern(daten):
    config = lade_config()
    conn = mysql.connector.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database=config["database"]
    )
    cursor = conn.cursor()

    sql = """
    INSERT INTO media (
        dbid, inhaberid, inhaber, name, band, doppelband, isbn10,
        isbn13, preis, typ, verlag, bildurl, standort, zusand
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    werte = (
        daten["DBid"], config["inhaberid"], config["inhaber"], daten["Name"],
        daten["Band"], daten["Doppelband"], daten["ISBN10"], daten["ISBN13"],
        daten["Preis"], daten["Typ"], daten["Verlag"], daten["BilderUrl"],
        daten["Standort"], daten["Zustand"]
    )
    cursor.execute(sql, werte)
    conn.commit()
    cursor.close()
    conn.close()

def suche_daten(suchbegriff):
    config = lade_config()
    conn = mysql.connector.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database=config["database"]
    )
    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT * FROM media
    WHERE name LIKE %s OR isbn10 LIKE %s OR isbn13 LIKE %s OR dbid LIKE %s
    """
    like = f"%{suchbegriff}%"
    cursor.execute(sql, (like, like, like, like))
    ergebnisse = cursor.fetchall()
    cursor.close()
    conn.close()
    return ergebnisse

def hole_vollstaendige_daten(dbid):
    config = lade_config()
    conn = mysql.connector.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database=config["database"]
    )
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM media WHERE dbid = %s"
    cursor.execute(sql, (dbid,))
    ergebnis = cursor.fetchone()

    cursor.close()
    conn.close()
    return ergebnis
# ================= GUI =================
def speichern():
    daten = {}
    for feld in felder:
        if feld == "DBid":
            if not eintraege[feld].get():
                daten[feld] = generiere_dbid()
                eintraege[feld].insert(0, daten[feld])
            else:
                daten[feld] = eintraege[feld].get()
        else:
            daten[feld] = eintraege[feld].get()

    try:
        daten_in_db_speichern(daten)
        for widget in eintraege.values():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
            elif isinstance(widget, ttk.Combobox):
                widget.set("")
        status_label.config(text="✅ Buch wurde erfolgreich gespeichert!", fg="green")
    except Exception as e:
        status_label.config(text=f"❌ Fehler beim Speichern: {str(e)}", fg="red")

def suche():
    global baum
    suchbegriff = such_eintrag.get()
    ergebnisse = suche_daten(suchbegriff)

    for row in baum.get_children():
        baum.delete(row)

    for eintrag in ergebnisse:
#dbid, inhaberid, inhaber, name, band, doppelband, isbn10,isbn13, preis, typ, verlag, bildurl, standort, zusand
#"DBid","Inhaber" "Name", "ISBN10", "ISBN13", "Preis", "Typ", "Standort", "Zustand"
        werte = [eintrag.get(f, "") for f in ["dbid","inhaber", "name", "band", "isbn10", "isbn13", "preis", "typ", "standort", "zusand"]]
        baum.insert("", "end", values=werte)
    status_label.config(text=f"i Suche Nach: {suchbegriff}", fg="violet")

def zeige_hauptfenster():
    global eintraege, status_label, baum, such_eintrag

    hauptfenster = tk.Tk()
    hauptfenster.title("📚 Bücherei 2.0 Online ~Python Versaion~")

    for i, feld in enumerate(felder):
        tk.Label(hauptfenster, text=feld).grid(row=i, column=0, sticky="e")

        if feld == "Doppelband":
            cb = ttk.Combobox(hauptfenster, values=doppelband_optionen, state="readonly")
            cb.grid(row=i, column=1)
            eintraege[feld] = cb

        elif feld == "Typ":
            cb = ttk.Combobox(hauptfenster, values=typ_optionen, state="readonly")
            cb.grid(row=i, column=1)
            eintraege[feld] = cb

        elif feld == "Zustand":
            cb = ttk.Combobox(hauptfenster, values=zustand_optionen, state="readonly")
            cb.grid(row=i, column=1)
            eintraege[feld] = cb

        elif feld == "DBid":
            eintrag = tk.Entry(hauptfenster, width=30)
            eintrag.grid(row=i, column=1, sticky="w")
            tk.Button(hauptfenster, text="Neue DBid", command=neue_dbid).grid(row=i, column=2, padx=5)
            eintraege[feld] = eintrag
            
        elif feld == "ISBN13":
            eintrag = tk.Entry(hauptfenster, width=30)
            eintrag.grid(row=i, column=1, sticky="w")
            # Neuer Button für die API-Suche
            tk.Button(hauptfenster, text="ISBN suchen", command=google_books_isbn_suche).grid(row=i, column=2, padx=5)
            eintraege[feld] = eintrag

        else:
            eintrag = tk.Entry(hauptfenster, width=40)
            eintrag.grid(row=i, column=1)
            eintraege[feld] = eintrag

    tk.Button(hauptfenster, text="💾 Speichern", command=speichern).grid(row=len(felder), column=0, columnspan=2, pady=10)
    tk.Button(hauptfenster, text="🔄 Nach Updates suchen", command=check_for_updates).grid(row=len(felder), column=2, padx=10, pady=10)
    #column=2, padx=10, pady=10)
    
    # Suchbereich
    tk.Label(hauptfenster, text="🔍 Suche (Name oder ISBN10 oder ISBN13 oder DBID)").grid(row=0, column=3, padx=10, sticky="w")
    such_eintrag = tk.Entry(hauptfenster)
    such_eintrag.grid(row=1, column=3, padx=10)
    tk.Button(hauptfenster, text="Suchen", command=suche).grid(row=2, column=3, padx=10)

    # Ergebnis-Tabelle
    #dbid, inhaberid, inhaber, name, band, doppelband, isbn10,isbn13, preis, typ, verlag, bildurl, standort, zusand
    baum = ttk.Treeview(hauptfenster, columns=("DBid","Inhaber", "Name", "Band", "ISBN10", "ISBN13", "Preis", "Typ", "Standort", "Zustand"), show="headings")
    for col in baum["columns"]:
        baum.heading(col, text=col)
        baum.column(col, width=120)
    baum.grid(row=3, column=3, rowspan=10, padx=10, pady=5)
    baum.bind("<Double-1>", zeige_details)

    # Statusfeld
    status_label = tk.Label(hauptfenster, text="ℹ️ Bereit", anchor="w", fg="gray")
    status_label.grid(row=len(felder)+1, column=0, columnspan=4, sticky="we", padx=5, pady=5)

    hauptfenster.mainloop()

# ================= Login =================

def login():
    benutzer = eintrag_benutzer.get()
    passwort = eintrag_passwort.get()
    users = lade_user()

    passwort_hash = md5_hash(passwort)

    if benutzer in users and users[benutzer] == passwort_hash:
        login_fenster.destroy()
        zeige_hauptfenster()
    else:
        messagebox.showerror("Fehler", "Login fehlgeschlagen!")

# ================= Login-Fenster =================
if not os.path.exists("config.json") or not os.path.exists("users.json"):
    import subprocess
    subprocess.call(["python3", "setup.py"])

login_fenster = tk.Tk()
login_fenster.title("🔐 Login")
login_fenster.geometry("450x300") # Angepasste Größe für Logo und Inhalt

# Logo laden und anzeigen
try:
    img = Image.open("logo.png")
    img = img.resize((295, 150), Image.Resampling.LANCZOS) # Größe anpassen
    photo = ImageTk.PhotoImage(img)
    logo_label = tk.Label(login_fenster, image=photo)
    logo_label.image = photo # Referenz behalten
    logo_label.pack(pady=10)
except FileNotFoundError:
    tk.Label(login_fenster, text="Logo nicht gefunden!", fg="red").pack(pady=10)

# Frame für die Login-Eingaben
login_frame = tk.Frame(login_fenster)
login_frame.pack(pady=10)

tk.Label(login_frame, text="Benutzername").grid(row=0, column=0, pady=5)
tk.Label(login_frame, text="Passwort").grid(row=1, column=0, pady=5)

eintrag_benutzer = tk.Entry(login_frame)
eintrag_passwort = tk.Entry(login_frame, show="*")

eintrag_benutzer.grid(row=0, column=1, pady=5, padx=5)
eintrag_passwort.grid(row=1, column=1, pady=5, padx=5)

tk.Button(login_fenster, text="Login", command=login).pack(pady=10)

login_fenster.mainloop()

