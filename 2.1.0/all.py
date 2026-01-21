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
import io
import platform


# Optional: Import für VLC (muss separat installiert werden: pip install python-vlc)
try:
    import vlc
except ImportError:
    vlc = None
    print("VLC-Bibliothek (python-vlc) nicht gefunden. Die Abspielfunktion funktioniert nicht.")

# ==============================================================================
# GLOBALE KONSTANTEN
# ==============================================================================

# --- Artikel-Modul Globale Konstanten ---
ARTIKEL_FELDER = [
    "DBid", "Name", "Band", "Doppelband", "ISBN10", "ISBN13",
    "Preis", "Typ", "Verlag", "BilderUrl", "Standort", "Zustand"
]
ARTIKEL_DOPPELBAND_OPTIONEN = ["Ja", "Nein"]
ARTIKEL_TYP_OPTIONEN = [
    "Manga", "Anime", "Comics", "Buch", "eBook", "AnimeComics", "CD",
    "Schallplatte", "DVD", "VHS", "Blu-Ray", "Spiele"
]
ARTIKEL_ZUSTAND_OPTIONEN = ["Sehr Gut", "Gut", "Mittel", "Schlecht", "Sehr Schlecht"]

# --- Anime-Modul Globale Konstanten ---
AFSS_FIELDS = [
    "AFSSID", "Titel", "Episoden", "Anzahl Episoden", "Cover URL",
    "Untertitel Sprache", "Audio Sprache", "Lokale Playlist", "Online Playlist",
    "Medium", "Fansub Name", "Fansub URL"
]
AFSS_MEDIUM_OPTIONS = ["Online", "DVD", "VHS", "Datei (Auf PC)", "Blu-Ray"]

status_label = None # Wird global in zeige_hauptfenster gesetzt
# --- NEUE KONSTANTEN FÜR FILME & SERIEN ---
FILM_TYP_OPTIONEN = ["Film", "Serie"]
FILM_FORMAT_OPTIONEN = ["DVD", "Blu-ray", "4K UHD", "Digital", "VHS"]

# -------------------- HILFSFUNKTIONEN --------------------

def md5_hash(text):
    """Erzeugt einen MD5-Hash des übergebenen Textes."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def generiere_dbid(length=16):
    """Generiert eine zufällige ID für neue Einträge."""
    zeichen = string.ascii_uppercase + string.digits
    return ''.join(random.choices(zeichen, k=length))

def lade_config(dateiname):
    """Lädt eine JSON-Datei anhand des übergebenen Dateinamens."""
    try:
        with open(dateiname, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Konfigurationsdatei '{dateiname}' wurde nicht gefunden.")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Die Datei '{dateiname}' ist keine gültige JSON-Datei.")
        return {}

def speichere_config(dateiname, config_data):
    """Speichert Daten in eine JSON-Datei."""
    try:
        with open(dateiname, 'w') as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception as e:
        print(f"❌ Fehler beim Speichern von '{dateiname}': {e}")
        return False

def save_users_json(users_data):
    """Speichert die Benutzerdaten in users.json."""
    return speichere_config("users.json", users_data)

# -------------------- STATISTIK FUNKTION (AKTUALISIERT MIT MEHR DEBUGGING) --------------------

def send_statistics():
    """Sammelt Systemdaten, inkrementiert den Zähler und sendet die Statistik."""

    # NEU: Lade Statistik-Konfiguration aus progPen.json
    stats_config = lade_config("progPen.json")

    # 1. Zähler inkrementieren und speichern
    open_count = stats_config.get("open_count", 0) + 1
    stats_config["open_count"] = open_count

    # Speichern des aktualisierten Zählers in progPen.json
    speichere_config("progPen.json", stats_config)

    stats_url = stats_config.get("STATISTICS_URL", None)

    if not stats_url:
        print("ℹ️ STATISTICS_URL fehlt in progPen.json. Statistik-Übertragung übersprungen.")
        return

    # 2. Daten sammeln
    current_os = platform.system() # Z.B. 'Linux', 'Windows', 'Darwin'

    # Externe IP-Adresse abrufen (API-Abruf)
    current_ip = "N/A"
    try:
        # Verwende einen einfachen, zuverlässigen Dienst
        ip_response = requests.get('https://api.ipify.org', timeout=5)
        if ip_response.status_code == 200:
            current_ip = ip_response.text.strip()
        else:
            current_ip = f"Error {ip_response.status_code}"
    except requests.RequestException:
        pass # Ignoriere Fehler, falls keine Internetverbindung oder Timeout

    # Hole den Benutzernamen aus config.json, falls vorhanden, sonst N/A
    config = lade_config("config.json")
    program_username = config.get("username", os.environ.get('USER', os.environ.get('USERNAME', 'unknown')))
    program_username_hashed = md5_hash(program_username)

    data = {
        "program_name": "Bücherei 2.0 Online",
        "open_count": open_count,
        "os": current_os,
        "ip_address": current_ip,
        "username": program_username_hashed
    }

    # 3. Senden mit erweitertem Debugging
    try:
        print(f"\nDEBUG: 📡 Sende Statistik an: {stats_url}")
        print(f"DEBUG: 📦 Gesendete Daten (JSON): {json.dumps(data, indent=2)}") # <-- WICHTIG: Payload-Inhalt

        response = requests.post(stats_url, json=data, timeout=10)

        print(f"DEBUG: 📶 HTTP-Statuscode: {response.status_code}") # <-- WICHTIG: Statuscode

        if response.status_code == 200:
            print(f"DEBUG: ✅ Statistik erfolgreich gesendet. Server-Antwort: {response.text}")
        elif 400 <= response.status_code < 500:
            print(f"DEBUG: ⚠️ Client-Fehler ({response.status_code}). URL oder Payload prüfen. Server-Antwort: {response.text}")
        else: # 5xx oder andere Statuscodes
            print(f"DEBUG: ❌ Server-Fehler ({response.status_code}). Server-Antwort: {response.text}")

    except requests.exceptions.Timeout:
        print(f"DEBUG: ❌ Timeout-Fehler: Die Anfrage an {stats_url} hat 10 Sekunden überschritten.")
    except requests.exceptions.ConnectionError as e:
        print(f"DEBUG: ❌ Verbindungsfehler: Konnte keine Verbindung zu {stats_url} herstellen. URL prüfen! Fehler: {e}")
    except requests.RequestException as e:
        print(f"DEBUG: ❌ Allgemeiner Fehler beim Senden der Statistik an {stats_url}: {e}")
    print("-" * 50) # Trennlinie für bessere Übersicht


# -------------------- DB-VERBINDUNGSFUNKTIONEN --------------------

def connect_db_artikel(db_config):
    """Versucht, eine MySQL-Datenbankverbindung herzustellen."""
    try:
        # DB-Config muss bereits geladen sein, z.B. mittels lade_config("db_config.json")
        conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        return conn
    except mysql.connector.Error as err:
        # Statt messagebox in der Funktion direkt, wird der Aufrufer informiert
        print(f"Datenbankverbindungsfehler: {err}")
        return None
    except KeyError as err:
        print(f"Konfigurationsfehler: Fehlender Schlüssel in db_config.json: {err}")
        return None

def fetch_user_details(username):
    """Lädt detaillierte Benutzerinformationen aus der DB für den Profil-Tab."""
    db_config = lade_config("db_config.json")
    if not db_config:
        return None

    try:
        conn = connect_db_artikel(db_config)
        if not conn: return None

        cursor = conn.cursor(dictionary=True)
        # Bezieht alle relevanten Informationen aus der 'user'-Tabelle
        sql = "SELECT inhaberID, Name, email, license_tier, securityKEY FROM user WHERE username = %s"
        cursor.execute(sql, (username,))
        details = cursor.fetchone()
        cursor.close()
        conn.close()
        return details
    except Exception as e:
        print(f"Fehler beim Laden der Benutzerdetails: {e}")
        return None


# ==============================================================================
# MODUL-KLASSEN
# ==============================================================================

# -------------------- PLAYER MODUL --------------------

class PlayerModul:
    """Zeigt ein separates Fenster zur lokalen Medienwiedergabe."""
    def __init__(self, master, playlist_path):
        self.master = master
        self.master.title("🎬 Wiedergabe")
        self.master.geometry("350x200")
        self.playlist_path = playlist_path

        tk.Label(master, text="Playlist Wiedergabe", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(master, text=f"Quelle: {os.path.basename(playlist_path)}", wraplength=300).pack(pady=5)

        tk.Button(master, text="▶️ Mit VLC abspielen", command=self.play_with_vlc).pack(pady=5, fill="x", padx=20)
        tk.Button(master, text="📺 Über Plex/Standard-Player starten", command=self.play_with_plex).pack(pady=5, fill="x", padx=20)

    def play_with_vlc(self):
        if vlc is None:
             messagebox.showerror("Fehler", "Die python-vlc Bibliothek ist nicht installiert (pip install python-vlc).")
             return

        try:
            # Annahme: Lokale Pfade, die VLC lesen kann.
            instance = vlc.Instance()
            player = instance.media_player_new()
            media = instance.media_new(self.playlist_path)
            player.set_media(media)
            player.play()
            print(f"VLC Wiedergabe gestartet: {self.playlist_path}")

        except Exception as e:
            messagebox.showerror("Fehler", f"VLC-Wiedergabe fehlgeschlagen: {e}")

    def play_with_plex(self):
        # Versucht, den lokalen Pfad im Standard-Browser zu öffnen.
        playlist_url = f"file:///{os.path.abspath(self.playlist_path)}"
        webbrowser.open(playlist_url)
        messagebox.showinfo("Startbefehl", "Externer Startbefehl gesendet. Prüfen Sie Ihren Standard-Player/Browser.")

# -------------------- BENUTZER PROFIL MODUL (AKTUALISIERT FÜR progPen.json) --------------------

class UserInfoModul:
    """Der 'Mein Profil'-Tab zur Anzeige von Benutzer- und Systeminformationen."""
    def __init__(self, master, username):
        self.frame = ttk.Frame(master)
        self.username = username
        self.user_details = fetch_user_details(username)
        # progPen Konfiguration laden (für Links/Update)
        self.progpen_config = lade_config("progPen.json")
        self.create_widgets()

    def create_widgets(self):
        # Titel
        tk.Label(self.frame, text="Mein Profil & System", font=("Arial", 16, "bold")).pack(pady=15)

        # Statistik-Anzeige
        stats_config = lade_config("progPen.json")
        open_count = stats_config.get("open_count", 1)
        tk.Label(self.frame, text=f"Statistik: Programm wurde {open_count} Mal geöffnet.", fg="purple", font=("Arial", 10)).pack(pady=5)
        tk.Label(self.frame, text=f"Betriebssystem: {platform.system()}", fg="purple", font=("Arial", 10)).pack(pady=2)

        if not self.user_details:
            tk.Label(self.frame, text="⚠️ Benutzerdetails konnten nicht geladen werden.", fg="red").pack(pady=20)
            return

        # 1. Benutzerinformationen Frame
        info_frame = tk.LabelFrame(self.frame, text="Persönliche Daten & Schlüssel", padx=20, pady=10)
        info_frame.pack(pady=10, padx=20, fill="x")

        # Hinweis: Achte auf die Groß/Kleinschreibung der Keys (inhaberID vs InhaberID)
        data = {
            "Benutzername": self.username,
            "Inhaber-Name": self.user_details.get("Name", "N/A"),
            "InhaberID": self.user_details.get("InhaberID") or self.user_details.get("inhaberID", "N/A"),
            "E-Mail": self.user_details.get("email", "N/A"),
            "Lizenz-Status": self.user_details.get("license_tier", "FREE"),
            "Sicherheitsschlüssel (Key)": self.user_details.get("securityKEY", "Kein Key")
        }

        for i, (key, value) in enumerate(data.items()):
            tk.Label(info_frame, text=f"{key}:", anchor="w", width=30).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            tk.Label(info_frame, text=value, anchor="w", fg="blue").grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # --- HIER IST DER BUTTON FÜR DIE KONTOVERWALTUNG ---
        tk.Button(info_frame,
                  text="⚙️ Konto online verwalten / Passwort ändern",
                  command=lambda: webbrowser.open("https://anmeldung.buch-archiv20-software.de/dashboard.php"),
                  bg="#4285F4", fg="white", font=("Arial", 9, "bold")).grid(row=len(data), column=0, columnspan=2, pady=10)

        # 2. Aktionen & Links Frame
        actions_frame = tk.LabelFrame(self.frame, text="System & Links", padx=20, pady=10)
        actions_frame.pack(pady=10, padx=20, fill="x")

        links = self.progpen_config.get("PROGRAMM_LINKS", {})
        update_config = self.progpen_config.get("UPDATE_CONFIG", {})
        local_version = update_config.get("LOCAL_VERSION", "N/A")

        tk.Label(actions_frame, text=f"Installierte Version: {local_version}", font=("Arial", 10)).pack(pady=5)

        # Buttons für Links
        link_buttons = [
            ("🌐 Programm Webseite", "WEBSITE"),
            ("💬 Forum / Kontakt", "FORUM"),
            ("🔗 Support Formular", "SUPPORT_FORMULAR"),
            ("🐈 GitHub Repo", "GITHUB_REPO")
        ]

        for text, key in link_buttons:
            tk.Button(actions_frame, text=text,
                      command=lambda k=key: webbrowser.open(links.get(k, "about:blank"))).pack(pady=3, fill="x", padx=10)

        # Update Button
        tk.Button(actions_frame, text="⬆️ Update Prüfen (Udane Batte)",
                  command=self.check_for_update, bg="orange").pack(pady=10, fill="x", padx=10)

    def check_for_update(self):
        """Prüft auf Updates und startet bei Ja den Auto-Installer."""
        # 1. Konfiguration laden
        update_config = self.progpen_config.get("UPDATE_CONFIG", {})
        local_version = update_config.get("LOCAL_VERSION", "2.1.0")
        # Deine feste API-URL
        update_url = "https://buch-archiv20-software.de/api/check_version.php"

        # Status-Anzeige (versucht self.status_label zu nutzen)
        label = getattr(self, 'status_label', None)
        if label: label.config(text="ℹ️ Prüfe auf Updates...", fg="orange")

        try:
            # 2. Server abfragen
            response = requests.get(update_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            latest_version = data.get("latest_version")
            download_url = data.get("download_url") # Muss ein Link zu einer .zip sein!

            # Versions-Vergleichs-Logik
            def parse_v(v): return tuple(map(int, str(v).split('.')))

            if parse_v(latest_version) > parse_v(local_version):
                if label: label.config(text=f"🚀 Update {latest_version} verfügbar!", fg="red")

                msg = f"Aktuelle Version: {local_version}\nNeue Version: {latest_version}\n\nMöchten Sie das Update jetzt automatisch installieren?"
                if messagebox.askyesno("Update verfügbar!", msg):
                    # STARTE AUTO-UPDATE
                    self.perform_auto_update(download_url)
            else:
                if label: label.config(text=f"✅ Version {local_version} ist aktuell.", fg="green")
                messagebox.showinfo("Aktuell", f"Deine Version ({local_version}) ist die neueste.")

        except Exception as e:
            if label: label.config(text="❌ Fehler beim Update-Check.", fg="red")
            messagebox.showerror("Fehler", f"Update-Check fehlgeschlagen: {e}")

    def perform_auto_update(self, download_url):
        """Lädt die ZIP herunter und entpackt sie."""
        try:
            import zipfile, shutil, subprocess

            # 1. ZIP herunterladen
            zip_file = "update_package.zip"
            r = requests.get(download_url, stream=True)
            with open(zip_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 2. Entpacken in temporären Ordner
            temp_dir = "update_temp"
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)

            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # 3. Externes Updater-Skript erstellen (tauscht Dateien aus während App zu ist)
            self.create_updater_script(temp_dir)

            messagebox.showinfo("Installation", "Update geladen! Das Programm wird nun beendet und installiert das Update. Bitte warten Sie kurz.")

            # 4. Updater starten und App schließen
            if platform.system() == "Windows":
                subprocess.Popen(["cmd", "/c", "updater.bat"], shell=True)
            else:
                subprocess.Popen(["sh", "updater.sh"])

            sys.exit() # Beendet all.py

        except Exception as e:
            messagebox.showerror("Update fehlgeschlagen", f"Fehler während der Installation: {e}")

    def create_updater_script(self, source):
        """Erstellt die Batch/Shell Datei für den Dateitausch."""
        if platform.system() == "Windows":
            with open("updater.bat", "w") as f:
                f.write(f"@echo off\n")
                f.write(f"timeout /t 2 /nobreak > nul\n") # Warten bis App zu ist
                f.write(f"xcopy /s /y \"{source}\\*\" \".\"\n") # Dateien überschreiben
                f.write(f"rd /s /q \"{source}\"\n") # Aufräumen
                f.write(f"del \"update_package.zip\"\n")
                f.write(f"start python all.py\n") # Neustart
                f.write(f"del \"%~f0\"\n")
        else:
            with open("updater.sh", "w") as f:
                f.write(f"#!/bin/bash\nsleep 2\ncp -r {source}/* .\n")
                f.write(f"rm -rf {source} update_package.zip\npython3 all.py &\nrm -- \"$0\"\n")

# -------------------- ARTIKEL MODUL (MEDIENVERWALTUNG) --------------------

class ArtikelModul(tk.Frame):
    """ Artikel-Verwaltungsmodul (Ursprünglicher Inhalt von main.py). """
    def __init__(self, master):
        super().__init__(master)
        self.eintraege = {}
        self.status_label = None
        self.baum = None
        self.such_eintrag = None
        # Verwende master.winfo_toplevel() als top-level-master für die Dialoge
        self.main_master = master.winfo_toplevel()
        self.create_widgets()

    # --- DB Funktionen des Artikel-Moduls ---
    def connect_db_artikel(self, config):
        # Stellt Verbindung zur Artikel-DB her (verwendet db_config)
        return connect_db_artikel(config) # Nutzt die globale Funktion

    def daten_in_db_speichern(self, daten):
        # 1. Konfiguration laden, um Inhaber-Daten zu bekommen
        config = lade_config("config.json")
        if not config or "inhaberid" not in config:
             raise Exception("Fehlende Inhaber-ID in config.json. Bitte setup.py erneut ausführen.")

        # 2. DB-Verbindung
        db_config = lade_config("db_config.json")
        conn = self.connect_db_artikel(db_config)
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

    def suche_daten(self, suchbegriff):
        db_config = lade_config("db_config.json")
        conn = self.connect_db_artikel(db_config)
        cursor = conn.cursor(dictionary=True)

        # Die Spalten für die erweiterte Anzeige in der Treeview
        sql = """
        SELECT dbid, inhaber, name, band, isbn10, isbn13, preis, typ, verlag, standort, zusand FROM media
        WHERE name LIKE %s OR isbn10 LIKE %s OR isbn13 LIKE %s OR dbid LIKE %s
        """
        like = f"%{suchbegriff}%"
        cursor.execute(sql, (like, like, like, like))
        ergebnisse = cursor.fetchall()
        cursor.close()
        conn.close()
        return ergebnisse

    def hole_vollstaendige_daten(self, dbid):
        db_config = lade_config("db_config.json")
        conn = self.connect_db_artikel(db_config)
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM media WHERE dbid = %s"
        cursor.execute(sql, (dbid,))
        ergebnis = cursor.fetchone()

        cursor.close()
        conn.close()
        return ergebnis

    # --- Modul-Funktionen ---
    def neue_dbid(self):
        neue_id = generiere_dbid()
        self.eintraege["DBid"].delete(0, tk.END)
        self.eintraege["DBid"].insert(0, neue_id)
        if self.status_label: # Sicherstellen, dass das Label existiert
             self.status_label.config(text=f"ℹ️ Neue DBid generiert: {neue_id}", fg="blue")

    def google_books_isbn_suche(self):
        # ... (Logik wie zuvor) ...
        isbn = self.eintraege["ISBN13"].get() or self.eintraege["ISBN10"].get()
        if not isbn:
            self.status_label.config(text="❌ Bitte eine ISBN eingeben, um zu suchen!", fg="red")
            return

        try:
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get('totalItems', 0) > 0:
                item = data['items'][0]['volumeInfo']

                titel = item.get('title', '')
                verlag = item.get('publisher', '')
                bilder_url = item.get('imageLinks', {}).get('thumbnail', '')

                self.eintraege["Name"].delete(0, tk.END)
                self.eintraege["Name"].insert(0, titel)

                self.eintraege["Verlag"].delete(0, tk.END)
                self.eintraege["Verlag"].insert(0, verlag)

                self.eintraege["BilderUrl"].delete(0, tk.END)
                self.eintraege["BilderUrl"].insert(0, bilder_url)

                self.status_label.config(text="✅ Metadaten erfolgreich von Google Books geladen!", fg="green")
            else:
                self.status_label.config(text="❌ Keine Ergebnisse für diese ISBN gefunden.", fg="red")

        except requests.exceptions.RequestException as e:
            self.status_label.config(text=f"❌ Fehler bei der API-Anfrage: {str(e)}", fg="red")
        except KeyError:
            self.status_label.config(text="❌ Fehler beim Parsen der API-Antwort. Daten unvollständig.", fg="red")


    def speichern(self):
        daten = {}
        for feld in ARTIKEL_FELDER:
            if feld == "DBid":
                if not self.eintraege[feld].get():
                    daten[feld] = generiere_dbid()
                    self.eintraege[feld].insert(0, daten[feld])
                else:
                    daten[feld] = self.eintraege[feld].get()
            else:
                daten[feld] = self.eintraege[feld].get()

        try:
            self.daten_in_db_speichern(daten)
            # Eingabefelder leeren
            for widget in self.eintraege.values():
                if isinstance(widget, tk.Entry):
                    widget.delete(0, tk.END)
                elif isinstance(widget, ttk.Combobox):
                    widget.set("")
            self.status_label.config(text="✅ Artikel wurde erfolgreich gespeichert!", fg="green")
            self.neue_dbid() # Neue ID für den nächsten Eintrag generieren
        except Exception as e:
            self.status_label.config(text=f"❌ Fehler beim Speichern: {str(e)}", fg="red")

    def suche(self):
        suchbegriff = self.such_eintrag.get()
        ergebnisse = self.suche_daten(suchbegriff)

        for row in self.baum.get_children():
            self.baum.delete(row)

        # Erweitert um "Verlag"
        artikel_cols = ["dbid","inhaber", "name", "band", "isbn10", "isbn13", "preis", "typ", "verlag", "standort", "zusand"]

        for eintrag in ergebnisse:
            werte = [eintrag.get(f, "") for f in artikel_cols]
            self.baum.insert("", "end", values=werte)
        self.status_label.config(text=f"i Suche Nach: {suchbegriff}", fg="violet")

    def zeige_details(self, event):
        # ... (Logik wie zuvor) ...
        selected_item = self.baum.selection()
        if not selected_item: return

        item_werte = self.baum.item(selected_item, "values")
        dbid_wert = item_werte[0]

        detail_daten = self.hole_vollstaendige_daten(dbid_wert)
        if not detail_daten:
            messagebox.showerror("Fehler", "Detaildaten konnten nicht geladen werden.")
            return

        # Details-Fenster erstellen
        details_fenster = tk.Toplevel(self.main_master)
        details_fenster.title(f"Details für: {detail_daten.get('name', 'N/A')}")
        details_fenster.geometry("600x400")
        details_fenster.configure(bg="#f0f0f0")

        main_frame = tk.Frame(details_fenster, bg="#f0f0f0", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # Bildbereich (links)
        bild_frame = tk.Frame(main_frame, bg="#f0f0f0")
        bild_frame.pack(side="left", padx=10)
        bild_label = tk.Label(bild_frame, bg="#f0f0f0")
        bild_label.pack()

        # Detailbereich (rechts)
        info_frame = tk.Frame(main_frame, bg="#f0f0f0")
        info_frame.pack(side="left", padx=10, fill="both", expand=True)
        tk.Label(info_frame, text=detail_daten.get('name', 'N/A'), font=("Helvetica", 16, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Beispiel für Detailanzeige
        details_liste = ["inhaber", "band", "typ", "verlag", "standort", "zustand", "isbn10", "isbn13", "preis"]
        for i, key in enumerate(details_liste):
            tk.Label(info_frame, text=f"{key.capitalize()}:", anchor="w", bg="#f0f0f0").grid(row=i+1, column=0, sticky="w", padx=5, pady=2)
            tk.Label(info_frame, text=detail_daten.get(key, 'N/A'), anchor="w", fg="blue", bg="#f0f0f0").grid(row=i+1, column=1, sticky="w", padx=5, pady=2)

        details_fenster.mainloop()


    def create_widgets(self):
        # Das Frame wird in zwei Hauptbereiche unterteilt: Eingabe (links) und Suche/Ergebnisse (rechts)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        input_frame_container = tk.Frame(self, padx=10, pady=10, relief=tk.GROOVE, bd=2)
        input_frame_container.grid(row=0, column=0, sticky="nsew")

        search_frame_container = tk.Frame(self, padx=10, pady=10, relief=tk.GROOVE, bd=2)
        search_frame_container.grid(row=0, column=1, sticky="nsew")

        # --- Eingabebereich (links) ---
        input_frame = tk.Frame(input_frame_container)
        input_frame.pack(padx=5, pady=5)

        for i, feld in enumerate(ARTIKEL_FELDER):
            tk.Label(input_frame, text=f"{feld}:").grid(row=i, column=0, pady=2, sticky="w")

            if feld == "Doppelband":
                eintrag = ttk.Combobox(input_frame, values=ARTIKEL_DOPPELBAND_OPTIONEN, state="readonly", width=37)
            elif feld == "Typ":
                eintrag = ttk.Combobox(input_frame, values=ARTIKEL_TYP_OPTIONEN, state="readonly", width=37)
            elif feld == "Zustand":
                eintrag = ttk.Combobox(input_frame, values=ARTIKEL_ZUSTAND_OPTIONEN, state="readonly", width=37)
            else:
                eintrag = tk.Entry(input_frame, width=40)

            eintrag.grid(row=i, column=1, pady=2, padx=5, sticky="ew")
            self.eintraege[feld] = eintrag

        # Schaltflächen für Eingabe
        tk.Button(input_frame, text="🔄 Neue DBid", command=self.neue_dbid).grid(row=len(ARTIKEL_FELDER), column=0, pady=10, sticky="w")
        tk.Button(input_frame, text="🔍 ISBN/Google Suche", command=self.google_books_isbn_suche).grid(row=len(ARTIKEL_FELDER), column=1, pady=10, sticky="e")
        tk.Button(input_frame, text="💾 Speichern", command=self.speichern, bg="#90EE90").grid(row=len(ARTIKEL_FELDER) + 1, column=0, columnspan=2, pady=5, sticky="we")

        # --- Suchbereich (rechts) ---
        search_frame_container.columnconfigure(0, weight=1)
        search_frame_container.rowconfigure(3, weight=1)

        tk.Label(search_frame_container, text="🔍 Suche (Name, ISBN oder DBID)").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        self.such_eintrag = tk.Entry(search_frame_container, width=50)
        self.such_eintrag.grid(row=1, column=0, padx=(0, 5), sticky="we")
        tk.Button(search_frame_container, text="Suchen", command=self.suche, bg="#ADD8E6").grid(row=1, column=1, sticky="e")

        # Ergebnis-Tabelle - ERWEITERT UM VERLAG
        self.baum = ttk.Treeview(search_frame_container, columns=("DBid","Inhaber", "Name", "Band", "ISBN10", "ISBN13", "Preis", "Typ", "Verlag", "Standort", "Zustand"), show="headings")

        # Kopfzeilen setzen
        for col in self.baum["columns"]:
            self.baum.heading(col, text=col)

        self.baum.column("DBid", width=80, anchor='center')
        self.baum.column("Name", width=200)
        self.baum.column("Verlag", width=100) # NEU

        self.baum.grid(row=3, column=0, columnspan=2, padx=(0, 5), pady=5, sticky="nsew")
        self.baum.bind("<Double-1>", self.zeige_details)

        # Scrollbar hinzufügen
        scrollbar = ttk.Scrollbar(search_frame_container, orient="vertical", command=self.baum.yview)
        self.baum.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=3, column=2, sticky="ns", padx=(0, 5), pady=5)


        # Statusfeld (über gesamte Breite unten im Modul)
        self.status_label = tk.Label(self, text="ℹ️ Bereit", anchor="w", fg="gray", bd=1, relief=tk.SUNKEN)
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="we", padx=10, pady=5)

        # Startzustand: Neue ID generieren
        self.neue_dbid()

# -------------------- ANIME FAN SUB SYSTEM MODUL (AKTUALISIERT) --------------------

class AnimeFanSubSystem:
    """Der Tab für Anime-Fansub-Datenbankverwaltung mit Eingabe, Suche und Update."""
    def __init__(self, master):
        self.frame = ttk.Frame(master) # Dies ist das eigentliche Widget, das das Grid verwendet
        self.master = master.winfo_toplevel()
        self.eintraege = {}
        # WICHTIG: status_label hier auf None setzen, um Attribute-Error zu vermeiden
        self.status_label = None
        self.create_widgets()
        self.load_all_anime() # Lädt alle Einträge beim Start

    # --- DB Funktionen des AFSS-Moduls ---
    def neue_afssid(self):
        return generiere_dbid(length=10) # Kürzere AFSSID

    def hole_vollstaendige_daten(self, afssid):
        db_config = lade_config("db_config.json")
        conn = connect_db_artikel(db_config)
        if not conn: return None

        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM anime WHERE afssid = %s"
        cursor.execute(sql, (afssid,))
        ergebnis = cursor.fetchone()
        cursor.close()
        conn.close()
        return ergebnis

    def save_to_db(self):
        """Speichert oder aktualisiert einen Anime-Eintrag."""
        daten = {}
        for feld in AFSS_FIELDS:
            widget = self.eintraege[feld]
            key_name = feld.lower().replace(' ', '_')

            if isinstance(widget, ttk.Combobox):
                daten[key_name] = widget.get()
            elif feld == "Anzahl Episoden":
                try:
                    daten[key_name] = int(widget.get() or 0)
                except ValueError:
                    messagebox.showerror("Fehler", "Anzahl Episoden muss eine Zahl sein.")
                    return
            elif feld == "Cover URL": daten["cover"] = widget.get()
            elif feld == "Untertitel Sprache": daten["untertitel"] = widget.get()
            elif feld == "Audio Sprache": daten["audio"] = widget.get()
            elif feld == "Lokale Playlist": daten["playlist_local"] = widget.get()
            elif feld == "Online Playlist": daten["playlist_url"] = widget.get()
            else: daten[key_name] = widget.get()

        afssid = daten['afssid']
        if not afssid:
            messagebox.showerror("Fehler", "AFSSID darf nicht leer sein.")
            return

        db_config = lade_config("db_config.json")
        conn = connect_db_artikel(db_config)
        if not conn: return
        cursor = conn.cursor()

        cursor.execute("SELECT afssid FROM anime WHERE afssid = %s", (afssid,))
        exists = cursor.fetchone()

        db_keys = {
            "AFSSID": "afssid", "Titel": "titel", "Episoden": "episoden",
            "Anzahl Episoden": "episoden_anzahl", "Cover URL": "cover",
            "Untertitel Sprache": "untertitel", "Audio Sprache": "audio",
            "Lokale Playlist": "playlist_local", "Online Playlist": "playlist_url",
            "Medium": "medium", "Fansub Name": "fansub_name", "Fansub URL": "fansub_url"
        }

        db_daten = {db_keys[k]: daten[k.lower().replace(' ', '_')] for k in AFSS_FIELDS}
        columns = ', '.join([f'`{k}`' for k in db_daten.keys()])
        placeholders = ', '.join(['%s'] * len(db_daten))
        werte = tuple(db_daten.values())

        try:
            if exists:
                update_set = ', '.join([f"`{k}` = %s" for k in db_daten.keys()])
                sql = f"UPDATE anime SET {update_set} WHERE afssid = %s"
                cursor.execute(sql, werte + (afssid,))
                self.status_label.config(text=f"✅ Update erfolgreich für AFSSID: {afssid}", fg="green")
            else:
                sql = f"INSERT INTO anime ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, werte)
                self.status_label.config(text=f"✅ Neuer Eintrag gespeichert: {afssid}", fg="green")

            conn.commit()
            self.clear_form()
            self.load_all_anime()

        except mysql.connector.Error as err:
            self.status_label.config(text=f"❌ DB-Fehler beim Speichern: {err}", fg="red")
        finally:
            cursor.close()
            conn.close()

    def search_anime(self, query=None):
        """Sucht nach Anime-Einträgen und aktualisiert das Treeview. ERWEITERT."""
        if query is None:
            query = self.search_entry.get()

        db_config = lade_config("db_config.json")
        conn = connect_db_artikel(db_config)
        if not conn: return
        cursor = conn.cursor(dictionary=True)

        # Holen Sie die benötigten Spalten für die erweiterte Treeview
        sql = """
        SELECT afssid, titel, episoden, medium, playlist_local FROM anime
        WHERE afssid LIKE %s OR titel LIKE %s
        """
        like = f"%{query}%"
        cursor.execute(sql, (like, like))
        ergebnisse = cursor.fetchall()
        cursor.close()
        conn.close()

        for row in self.tree.get_children():
            self.tree.delete(row)

        for eintrag in ergebnisse:
            # Die Werte müssen der Reihenfolge der Spalten in create_treeview entsprechen
            self.tree.insert("", "end", values=(
                eintrag.get("afssid", ""),
                eintrag.get("titel", ""),
                eintrag.get("episoden", ""),
                eintrag.get("medium", "N/A"), # NEU
                eintrag.get("playlist_local", "N/A") # NEU
            ))
        self.status_label.config(text=f"ℹ️ {len(ergebnisse)} Einträge gefunden für '{query}'.", fg="blue")

    def load_all_anime(self):
        """Lädt alle Einträge beim Start."""
        self.search_anime(query="")

    def load_for_update(self, event):
        """Lädt die ausgewählten Daten in die Eingabemaske."""
        selected_item = self.tree.selection()
        if not selected_item: return

        afssid = self.tree.item(selected_item, 'values')[0]
        details = self.hole_vollstaendige_daten(afssid)

        if not details:
            self.status_label.config(text="❌ Fehler beim Laden der Details.", fg="red")
            return

        db_to_gui_map = {
            "afssid": "AFSSID", "titel": "Titel", "episoden": "Episoden",
            "episoden_anzahl": "Anzahl Episoden", "cover": "Cover URL",
            "untertitel": "Untertitel Sprache", "audio": "Audio Sprache",
            "playlist_local": "Lokale Playlist", "playlist_url": "Online Playlist",
            "medium": "Medium", "fansub_name": "Fansub Name", "fansub_url": "Fansub URL"
        }

        for db_key, gui_key in db_to_gui_map.items():
            value = str(details.get(db_key, ""))
            widget = self.eintraege.get(gui_key)

            if widget:
                widget.delete(0, tk.END)
                if isinstance(widget, ttk.Combobox):
                    widget.set(value)
                else:
                    widget.insert(0, value)

        self.eintraege["AFSSID"].config(state='readonly')
        self.status_label.config(text=f"ℹ️ AFSSID {afssid} zum Bearbeiten geladen. Speichern führt zum Update.", fg="orange")

    def clear_form(self):
        """Leert alle Eingabefelder und generiert eine neue AFSSID."""
        for key in AFSS_FIELDS:
            widget = self.eintraege[key]
            widget.delete(0, tk.END)
            if isinstance(widget, ttk.Combobox):
                widget.set("")

        self.eintraege["AFSSID"].config(state='normal')
        self.eintraege["AFSSID"].insert(0, self.neue_afssid())

        if self.status_label:
            self.status_label.config(text="ℹ️ Formular geleert. Neue AFSSID generiert.", fg="gray")


    # --- AFSS-GUI Funktionen ---
    def create_treeview(self):
        # Treeview Spalten definieren (erweitert um Medium und Lokaler Pfad)
        cols = ("AFSSID", "Titel", "Episoden", "Medium", "Lokaler Pfad")
        tree = ttk.Treeview(self.search_result_frame, columns=cols, show='headings', height=15)

        tree.heading("AFSSID", text="AFSSID")
        tree.heading("Titel", text="Titel")
        tree.heading("Episoden", text="Episoden")
        tree.heading("Medium", text="Medium") # NEU
        tree.heading("Lokaler Pfad", text="Lokaler Pfad") # NEU

        tree.column("AFSSID", width=100, anchor='center')
        tree.column("Titel", width=250)
        tree.column("Episoden", width=60, anchor='center')
        tree.column("Medium", width=80, anchor='center')
        tree.column("Lokaler Pfad", width=200)

        tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(self.search_result_frame, orient="vertical", command=tree.yview)
        vsb.pack(side='right', fill='y')
        tree.configure(yscrollcommand=vsb.set)

        return tree

    def create_widgets(self):
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        # --- Statusleiste (unten) MUSS ZUERST ERSTELLT WERDEN ---
        self.status_label = tk.Label(self.frame, text="ℹ️ Initialisiere...", anchor="w", fg="gray", bd=1, relief=tk.SUNKEN)
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="we", padx=10, pady=5)

        # --- Eingabebereich (links) ---
        input_container = tk.LabelFrame(self.frame, text="Anime Eintrag Bearbeiten/Neu", padx=10, pady=10)
        input_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        input_frame = tk.Frame(input_container)
        input_frame.pack(padx=5, pady=5)

        for i, feld in enumerate(AFSS_FIELDS):
            tk.Label(input_frame, text=f"{feld}:").grid(row=i, column=0, pady=2, sticky="w")

            if feld == "Medium":
                eintrag = ttk.Combobox(input_frame, values=AFSS_MEDIUM_OPTIONS, state="readonly", width=37)
            else:
                eintrag = tk.Entry(input_frame, width=40)

            eintrag.grid(row=i, column=1, pady=2, padx=5, sticky="ew")
            self.eintraege[feld] = eintrag

        self.clear_form()

        # --- Eingabe-Buttons ---
        button_frame = tk.Frame(input_frame)
        button_frame.grid(row=len(AFSS_FIELDS), column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="💾 Speichern/Update", command=self.save_to_db, bg="#90EE90").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="❌ Neueingabe", command=self.clear_form, bg="#FFD700").pack(side=tk.LEFT, padx=5)

        # --- Such- und Ergebnisbereich (rechts) ---
        search_container = tk.LabelFrame(self.frame, text="Suche & Ergebnisse", padx=10, pady=10)
        search_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        search_container.columnconfigure(0, weight=1)
        search_container.rowconfigure(2, weight=1)

        # Sucheingabe
        search_input_frame = tk.Frame(search_container)
        search_input_frame.grid(row=0, column=0, sticky="we", pady=(0, 10))
        search_input_frame.columnconfigure(0, weight=1)

        tk.Label(search_input_frame, text="Suche AFSSID/Titel:").grid(row=0, column=0, sticky="w")
        self.search_entry = tk.Entry(search_input_frame, width=50)
        self.search_entry.grid(row=1, column=0, padx=(0, 5), sticky="we")
        tk.Button(search_input_frame, text="🔍 Suchen", command=self.search_anime, bg="#ADD8E6").grid(row=1, column=1, sticky="e")

        # Suchergebnis-Frame
        self.search_result_frame = tk.Frame(search_container)
        self.search_result_frame.grid(row=2, column=0, sticky="nsew")
        self.tree = self.create_treeview()

        # --- Event Bindings ---
        self.tree.bind('<<TreeviewSelect>>', self.load_for_update) # Einzelklick zum Bearbeiten
        self.tree.bind('<Double-1>', self.on_double_click)

        # --- Abspielen Button (unten rechts) ---
        play_button_frame = tk.Frame(search_container)
        play_button_frame.grid(row=3, column=0, sticky="e", pady=5)
        tk.Button(play_button_frame, text="▶️ Lokale Playlist Abspielen", command=self.play_local_playlist, bg="#90EE90").pack(side=tk.RIGHT, padx=5)

    def on_double_click(self, event):
        """Zeigt Details zum ausgewählten Eintrag an."""
        selected_item = self.tree.selection()
        if selected_item:
            afssid = self.tree.item(selected_item, 'values')[0]
            details = self.hole_vollstaendige_daten(afssid)

            if details:
                detail_str = "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in details.items() if v])
                messagebox.showinfo(f"Details zu AFSSID: {afssid}", detail_str)
            else:
                 messagebox.showwarning("Fehler", f"Keine Details für AFSSID {afssid} gefunden.")

    def play_local_playlist(self):
        """Startet das Player-Modul mit dem lokalen Pfad."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Auswahl fehlt", "Bitte wählen Sie einen Anime-Eintrag aus.")
            return

        item_data = self.tree.item(selected_item, 'values')
        playlist_path = item_data[4] # Lokaler Pfad ist die 5. Spalte (Index 4)

        if playlist_path and playlist_path not in ["N/A", "Kein Pfad", ""]:
            # Erstellt das separate Player-Fenster
            player_window = tk.Toplevel(self.master)
            PlayerModul(player_window, playlist_path)
        else:
             messagebox.showwarning("Fehlende Daten", "Keine lokale Playlist ('Lokaler Pfad') für diesen Eintrag gefunden.")

# -------------------- SCHALLPLATTEN MODUL --------------------

class SchallplattenModul(tk.Frame):
    """ Schallplatten-Suchmodul (Reimplementiert aus schlplatte.py). """
    def __init__(self, master):
        super().__init__(master)
        self.bilder = {}
        self.main_master = master.winfo_toplevel()
        # Konfiguration laden
        config = lade_config("config.json")
        # Fallback für die alten Konfigurationsschlüssel, wenn noch vorhanden
        self.API_URL = config.get("api_url")
        self.API_TOKEN = config.get("token")

        if not self.API_URL or not self.API_TOKEN:
             tk.Label(self, text="⚠️ Konfiguration (config.json) unvollständig für Schallplatten-API (api_url/token fehlen).", fg="red").pack(pady=20)
             return

        self.create_widgets()

    def create_widgets(self):
        # Haupt-Frame für Input und Suchen
        main_search_frame = tk.Frame(self)
        main_search_frame.pack(pady=10, padx=10, fill="x")

        # Eingabefelder (links)
        input_frame = tk.Frame(main_search_frame)
        input_frame.pack(side="left", padx=10)

        tk.Label(input_frame, text="Titel:").grid(row=0, column=0, sticky="w", padx=5)
        self.eintrag_name = tk.Entry(input_frame, width=40)
        self.eintrag_name.grid(row=0, column=1, padx=5)

        tk.Label(input_frame, text="Plattennummer:").grid(row=1, column=0, sticky="w", padx=5)
        self.eintrag_nummer = tk.Entry(input_frame, width=40)
        self.eintrag_nummer.grid(row=1, column=1, padx=5)

        tk.Label(input_frame, text="DB-ID:").grid(row=2, column=0, sticky="w", padx=5)
        self.eintrag_dbid = tk.Entry(input_frame, width=40)
        self.eintrag_dbid.grid(row=2, column=1, padx=5)

        tk.Button(input_frame, text="🔍 Suchen", command=self.suche, bg="#87CEFA").grid(row=0, column=2, rowspan=3, padx=10, sticky="nsew")

        # Ergebnis-Liste und Bild-Bereich
        result_frame = tk.Frame(self)
        result_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Ergebnis-Liste (links in result_frame)
        self.listbox = tk.Listbox(result_frame, width=80, height=20)
        self.listbox.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.listbox.bind('<Double-1>', self.oeffnen)
        self.listbox.bind('<<ListboxSelect>>', self.bild_anzeigen)

        # Bild-Bereich (rechts in result_frame)
        self.bild_label = tk.Label(result_frame, text="Bild hier", width=30, height=15, relief="solid")
        self.bild_label.pack(side="right", fill="y")

    def suche(self):
        params = {
            "q": "",
            "token": self.API_TOKEN
        }
        # Kombiniere Filter
        q = []
        if self.eintrag_name.get():
            q.append(self.eintrag_name.get())
        if self.eintrag_nummer.get():
            q.append(self.eintrag_nummer.get())
        if self.eintrag_dbid.get():
            q.append(self.eintrag_dbid.get())
        params["q"] = " ".join(q)

        try:
            r = requests.get(self.API_URL, params=params)
            r.raise_for_status()
            daten = r.json()

            self.listbox.delete(0, tk.END)
            self.bilder.clear()

            for eintrag in daten:
                # Text ist das erste Element, Link das zweite, Bild-URL das dritte
                # Hinzufügen von mehr Informationen im Anzeigetext
                text = f"{eintrag.get('name', 'N/A')} [{eintrag.get('plattennummer', 'N/A')}] | Genre: {eintrag.get('genre', 'N/A')} | DBID: {eintrag.get('dbid', 'N/A')}"
                link = f"https://philipp-lindner-server.de/schalplatte/details.php?id={eintrag.get('id')}"
                # Der Wert in der Listbox ist ein Tupel (Anzeigetext, Link, Bild-URL)
                self.listbox.insert(tk.END, (text, link, eintrag.get('bild_url')))
        except Exception as e:
            messagebox.showerror("Fehler bei der Suche", str(e))

    def oeffnen(self, evt):
        auswahl = self.listbox.curselection()
        if auswahl:
            eintrag = self.listbox.get(auswahl[0])
            link = eintrag[1] # Link ist das zweite Element im Tupel
            webbrowser.open(link)

    def bild_anzeigen(self, evt):
        auswahl = self.listbox.curselection()
        if auswahl:
            eintrag = self.listbox.get(auswahl[0])
            bild_url = eintrag[2]

            if not bild_url:
                self.bild_label.config(text="Kein Bild verfügbar", image="")
                return

            try:
                # Bild laden
                r = requests.get(bild_url)
                img = Image.open(io.BytesIO(r.content))
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)

                # Speichere die Referenz
                self.bilder['current_image'] = ImageTk.PhotoImage(img)
                self.bild_label.config(image=self.bilder['current_image'], text="")
            except Exception:
                self.bild_label.config(text="Bild konnte nicht geladen werden", image="")

# =============================================================================
# MODUL: MULTI-MEDIEN-VERWALTUNG (FILME, SERIEN, ANIME)
# =============================================================================

class FilmSerienModul(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        # Lädt den Key aus der progPen.json
        self.api_key = self.lade_api_key()
        self.eintraege = {}
        self.create_widgets()

    def lade_api_key(self):
        try:
            with open("progPen.json", "r") as f:
                data = json.load(f)
                return data.get("TMDB_API_KEY", "")
        except:
            return ""

    def neue_dbid_fuer_feld(self):
        """ Nutzt deine Funktion generiere_dbid(16) """
        neue_id = generiere_dbid(length=16)
        self.eintraege["DBid"].config(state='normal')
        self.eintraege["DBid"].delete(0, tk.END)
        self.eintraege["DBid"].insert(0, neue_id)
        self.eintraege["DBid"].config(state='readonly')

    def info_abrufen(self):
        titel = self.eintraege["Titel"].get()
        typ = self.eintraege["Typ"].get()

        if not titel:
            messagebox.showwarning("Suche", "Bitte gib einen Titel ein!")
            return

        if typ == "Anime":
            # --- MyAnimeList Suche via Jikan API ---
            url = f"https://api.jikan.moe/v4/anime?q={titel}&limit=1"
            try:
                res = requests.get(url).json()
                data = res['data'][0]
                self.fuelle_felder(
                    titel=data.get('title'),
                    id_val=data.get('mal_id'),
                    jahr=data.get('aired', {}).get('prop', {}).get('from', {}).get('year'),
                    genre=", ".join([g['name'] for g in data.get('genres', [])]),
                    descr=data.get('synopsis'),
                    img=data.get('images', {}).get('jpg', {}).get('large_image_url')
                )
            except:
                messagebox.showerror("MAL", "Keine Anime-Daten gefunden.")
        else:
            # --- TMDB Suche für Filme & Serien ---
            if not self.api_key:
                messagebox.showerror("Fehler", "Kein TMDB API Key in progPen.json gefunden!")
                return

            url = f"https://api.themoviedb.org/3/search/multi?api_key={self.api_key}&query={titel}&language=de-DE"
            try:
                res = requests.get(url).json()
                item = res['results'][0]
                self.fuelle_felder(
                    titel=item.get('title') or item.get('name'),
                    id_val=item.get('id'),
                    jahr=(item.get('release_date') or item.get('first_air_date', "0000"))[:4],
                    genre="Siehe TMDB", # TMDB liefert IDs, Umwandlung wäre hier zu lang
                    descr=item.get('overview'),
                    img=f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
                )
            except:
                messagebox.showerror("TMDB", "Keine Film-Daten gefunden.")

    def fuelle_felder(self, titel, id_val, jahr, genre, descr, img):
        self.eintraege["Titel"].delete(0, tk.END)
        self.eintraege["Titel"].insert(0, titel)
        self.eintraege["ID"].delete(0, tk.END)
        self.eintraege["ID"].insert(0, id_val)
        self.eintraege["Jahr"].delete(0, tk.END)
        self.eintraege["Jahr"].insert(0, jahr)
        self.eintraege["Genre"].delete(0, tk.END)
        self.eintraege["Genre"].insert(0, genre)
        self.eintraege["Beschreibung"].delete("1.0", tk.END)
        self.eintraege["Beschreibung"].insert("1.0", descr)
        self.eintraege["Cover_URL"].delete(0, tk.END)
        self.eintraege["Cover_URL"].insert(0, img)
        messagebox.showinfo("Erfolg", "Daten wurden automatisch ausgefüllt!")

    def speichern(self):

        # 1. Prüfen, ob der User PRO ist
        # (Angenommen, du hast das license_tier beim Login in einer globalen Variable gespeichert)
        #if USER_LICENSE_TIER == "FREE":
            # Checke wie viele Einträge schon existieren
         #   cursor.execute("SELECT COUNT(*) FROM filme_serien")
          #  anzahl = cursor.fetchone()[0]

           # if anzahl >= 100: # Limit für FREE-User
            #    messagebox.showwarning("Limit erreicht",
             #       "Als FREE-User kannst du maximal 50 Einträge speichern.\n"
              #      "Bitte upgrade auf PRO für unbegrenzten Speicherplatz!")
               # return
        # Daten sammeln
        vals = {k: v.get() if hasattr(v, 'get') else v.get("1.0", tk.END) for k, v in self.eintraege.items()}

        db_config = lade_config("db_config.json")
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            sql = """INSERT INTO filme_serien
                     (dbid, titel, typ, format, genre, jahr, tmdb_mal_id, standort, zustand, beschreibung, cover_url)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (
                vals["DBid"], vals["Titel"], vals["Typ"], vals["Format"], vals["Genre"],
                vals["Jahr"], vals["ID"], vals["Standort"], vals["Zustand"],
                vals["Beschreibung"].strip(), vals["Cover_URL"]
            ))
            conn.commit()
            conn.close()
            messagebox.showinfo("Erfolg", "Eintrag gespeichert!")
            self.neue_dbid_fuer_feld()
        except Exception as e:
            messagebox.showerror("DB Fehler", str(e))

    def create_widgets(self):
        main_scroll = tk.Canvas(self)
        form_frame = tk.Frame(main_scroll, padx=10, pady=10)
        main_scroll.pack(side="left", fill="both", expand=True)

        felder_liste = [
            ("DBid (16-stellig)", "DBid"),
            ("Titel", "Titel"),
            ("Typ", "Typ"),
            ("Format", "Format"),
            ("Genre", "Genre"),
            ("Jahr", "Jahr"),
            ("TMDB / MAL ID", "ID"),
            ("Standort", "Standort"),
            ("Zustand", "Zustand"),
            ("Cover URL", "Cover_URL")
        ]

        for i, (txt, key) in enumerate(felder_liste):
            tk.Label(form_frame, text=txt).grid(row=i, column=0, sticky="w", pady=2)
            if key == "Typ":
                e = ttk.Combobox(form_frame, values=["Film", "Serie", "Anime"], state="readonly")
            elif key == "Format":
                e = ttk.Combobox(form_frame, values=["DVD", "Blu-ray", "4K", "Digital", "VHS"], state="readonly")
            elif key == "Zustand":
                e = ttk.Combobox(form_frame, values=ARTIKEL_ZUSTAND_OPTIONEN, state="readonly")
            else:
                e = tk.Entry(form_frame, width=50)
            e.grid(row=i, column=1, pady=2, padx=5)
            self.eintraege[key] = e

        # Beschreibung (Textfeld)
        tk.Label(form_frame, text="Beschreibung").grid(row=len(felder_liste), column=0, sticky="nw")
        self.eintraege["Beschreibung"] = tk.Text(form_frame, height=5, width=38)
        self.eintraege["Beschreibung"].grid(row=len(felder_liste), column=1, pady=5)

        # Buttons
        btn_f = tk.Frame(form_frame)
        btn_f.grid(row=len(felder_liste)+1, column=0, columnspan=2, pady=10)

        tk.Button(btn_f, text="🔍 Info abrufen (TMDB/MAL)", command=self.info_abrufen, bg="#add8e6").pack(side="left", padx=5)
        tk.Button(btn_f, text="💾 In Datenbank speichern", command=self.speichern, bg="#90ee90", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        form_frame.pack()
        self.neue_dbid_fuer_feld()

# =============================================================================
# MODUL: GLOBALE MULTI-SUCHE MIT DIREKT-ZUGRIFF ("SPRINGE-ZU")
# =============================================================================

class GlobaleSucheModul(tk.Frame):
    def __init__(self, master, notebook_referenz):
        super().__init__(master)
        self.notebook = notebook_referenz  # Referenz auf das Haupt-Notebook
        self.create_widgets()

    def suche_starten(self, event=None):
        begriff = self.suche_entry.get().strip()
        if len(begriff) < 3:
            messagebox.showwarning("Suche", "Bitte mindestens 3 Zeichen eingeben.")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        db_config = lade_config("db_config.json")
        api_config = lade_config("config.json")

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            # Suchmuster für SQL (findet den Begriff irgendwo im Text oder in der ID)
            search_param = f"%{begriff}%"

            # 1. Suche in 'artikel' (Name ODER DBid)
            cursor.execute("""
                SELECT dbid, Name as titel, Typ, Standort
                FROM media
                WHERE Name LIKE %s OR dbid LIKE %s
            """, (search_param, search_param))
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=(row['dbid'], row['titel'], row['Typ'], row['Standort'], "BÜCHER_TAB"))

            # 2. Suche in 'anime_fan_sab' (Titel ODER AFSSID)
            cursor.execute("""
                SELECT AFSSID as dbid, Titel, 'Anime' as Typ, 'Digital' as Standort
                FROM anime
                WHERE Titel LIKE %s OR AFSSID LIKE %s
            """, (search_param, search_param))
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=(row['dbid'], row['Titel'], "Anime (AFSS)", "Digital", "ANIME_TAB"))

            # 3. Suche in 'filme_serien' (titel ODER dbid)
            cursor.execute("""
                SELECT dbid, titel, typ, standort
                FROM filme_serien
                WHERE titel LIKE %s OR dbid LIKE %s
            """, (search_param, search_param))
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=(row['dbid'], row['titel'], row['typ'], row['standort'], "VIDEO_TAB"))

            conn.close()

            # 4. Schallplatten API (Externe Suche)
            self.suche_schallplatten_api(begriff, api_config)

        except Exception as e:
            messagebox.showerror("Fehler", f"Suche fehlgeschlagen: {e}")

    def suche_schallplatten_api(self, begriff, config):
        url = config.get("api_url")
        params = {"token": config.get("token"), "query": begriff, "inhaberid": config.get("inhaberid")}
        try:
            res = requests.get(url, params=params, timeout=3)
            if res.status_code == 200:
                for item in res.json().get("results", []):
                    self.tree.insert("", "end", values=("API", item.get("album_title"), "Schallplatte", "Extern", "API"))
        except: pass

    def on_double_click(self, event):
        """ Die 'Springe-zu' Logik """
        item_id = self.tree.selection()[0]
        werte = self.tree.item(item_id, "values")
        dbid = werte[0]
        ziel_tab_kennung = werte[4]

        if ziel_tab_kennung == "API":
            messagebox.showinfo("Info", "Dies ist ein externer API-Eintrag. Er kann nur im Schallplatten-Tab verwaltet werden.")
            return

        # Mapping der Tab-Indizes (Muss mit deiner zeige_hauptfenster Reihenfolge übereinstimmen!)
        # Beispiel: 0=Profil, 1=Anime, 2=Bücher, 3=Video, 4=Suche
        tab_mapping = {
            "BÜCHER_TAB": 2,
            "ANIME_TAB": 1,
            "VIDEO_TAB": 3
        }

        if ziel_tab_kennung in tab_mapping:
            idx = tab_mapping[ziel_tab_kennung]
            self.notebook.select(idx)

            # Info an den User, welche ID geladen werden soll
            messagebox.showinfo("Springe zu...", f"Wechsle zu Tab... \nID {dbid} wurde zur Bearbeitung vorgemerkt.")
            # Hier könnte man jetzt noch eine Funktion aufrufen: self.notebook.winfo_children()[idx].lade_datensatz(dbid)

    def create_widgets(self):
        lbl = tk.Label(self, text="🔎 Globale Datenbank-Suche", font=("Arial", 14, "bold"), pady=10)
        lbl.pack()

        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=20)

        self.suche_entry = tk.Entry(search_frame, font=("Arial", 12))
        self.suche_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.suche_entry.bind("<Return>", self.suche_starten)

        btn = tk.Button(search_frame, text="Suchen", command=self.suche_starten, bg="#90ee90", width=15)
        btn.pack(side="left")

        # Tabelle
        columns = ("ID", "Titel", "Typ", "Standort", "InternerTyp")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("ID", text="Medien-ID")
        self.tree.heading("Titel", text="Titel / Name")
        self.tree.heading("Typ", text="Kategorie")
        self.tree.heading("Standort", text="Lagerort")
        self.tree.column("InternerTyp", width=0, stretch=tk.NO) # Versteckte Spalte für Logik

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree.bind("<Double-1>", self.on_double_click)

        tk.Label(self, text="Doppelklick auf ein Ergebnis, um zum entsprechenden Tab zu springen.", fg="gray").pack()



# -------------------- HAUPT-GUI LOGIK --------------------

def zeige_hauptfenster(username):
    """Erstellt das Hauptfenster mit den Tabs nach erfolgreichem Login."""
    global hauptfenster
    hauptfenster = tk.Tk()
    hauptfenster.title(f"Bücherei 2.0 Online - Angemeldet als: {username}")
    hauptfenster.geometry("1400x900") # Größere Standardgröße

    notebook = ttk.Notebook(hauptfenster)


    # 1. Mein Profil Tab
    user_info_instance = UserInfoModul(notebook, username)
    notebook.add(user_info_instance.frame, text='👤 Mein Profil')

    # 2. Anime Fan Sub System Tab (AFSS)
    afss_instance = AnimeFanSubSystem(hauptfenster)
    notebook.add(afss_instance.frame, text='📺 Anime Fan Sub System')

    # 3. Medienverwaltung Tab (ArtikelModul)
    medien_frame = ArtikelModul(notebook)
    notebook.add(medien_frame, text='📚 Medienverwaltung')

    # 4. Schallplatten Tab (SchallplattenModul)
    schallplatten_frame = SchallplattenModul(notebook)
    notebook.add(schallplatten_frame, text='🎵 Schallplatten')

    #5 DVD Filme und CO
    medien_tab = FilmSerienModul(notebook)
    notebook.add(medien_tab, text="🎬 Video-Archiv")

    #6 Globale suche
    suche_tab = GlobaleSucheModul(notebook, notebook)
    notebook.add(suche_tab, text="🔍 Globale Suche")



    notebook.pack(expand=True, fill='both', padx=10, pady=10)

    # Der globale Status-Label
    global status_label
    status_label = tk.Label(hauptfenster, text="Bereit.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_label.pack(side=tk.BOTTOM, fill=tk.X)

    hauptfenster.mainloop()


# -------------------- LOGIN / REGISTRIERUNG LOGIK --------------------

def register_user_gui(users, login_fenster):
    """Zeigt ein separates Fenster zur Benutzerregistrierung."""
    reg_window = tk.Toplevel(login_fenster)
    reg_window.title("Neu Registrieren")
    reg_window.geometry("350x300")
    reg_window.resizable(False, False)

    def attempt_registration():
        new_user = entry_new_user.get().strip()
        new_pass = entry_new_pass.get()
        new_pass_confirm = entry_new_pass_confirm.get()

        if new_user in users:
            messagebox.showerror("Fehler", "Benutzername existiert bereits in users.json.")
            return
        if new_pass != new_pass_confirm:
            messagebox.showerror("Fehler", "Passwörter stimmen nicht überein.")
            return
        if not new_user or not new_pass:
            messagebox.showerror("Fehler", "Benutzername und Passwort dürfen nicht leer sein.")
            return

        db_config = lade_config("db_config.json")
        if not db_config:
            messagebox.showerror("Fehler", "Datenbankkonfiguration (db_config.json) fehlt.")
            return

        try:
            conn = connect_db_artikel(db_config)
            if not conn:
                messagebox.showerror("DB Fehler", "Keine Verbindung zur Datenbank möglich.")
                return

            cursor = conn.cursor()

            password_hash = md5_hash(new_pass)
            # Erzeugt eine eindeutige Inhaber-ID basierend auf dem Benutzernamen
            inhaber_id = hashlib.md5(new_user.encode()).hexdigest()[:10]

            # Die user-Tabelle muss die Spalten 'username', 'password', 'inhaberID', 'Name', 'license_tier' enthalten
            sql = "INSERT INTO user (inhaberID, username, Name, password, license_tier) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (inhaber_id, new_user, new_user, password_hash, "FREE"))
            conn.commit()

            cursor.close()
            conn.close()

            # users.json aktualisieren (wichtig für den sofortigen Login)
            users[new_user] = password_hash
            save_users_json(users)

            messagebox.showinfo("Erfolg", f"Benutzer '{new_user}' wurde registriert. Sie können sich jetzt anmelden.")
            reg_window.destroy()

        except mysql.connector.Error as err:
            messagebox.showerror("DB Fehler", f"Registrierung fehlgeschlagen: {err}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    tk.Label(reg_window, text="Neuer Benutzername:", font=("Arial", 10, "bold")).pack(pady=5)
    entry_new_user = tk.Entry(reg_window, width=30)
    entry_new_user.pack()

    tk.Label(reg_window, text="Passwort:").pack(pady=5)
    entry_new_pass = tk.Entry(reg_window, show="*", width=30)
    entry_new_pass.pack()

    tk.Label(reg_window, text="Passwort bestätigen:").pack(pady=5)
    entry_new_pass_confirm = tk.Entry(reg_window, show="*", width=30)
    entry_new_pass_confirm.pack()

    tk.Button(reg_window, text="Registrieren", command=attempt_registration, bg="yellow").pack(pady=15)
    reg_window.grab_set()

def login():
    """Überprüft die Anmeldedaten und startet das Hauptfenster."""
    benutzer = eintrag_benutzer.get().strip()
    passwort = eintrag_passwort.get()

    users = lade_config("users.json")

    if not users:
        messagebox.showerror("Fehler", "Benutzerdaten (users.json) konnten nicht geladen werden. Bitte setup.py erneut starten.")
        return

    # Passwort-Hash vergleichen
    passwort_hash = md5_hash(passwort)

    if benutzer in users and users[benutzer] == passwort_hash:
        login_fenster.destroy()
        # VORHER: zeige_hauptfenfenster(benutzer)
        zeige_hauptfenster(benutzer) # ⬅️ KORRIGIERTE ZEILE
    else:
        messagebox.showerror("Fehler", "Login fehlgeschlagen! (Falscher Benutzername oder Passwort)")

# -------------------- MAIN BLOCK --------------------

if __name__ == "__main__":

    # NEU: Statistik senden (muss vor dem Login-Fenster passieren)
    send_statistics()

    # Prüft, ob Konfigurationsdateien existieren. Falls nicht, startet es setup.py.
    # Wichtig: Hier wird nur auf die nötigsten Dateien geprüft, setup.py muss die restlichen erstellen.
    if not os.path.exists("config.json") or not os.path.exists("users.json") or not os.path.exists("db_config.json") or not os.path.exists("progPen.json"):
        messagebox.showwarning("Setup erforderlich", "Konfigurationsdateien fehlen. Bitte setup.py ausführen.")

    # Benutzerdaten für Registrierung laden
    users_data = lade_config("users.json")

    login_fenster = tk.Tk()
    login_fenster.title("🔐 Login")
    login_fenster.geometry("450x400")

    # Logo laden und anzeigen (optional)
    try:
        # Passen Sie den Pfad zu Ihrem Logo an
        img = Image.open("logo.png")
        img = img.resize((295, 150), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(login_fenster, image=photo)
        logo_label.image = photo
        logo_label.pack(pady=10)
    except FileNotFoundError:
        tk.Label(login_fenster, text="Bücherei 2.0", font=("Arial", 24, "bold")).pack(pady=10)
    except Exception as e:
         tk.Label(login_fenster, text=f"Fehler beim Laden des Logos: {e}", fg="red").pack(pady=10)


    # Frame für die Login-Eingaben
    login_frame = tk.Frame(login_fenster)
    login_frame.pack(pady=10)

    tk.Label(login_frame, text="Benutzername").grid(row=0, column=0, pady=5, sticky="w")
    eintrag_benutzer = tk.Entry(login_frame, width=30)
    eintrag_benutzer.grid(row=0, column=1, pady=5)

    tk.Label(login_frame, text="Passwort").grid(row=1, column=0, pady=5, sticky="w")
    eintrag_passwort = tk.Entry(login_frame, show="*", width=30)
    eintrag_passwort.grid(row=1, column=1, pady=5)

    # Buttons
    button_frame = tk.Frame(login_fenster)
    button_frame.pack(pady=20)

    tk.Button(button_frame, text="Login", command=login, bg="#90EE90", width=15).pack(side=tk.LEFT, padx=10)

    # Registrieren-Button
    tk.Button(button_frame, text="Neu Registrieren", command=lambda: webbrowser.open("https://anmeldung.buch-archiv20-software.de/"), bg="#ADD8E6", width=15).pack(side=tk.LEFT, padx=10)

    login_fenster.mainloop()
