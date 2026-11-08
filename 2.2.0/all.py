# =============================================================
# Projekt: Bücherei 2.0 Online
# Autor: Philipp Lindner
# Webseite: https://buch-archiv20-software.de/
# Lizenz: MIT License
# -------------------------------------------------------------
# Copyright (c) 2026 Philipp Lindner
# =============================================================

import json
import os
import random
import string
import hashlib
import tkinter as tk
from tkinter import messagebox, ttk
import requests
import webbrowser
from PIL import Image, ImageTk
import io
import platform
import sys
import logging

# ===================== GLOBAL API CONFIGURATION =====================
API_BASE_URL = "https://api-buch-archiv20-software.route64.de"

def get_api_headers():
    """Erstellt den Header inklusive API Secret Key."""
    config = lade_config("config.json")
    api_key = config.get("api_secret_key", config.get("API_SECRET_KEY", "DEIN_SICHERER_API_KEY"))
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

# ===================== LOGGING & API-TERMINAL-OUTPUT =====================
LOG_DATEI = "debug_log.txt"
logging.basicConfig(
    filename=LOG_DATEI,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# System-Logging zusätzlich auf der Kommandozeile (Console) ausgeben
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - API-LOG: %(message)s'))
logging.getLogger().addHandler(console_handler)

logging.info("--- Programm gestartet ---")

def api_request(method, endpoint, **kwargs):
    """Führt HTTP-Requests aus und loggt die gesamte Kommunikation in der Konsole."""
    url = f"{API_BASE_URL}{endpoint}"
    kwargs["headers"] = get_api_headers()

    logging.info(f"--> HTTP {method.upper()} {url}")
    if "params" in kwargs:
        logging.info(f"    Params: {kwargs['params']}")
    if "json" in kwargs:
        logging.info(f"    Body: {kwargs['json']}")

    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        logging.info(f"<-- Status: {response.status_code}")
        try:
            logging.debug(f"    Response Payload: {response.json()}")
        except Exception:
            logging.debug(f"    Response Text: {response.text[:200]}")
        return response
    except Exception as e:
        logging.error(f"❌ API Connection Error: {e}")
        raise e

# Optional: Import für VLC
try:
    import vlc
except ImportError:
    vlc = None
    print("VLC-Bibliothek (python-vlc) nicht gefunden. Die Abspielfunktion funktioniert nicht.")

# ==============================================================================
# GLOBALE KONSTANTEN
# ==============================================================================

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

AFSS_FIELDS = [
    "AFSSID", "Titel", "Episoden", "Anzahl Episoden", "Cover URL",
    "Untertitel Sprache", "Audio Sprache", "Lokale Playlist", "Online Playlist",
    "Medium", "Fansub Name", "Fansub URL"
]
AFSS_MEDIUM_OPTIONS = ["Online", "DVD", "VHS", "Datei (Auf PC)", "Blu-Ray"]

FILM_TYP_OPTIONEN = ["Film", "Serie"]
FILM_FORMAT_OPTIONEN = ["DVD", "Blu-ray", "4K UHD", "Digital", "VHS"]

status_label = None

# ===================== DESIGN-TOOLS =====================
def lade_design_einstellungen(config_path="config.json"):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return {
            "background_color": config.get("background_color", "#ffffff"),
            "text_color": config.get("text_color", "#000000"),
            "background_image": config.get("background_image", "")
        }
    except Exception:
        return {"background_color": "#ffffff", "text_color": "#000000", "background_image": ""}

def wende_design_einstellungen(root, design):
    root.configure(bg=design["background_color"])
    for widget in root.winfo_children():
        try:
            widget.configure(bg=design["background_color"], fg=design["text_color"])
        except:
            pass
    if design["background_image"]:
        try:
            img = Image.open(design["background_image"])
            img = img.resize((root.winfo_width(), root.winfo_height()), Image.Resampling.LANCZOS)
            bg_img = ImageTk.PhotoImage(img)
            label = tk.Label(root, image=bg_img)
            label.image = bg_img
            label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Fehler beim Laden des Hintergrundbilds: {e}")

def oeffne_design_einstellungen(root):
    from tkinter import colorchooser, filedialog
    def speichern():
        config_path = "config.json"
        config = lade_config(config_path)
        config["background_color"] = bg_var.get()
        config["text_color"] = fg_var.get()
        config["background_image"] = img_var.get()
        speichere_config(config_path, config)
        design = lade_design_einstellungen()
        wende_design_einstellungen(root, design)
        win.destroy()

    def waehle_bg():
        farbe = colorchooser.askcolor(title="Hintergrundfarbe wählen")[1]
        if farbe: bg_var.set(farbe)
    def waehle_fg():
        farbe = colorchooser.askcolor(title="Textfarbe wählen")[1]
        if farbe: fg_var.set(farbe)
    def waehle_img():
        pfad = filedialog.askopenfilename(title="Hintergrundbild wählen", filetypes=[("Bilder", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if pfad: img_var.set(pfad)

    design = lade_design_einstellungen()
    win = tk.Toplevel(root)
    win.title("Design-Einstellungen")
    win.geometry("400x250")
    tk.Label(win, text="Hintergrundfarbe:").pack()
    bg_var = tk.StringVar(value=design["background_color"])
    tk.Entry(win, textvariable=bg_var).pack()
    tk.Button(win, text="Farbe wählen", command=waehle_bg).pack()
    tk.Label(win, text="Textfarbe:").pack()
    fg_var = tk.StringVar(value=design["text_color"])
    tk.Entry(win, textvariable=fg_var).pack()
    tk.Button(win, text="Farbe wählen", command=waehle_fg).pack()
    tk.Label(win, text="Hintergrundbild:").pack()
    img_var = tk.StringVar(value=design["background_image"])
    tk.Entry(win, textvariable=img_var).pack()
    tk.Button(win, text="Bild wählen", command=waehle_img).pack()
    tk.Button(win, text="Speichern", command=speichern).pack(pady=10)

# -------------------- HILFSFUNKTIONEN --------------------

def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def generiere_dbid(length=16):
    zeichen = string.ascii_uppercase + string.digits
    return ''.join(random.choices(zeichen, k=length))

def lade_config(dateiname):
    try:
        with open(dateiname, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden von '{dateiname}': {e}")
        return {}

def speichere_config(dateiname, config_data):
    try:
        with open(dateiname, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        logging.info(f"Datei '{dateiname}' erfolgreich gespeichert.")
        return True
    except Exception as e:
        logging.error(f"Fehler beim Speichern von '{dateiname}': {e}")
        return False

def fetch_user_details(username):
    """Holt Benutzerdetails über den FastAPI-Endpunkt /user (mit Konsolen-Logging)."""
    try:
        res = api_request("GET", "/user", params={"username": username})
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Userdetails via API: {e}")
        return None

def send_statistics():
    stats_config = lade_config("progPen.json")
    open_count = stats_config.get("open_count", 0) + 1
    stats_config["open_count"] = open_count
    speichere_config("progPen.json", stats_config)

# ==============================================================================
# MODUL-KLASSEN
# ==============================================================================

class PlayerModul:
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
             messagebox.showerror("Fehler", "Die python-vlc Bibliothek ist nicht installiert.")
             return
        try:
            instance = vlc.Instance()
            player = instance.media_player_new()
            media = instance.media_new(self.playlist_path)
            player.set_media(media)
            player.play()
        except Exception as e:
            messagebox.showerror("Fehler", f"VLC-Wiedergabe fehlgeschlagen: {e}")

    def play_with_plex(self):
        playlist_url = f"file:///{os.path.abspath(self.playlist_path)}"
        webbrowser.open(playlist_url)
        messagebox.showinfo("Startbefehl", "Externer Startbefehl gesendet.")

class UserInfoModul:
    def __init__(self, master, username):
        self.frame = ttk.Frame(master)
        self.username = username
        self.user_details = fetch_user_details(username)
        self.progpen_config = lade_config("progPen.json")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.frame, text="Mein Profil & System", font=("Arial", 16, "bold")).pack(pady=15)
        stats_config = lade_config("progPen.json")
        open_count = stats_config.get("open_count", 1)
        tk.Label(self.frame, text=f"Statistik: Programm wurde {open_count} Mal geöffnet.", fg="purple", font=("Arial", 10)).pack(pady=5)
        tk.Label(self.frame, text=f"Betriebssystem: {platform.system()}", fg="purple", font=("Arial", 10)).pack(pady=2)

        if not self.user_details:
            tk.Label(self.frame, text="⚠️ Benutzerdetails konnten nicht geladen werden.", fg="red").pack(pady=20)
            return

        info_frame = tk.LabelFrame(self.frame, text="Persönliche Daten & Schlüssel", padx=20, pady=10)
        info_frame.pack(pady=10, padx=20, fill="x")

        data = {
            "Benutzername": self.username,
            "Inhaber-Name": self.user_details.get("Name", "N/A"),
            "InhaberID": self.user_details.get("inhaberID") or self.user_details.get("InhaberID", "N/A"),
            "E-Mail": self.user_details.get("email", "N/A"),
            "Lizenz-Status": self.user_details.get("license_tier", "FREE"),
            "Sicherheitsschlüssel (Key)": self.user_details.get("securityKEY", "Kein Key")
        }

        for i, (key, value) in enumerate(data.items()):
            tk.Label(info_frame, text=f"{key}:", anchor="w", width=30).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            tk.Label(info_frame, text=value, anchor="w", fg="blue").grid(row=i, column=1, sticky="w", padx=5, pady=2)

        tk.Button(info_frame, text="⚙️ Konto online verwalten / Passwort ändern",
                  command=lambda: webbrowser.open("https://anmeldung.buch-archiv20-software.de/dashboard.php"),
                  bg="#4285F4", fg="white", font=("Arial", 9, "bold")).grid(row=len(data), column=0, columnspan=2, pady=10)

        actions_frame = tk.LabelFrame(self.frame, text="System & Links", padx=20, pady=10)
        actions_frame.pack(pady=10, padx=20, fill="x")

        links = self.progpen_config.get("PROGRAMM_LINKS", {})
        update_config = self.progpen_config.get("UPDATE_CONFIG", {})
        local_version = update_config.get("LOCAL_VERSION", "N/A")

        tk.Label(actions_frame, text=f"Installierte Version: {local_version}", font=("Arial", 10)).pack(pady=5)

        link_buttons = [
            ("🌐 Programm Webseite", "WEBSITE"),
            ("💬 Forum / Kontakt", "FORUM"),
            ("🔗 Support Formular", "SUPPORT_FORMULAR"),
            ("🐈 GitHub Repo", "GITHUB_REPO")
        ]

        for text, key in link_buttons:
            tk.Button(actions_frame, text=text,
                      command=lambda k=key: webbrowser.open(links.get(k, "about:blank"))).pack(pady=3, fill="x", padx=10)

class ArtikelModul(tk.Frame):
    """ Artikel-Verwaltungsmodul (API Integration) """

    def __init__(self, master):
        super().__init__(master)
        self.eintraege = {}
        self.status_label = None
        self.baum = None
        self.such_eintrag = None
        self.main_master = master.winfo_toplevel()
        self.create_widgets()

    def lade_datensatz(self, dbid):
        config = lade_config("config.json")
        inhaberid = config.get("inhaberid", "")
        try:
            res = api_request("GET", "/media", params={"inhaberid": inhaberid, "q": dbid})
            if res.status_code == 200:
                items = res.json()
                matching = [item for item in items if item.get("dbid") == dbid]
                if matching:
                    daten = matching[0]
                    for feld in ARTIKEL_FELDER:
                        widget = self.eintraege.get(feld)
                        if widget:
                            widget.delete(0, tk.END)
                            key_name = "zusand" if feld.lower() == "zustand" else ("bildurl" if feld.lower() == "bilderurl" else feld.lower())
                            widget.insert(0, daten.get(key_name, daten.get(feld, "")))
                    if self.status_label:
                        self.status_label.config(text=f"ℹ️ Datensatz {dbid} geladen.", fg="blue")
                    return
            messagebox.showerror("Fehler", f"Kein Eintrag mit DBid {dbid} gefunden.")
        except Exception as e:
            messagebox.showerror("Fehler", f"API-Fehler beim Laden: {e}")

    def speichern(self):
        config = lade_config("config.json")
        inhaberid = config.get("inhaberid")
        inhaber = config.get("inhaber", "")

        if not inhaberid:
            messagebox.showerror("Fehler", "Fehlende Inhaber-ID in config.json.")
            return

        payload = {
            "dbid": self.eintraege["DBid"].get() or generiere_dbid(),
            "inhaberid": str(inhaberid),
            "inhaber": str(inhaber),
            "name": self.eintraege["Name"].get(),
            "band": self.eintraege["Band"].get(),
            "doppelband": self.eintraege["Doppelband"].get(),
            "isbn10": self.eintraege["ISBN10"].get(),
            "isbn13": self.eintraege["ISBN13"].get(),
            "preis": self.eintraege["Preis"].get(),
            "typ": self.eintraege["Typ"].get(),
            "verlag": self.eintraege["Verlag"].get(),
            "bildurl": self.eintraege["BilderUrl"].get(),
            "standort": self.eintraege["Standort"].get(),
            "zusand": self.eintraege["Zustand"].get()
        }

        try:
            res = api_request("POST", "/media", json=payload)
            if res.status_code == 200:
                for widget in self.eintraege.values():
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                    elif isinstance(widget, ttk.Combobox):
                        widget.set("")
                self.status_label.config(text="✅ Artikel erfolgreich via API gespeichert!", fg="green")
                self.neue_dbid()
            else:
                self.status_label.config(text=f"❌ Fehler: {res.status_code} - {res.text}", fg="red")
        except Exception as e:
            self.status_label.config(text=f"❌ Fehler beim Speichern: {e}", fg="red")

    def suche(self):
        suchbegriff = self.such_eintrag.get()
        config = lade_config("config.json")
        inhaberid = config.get("inhaberid", "")

        try:
            res = api_request("GET", "/media", params={"inhaberid": inhaberid, "q": suchbegriff})
            if res.status_code == 200:
                ergebnisse = res.json()
                for row in self.baum.get_children():
                    self.baum.delete(row)

                artikel_cols = ["dbid", "inhaber", "name", "band", "isbn10", "isbn13", "preis", "typ", "verlag", "standort", "zusand"]
                for eintrag in ergebnisse:
                    werte = [eintrag.get(f, "") for f in artikel_cols]
                    self.baum.insert("", "end", values=werte)
                self.status_label.config(text=f"ℹ️ Suche nach: {suchbegriff}", fg="violet")
            else:
                self.status_label.config(text=f"❌ Fehler bei API-Suche: {res.status_code}", fg="red")
        except Exception as e:
            self.status_label.config(text=f"❌ Verbindungsfehler: {e}", fg="red")

    def neue_dbid(self):
        neue_id = generiere_dbid()
        self.eintraege["DBid"].delete(0, tk.END)
        self.eintraege["DBid"].insert(0, neue_id)
        if self.status_label:
            self.status_label.config(text=f"ℹ️ Neue DBid generiert: {neue_id}", fg="blue")

    def google_books_isbn_suche(self):
        isbn = self.eintraege["ISBN13"].get() or self.eintraege["ISBN10"].get()
        if not isbn:
            self.status_label.config(text="❌ Bitte eine ISBN eingeben!", fg="red")
            return
        try:
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get('totalItems', 0) > 0:
                item = data['items'][0]['volumeInfo']
                self.eintraege["Name"].delete(0, tk.END)
                self.eintraege["Name"].insert(0, item.get('title', ''))
                self.eintraege["Verlag"].delete(0, tk.END)
                self.eintraege["Verlag"].insert(0, item.get('publisher', ''))
                self.eintraege["BilderUrl"].delete(0, tk.END)
                self.eintraege["BilderUrl"].insert(0, item.get('imageLinks', {}).get('thumbnail', ''))
                self.status_label.config(text="✅ Metadaten von Google Books geladen!", fg="green")
            else:
                self.status_label.config(text="❌ Keine Ergebnisse für diese ISBN.", fg="red")
        except Exception as e:
            self.status_label.config(text=f"❌ API-Fehler: {e}", fg="red")

    def zeige_details(self, event):
        """Erweitertes Detail-Fenster mit sauberen Bezeichnungen & Cover-Bild."""
        selected_item = self.baum.selection()
        if not selected_item:
            return

        item_werte = self.baum.item(selected_item, "values")
        dbid_wert = item_werte[0]
        config = lade_config("config.json")
        inhaberid = config.get("inhaberid", "")

        try:
            res = api_request("GET", "/media", params={"inhaberid": inhaberid, "q": dbid_wert})
            if res.status_code == 200:
                results = res.json()
                details = next((item for item in results if item.get("dbid") == dbid_wert), None)
            else:
                details = None
        except Exception:
            details = None

        if not details:
            details = {
                "dbid": item_werte[0],
                "inhaber": item_werte[1],
                "name": item_werte[2],
                "band": item_werte[3],
                "isbn10": item_werte[4],
                "isbn13": item_werte[5],
                "preis": item_werte[6],
                "typ": item_werte[7],
                "verlag": item_werte[8],
                "standort": item_werte[9],
                "zusand": item_werte[10]
            }

        details_fenster = tk.Toplevel(self.main_master)
        details_fenster.title(f"Details: {details.get('name', dbid_wert)}")
        details_fenster.geometry("620x420")
        details_fenster.configure(bg="#f4f6f9")
        details_fenster.resizable(False, False)

        main_container = tk.Frame(details_fenster, bg="#f4f6f9", padx=15, pady=15)
        main_container.pack(fill="both", expand=True)

        bild_frame = tk.Frame(main_container, bg="#ffffff", bd=1, relief=tk.SOLID, width=160, height=220)
        bild_frame.pack(side="left", anchor="n", padx=(0, 15))
        bild_frame.pack_propagate(False)

        bild_label = tk.Label(bild_frame, text="Kein Cover", bg="#ffffff", fg="#888888")
        bild_label.pack(expand=True, fill="both")

        bild_url = details.get("bildurl") or details.get("bild_url")
        if bild_url:
            try:
                img_res = requests.get(bild_url, timeout=5)
                if img_res.status_code == 200:
                    img_data = Image.open(io.BytesIO(img_res.content))
                    img_data.thumbnail((150, 210), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img_data)
                    bild_label.config(image=photo, text="")
                    bild_label.image = photo
            except Exception as e:
                logging.warning(f"Cover-Bild konnte nicht geladen werden: {e}")

        info_frame = tk.Frame(main_container, bg="#f4f6f9")
        info_frame.pack(side="left", fill="both", expand=True)

        tk.Label(
            info_frame,
            text=details.get("name", "Unbenannt"),
            font=("Arial", 14, "bold"),
            bg="#f4f6f9",
            fg="#2c3e50",
            wraplength=380,
            justify="left"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        feld_zuordnung = [
            ("DB-ID", details.get("dbid", "-")),
            ("Inhaber", details.get("inhaber", "-")),
            ("Band / Doppelband", f"{details.get('band', '')} / {details.get('doppelband', '')}".strip(" /")),
            ("ISBN 10 / 13", f"{details.get('isbn10', '')} | {details.get('isbn13', '')}".strip(" |")),
            ("Typ / Kategorie", details.get("typ", "-")),
            ("Verlag", details.get("verlag", "-")),
            ("Preis", f"{details.get('preis', '-')} €" if details.get('preis') else "-"),
            ("Standort", details.get("standort", "-")),
            ("Zustand", details.get("zusand") or details.get("zustand", "-"))
        ]

        for idx, (label_txt, wert_txt) in enumerate(feld_zuordnung, start=1):
            tk.Label(
                info_frame,
                text=f"{label_txt}:",
                font=("Arial", 9, "bold"),
                bg="#f4f6f9",
                fg="#555555"
            ).grid(row=idx, column=0, sticky="w", pady=2)

            tk.Label(
                info_frame,
                text=wert_txt if wert_txt else "-",
                font=("Arial", 9),
                bg="#f4f6f9",
                fg="#000000"
            ).grid(row=idx, column=1, sticky="w", padx=(10, 0), pady=2)

        tk.Button(
            details_fenster,
            text="Schließen",
            command=details_fenster.destroy,
            width=12,
            bg="#e0e0e0"
        ).pack(side="bottom", pady=10)

    def create_widgets(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        input_frame_container = tk.Frame(self, padx=10, pady=10, relief=tk.GROOVE, bd=2)
        input_frame_container.grid(row=0, column=0, sticky="nsew")

        search_frame_container = tk.Frame(self, padx=10, pady=10, relief=tk.GROOVE, bd=2)
        search_frame_container.grid(row=0, column=1, sticky="nsew")

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

        tk.Button(input_frame, text="🔄 Neue DBid", command=self.neue_dbid).grid(row=len(ARTIKEL_FELDER), column=0, pady=10, sticky="w")
        tk.Button(input_frame, text="🔍 ISBN/Google Suche", command=self.google_books_isbn_suche).grid(row=len(ARTIKEL_FELDER), column=1, pady=10, sticky="e")
        tk.Button(input_frame, text="💾 Speichern", command=self.speichern, bg="#90EE90").grid(row=len(ARTIKEL_FELDER) + 1, column=0, columnspan=2, pady=5, sticky="we")

        search_frame_container.columnconfigure(0, weight=1)
        search_frame_container.rowconfigure(3, weight=1)

        tk.Label(search_frame_container, text="🔍 Suche (Name, ISBN oder DBID)").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        self.such_eintrag = tk.Entry(search_frame_container, width=50)
        self.such_eintrag.grid(row=1, column=0, padx=(0, 5), sticky="we")
        tk.Button(search_frame_container, text="Suchen", command=self.suche, bg="#ADD8E6").grid(row=1, column=1, sticky="e")

        self.baum = ttk.Treeview(search_frame_container, columns=("DBid","Inhaber", "Name", "Band", "ISBN10", "ISBN13", "Preis", "Typ", "Verlag", "Standort", "Zustand"), show="headings")
        for col in self.baum["columns"]:
            self.baum.heading(col, text=col)

        self.baum.column("DBid", width=80, anchor='center')
        self.baum.column("Name", width=200)
        self.baum.column("Verlag", width=100)

        self.baum.grid(row=3, column=0, columnspan=2, padx=(0, 5), pady=5, sticky="nsew")
        self.baum.bind("<Double-1>", self.zeige_details)

        scrollbar = ttk.Scrollbar(search_frame_container, orient="vertical", command=self.baum.yview)
        self.baum.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=3, column=2, sticky="ns", padx=(0, 5), pady=5)

        self.status_label = tk.Label(self, text="ℹ️ Bereit", anchor="w", fg="gray", bd=1, relief=tk.SUNKEN)
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="we", padx=10, pady=5)
        self.neue_dbid()

class AnimeFanSubSystem:
    """ Anime Fan Sub System (API Integration) """

    def __init__(self, master):
        self.frame = ttk.Frame(master)
        self.master = master.winfo_toplevel()
        self.eintraege = {}
        self.status_label = None
        self.create_widgets()
        self.load_all_anime()

    def neue_afssid(self):
        return generiere_dbid(length=10)

    def save_to_db(self):
        config = lade_config("config.json")
        inhaberid = config.get("inhaberid", "")

        payload = {
            "afssid": self.eintraege["AFSSID"].get(),
            "titel": self.eintraege["Titel"].get(),
            "episoden": self.eintraege["Episoden"].get(),
            "episoden_anzahl": str(self.eintraege["Anzahl Episoden"].get() or "0"),
            "cover": self.eintraege["Cover URL"].get(),
            "untertitel": self.eintraege["Untertitel Sprache"].get(),
            "audio": self.eintraege["Audio Sprache"].get(),
            "playlist_local": self.eintraege["Lokale Playlist"].get(),
            "playlist_url": self.eintraege["Online Playlist"].get(),
            "medium": self.eintraege["Medium"].get(),
            "fansub_name": self.eintraege["Fansub Name"].get(),
            "fansub_url": self.eintraege["Fansub URL"].get(),
            "inhaberid": str(inhaberid)
        }

        try:
            res = api_request("POST", "/anime", json=payload)
            if res.status_code == 200:
                self.status_label.config(text=f"✅ Anime gespeichert via API: {payload['afssid']}", fg="green")
                self.clear_form()
                self.load_all_anime()
            else:
                self.status_label.config(text=f"❌ API-Fehler: {res.status_code}", fg="red")
        except Exception as e:
            self.status_label.config(text=f"❌ Fehler: {e}", fg="red")

    def search_anime(self, query=None):
        if query is None:
            query = self.search_entry.get()

        try:
            res = api_request("GET", "/anime", params={"q": query})
            if res.status_code == 200:
                ergebnisse = res.json()
                for row in self.tree.get_children():
                    self.tree.delete(row)
                for eintrag in ergebnisse:
                    self.tree.insert("", "end", values=(
                        eintrag.get("afssid", ""),
                        eintrag.get("titel", ""),
                        eintrag.get("episoden", ""),
                        eintrag.get("medium", "N/A"),
                        eintrag.get("playlist_local", "N/A")
                    ))
                self.status_label.config(text=f"ℹ️ {len(ergebnisse)} Anime-Einträge gefunden.", fg="blue")
        except Exception as e:
            self.status_label.config(text=f"❌ Fehler bei Anime-Suche: {e}", fg="red")

    def load_all_anime(self):
        self.search_anime(query="")

    def clear_form(self):
        for key in AFSS_FIELDS:
            widget = self.eintraege[key]
            widget.delete(0, tk.END)
            if isinstance(widget, ttk.Combobox):
                widget.set("")
        self.eintraege["AFSSID"].config(state='normal')
        self.eintraege["AFSSID"].insert(0, self.neue_afssid())
        if self.status_label:
            self.status_label.config(text="ℹ️ Formular geleert.", fg="gray")

    def create_treeview(self):
        cols = ("AFSSID", "Titel", "Episoden", "Medium", "Lokaler Pfad")
        tree = ttk.Treeview(self.search_result_frame, columns=cols, show='headings', height=15)
        for col in cols:
            tree.heading(col, text=col)
        tree.column("AFSSID", width=100, anchor='center')
        tree.column("Titel", width=250)
        tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(self.search_result_frame, orient="vertical", command=tree.yview)
        vsb.pack(side='right', fill='y')
        tree.configure(yscrollcommand=vsb.set)
        return tree

    def create_widgets(self):
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.status_label = tk.Label(self.frame, text="ℹ️ Initialisiere...", anchor="w", fg="gray", bd=1, relief=tk.SUNKEN)
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="we", padx=10, pady=5)

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

        button_frame = tk.Frame(input_frame)
        button_frame.grid(row=len(AFSS_FIELDS), column=0, columnspan=2, pady=10)
        tk.Button(button_frame, text="💾 Speichern/Update", command=self.save_to_db, bg="#90EE90").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="❌ Neueingabe", command=self.clear_form, bg="#FFD700").pack(side=tk.LEFT, padx=5)

        search_container = tk.LabelFrame(self.frame, text="Suche & Ergebnisse", padx=10, pady=10)
        search_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        search_container.columnconfigure(0, weight=1)
        search_container.rowconfigure(2, weight=1)

        search_input_frame = tk.Frame(search_container)
        search_input_frame.grid(row=0, column=0, sticky="we", pady=(0, 10))
        search_input_frame.columnconfigure(0, weight=1)

        tk.Label(search_input_frame, text="Suche AFSSID/Titel:").grid(row=0, column=0, sticky="w")
        self.search_entry = tk.Entry(search_input_frame, width=50)
        self.search_entry.grid(row=1, column=0, padx=(0, 5), sticky="we")
        tk.Button(search_input_frame, text="🔍 Suchen", command=self.search_anime, bg="#ADD8E6").grid(row=1, column=1, sticky="e")

        self.search_result_frame = tk.Frame(search_container)
        self.search_result_frame.grid(row=2, column=0, sticky="nsew")
        self.tree = self.create_treeview()

        play_button_frame = tk.Frame(search_container)
        play_button_frame.grid(row=3, column=0, sticky="e", pady=5)
        tk.Button(play_button_frame, text="▶️ Lokale Playlist Abspielen", command=self.play_local_playlist, bg="#90EE90").pack(side=tk.RIGHT, padx=5)

    def play_local_playlist(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Auswahl fehlt", "Bitte wählen Sie einen Anime-Eintrag aus.")
            return
        item_data = self.tree.item(selected_item, 'values')
        playlist_path = item_data[4]
        if playlist_path and playlist_path not in ["N/A", "Kein Pfad", ""]:
            player_window = tk.Toplevel(self.master)
            PlayerModul(player_window, playlist_path)
        else:
             messagebox.showwarning("Fehlende Daten", "Keine lokale Playlist gefunden.")

class FilmSerienModul(tk.Frame):
    """ Film & Serien Modul (API Integration) """

    def __init__(self, master):
        super().__init__(master)
        self.api_key = self.lade_api_key()
        self.eintraege = {}
        self.create_widgets()

    def lade_api_key(self):
        config = lade_config("progPen.json")
        return config.get("TMDB_API_KEY", "")

    def neue_dbid_fuer_feld(self):
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
            url = f"https://api.jikan.moe/v4/anime?q={titel}&limit=1"
            try:
                res = requests.get(url, timeout=5).json()
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
            if not self.api_key:
                messagebox.showerror("Fehler", "Kein TMDB API Key in progPen.json gefunden!")
                return
            url = f"https://api.themoviedb.org/3/search/multi?api_key={self.api_key}&query={titel}&language=de-DE"
            try:
                res = requests.get(url, timeout=5).json()
                item = res['results'][0]
                self.fuelle_felder(
                    titel=item.get('title') or item.get('name'),
                    id_val=item.get('id'),
                    jahr=(item.get('release_date') or item.get('first_air_date', "0000"))[:4],
                    genre="TMDB",
                    descr=item.get('overview'),
                    img=f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
                )
            except:
                messagebox.showerror("TMDB", "Keine Film-Daten gefunden.")

    def fuelle_felder(self, titel, id_val, jahr, genre, descr, img):
        self.eintraege["Titel"].delete(0, tk.END)
        self.eintraege["Titel"].insert(0, titel)
        self.eintraege["ID"].delete(0, tk.END)
        self.eintraege["ID"].insert(0, str(id_val))
        self.eintraege["Jahr"].delete(0, tk.END)
        self.eintraege["Jahr"].insert(0, str(jahr))
        self.eintraege["Genre"].delete(0, tk.END)
        self.eintraege["Genre"].insert(0, genre)
        self.eintraege["Beschreibung"].delete("1.0", tk.END)
        self.eintraege["Beschreibung"].insert("1.0", descr or "")
        self.eintraege["Cover_URL"].delete(0, tk.END)
        self.eintraege["Cover_URL"].insert(0, img or "")
        messagebox.showinfo("Erfolg", "Daten wurden ausgefüllt!")

    def speichern(self):
        config = lade_config("config.json")
        inhaberid = config.get("inhaberid", "")

        payload = {
            "dbid": self.eintraege["DBid"].get(),
            "titel": self.eintraege["Titel"].get(),
            "typ": self.eintraege["Typ"].get(),
            "format": self.eintraege["Format"].get(),
            "genre": self.eintraege["Genre"].get(),
            "jahr": self.eintraege["Jahr"].get(),
            "tmdb_mal_id": self.eintraege["ID"].get(),
            "standort": self.eintraege["Standort"].get(),
            "zustand": self.eintraege["Zustand"].get(),
            "beschreibung": self.eintraege["Beschreibung"].get("1.0", tk.END).strip(),
            "cover_url": self.eintraege["Cover_URL"].get(),
            "inhaberid": str(inhaberid)
        }

        try:
            res = api_request("POST", "/filme", json=payload)
            if res.status_code == 200:
                messagebox.showinfo("Erfolg", "Film/Serie erfolgreich via API gespeichert!")
                self.neue_dbid_fuer_feld()
            else:
                messagebox.showerror("API Fehler", f"Fehler {res.status_code}: {res.text}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Verbindungsfehler zur API: {e}")

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

        tk.Label(form_frame, text="Beschreibung").grid(row=len(felder_liste), column=0, sticky="nw")
        self.eintraege["Beschreibung"] = tk.Text(form_frame, height=5, width=38)
        self.eintraege["Beschreibung"].grid(row=len(felder_liste), column=1, pady=5)

        btn_f = tk.Frame(form_frame)
        btn_f.grid(row=len(felder_liste)+1, column=0, columnspan=2, pady=10)
        tk.Button(btn_f, text="🔍 Info abrufen (TMDB/MAL)", command=self.info_abrufen, bg="#add8e6").pack(side="left", padx=5)
        tk.Button(btn_f, text="💾 In Datenbank speichern", command=self.speichern, bg="#90ee90", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        form_frame.pack()
        self.neue_dbid_fuer_feld()

class SchallplattenModul(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.bilder = {}
        self.main_master = master.winfo_toplevel()
        config = lade_config("config.json")
        self.API_URL = config.get("api_url")
        self.API_TOKEN = config.get("token")

        if not self.API_URL or not self.API_TOKEN:
             tk.Label(self, text="⚠️ Konfiguration (config.json) unvollständig für Schallplatten-API.", fg="red").pack(pady=20)
             return
        self.create_widgets()

    def create_widgets(self):
        main_search_frame = tk.Frame(self)
        main_search_frame.pack(pady=10, padx=10, fill="x")

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

        result_frame = tk.Frame(self)
        result_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.listbox = tk.Listbox(result_frame, width=80, height=20)
        self.listbox.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.listbox.bind('<Double-1>', self.oeffnen)
        self.listbox.bind('<<ListboxSelect>>', self.bild_anzeigen)

        self.bild_label = tk.Label(result_frame, text="Bild hier", width=30, height=15, relief="solid")
        self.bild_label.pack(side="right", fill="y")

    def suche(self):
        params = {"token": self.API_TOKEN}
        q = []
        if self.eintrag_name.get(): q.append(self.eintrag_name.get())
        if self.eintrag_nummer.get(): q.append(self.eintrag_nummer.get())
        if self.eintrag_dbid.get(): q.append(self.eintrag_dbid.get())
        params["q"] = " ".join(q)

        try:
            r = requests.get(self.API_URL, params=params, timeout=5)
            r.raise_for_status()
            daten = r.json()
            self.listbox.delete(0, tk.END)
            self.bilder.clear()
            for eintrag in daten:
                text = f"{eintrag.get('name', 'N/A')} [{eintrag.get('plattennummer', 'N/A')}] | Genre: {eintrag.get('genre', 'N/A')} | DBID: {eintrag.get('dbid', 'N/A')}"
                link = f"https://schall.philipp-lindner-server.de/details.php?id={eintrag.get('id')}"
                self.listbox.insert(tk.END, (text, link, eintrag.get('bild_url')))
        except Exception as e:
            messagebox.showerror("Fehler bei der Suche", str(e))

    def oeffnen(self, evt):
        auswahl = self.listbox.curselection()
        if auswahl:
            eintrag = self.listbox.get(auswahl[0])
            webbrowser.open(eintrag[1])

    def bild_anzeigen(self, evt):
        auswahl = self.listbox.curselection()
        if auswahl:
            eintrag = self.listbox.get(auswahl[0])
            bild_url = eintrag[2]
            if not bild_url:
                self.bild_label.config(text="Kein Bild verfügbar", image="")
                return
            try:
                r = requests.get(bild_url, timeout=5)
                img = Image.open(io.BytesIO(r.content))
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                self.bilder['current_image'] = ImageTk.PhotoImage(img)
                self.bild_label.config(image=self.bilder['current_image'], text="")
            except Exception:
                self.bild_label.config(text="Bild konnte nicht geladen werden", image="")

class GlobaleSucheModul(tk.Frame):
    """ Globale Suche (API Integration) """

    def __init__(self, master, notebook_referenz):
        super().__init__(master)
        self.notebook = notebook_referenz
        self.create_widgets()

    def suche_starten(self, event=None):
        begriff = self.suche_entry.get().strip()
        if len(begriff) < 3:
            messagebox.showwarning("Suche", "Bitte mindestens 3 Zeichen eingeben.")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        config = lade_config("config.json")
        inhaberid = config.get("inhaberid", "")

        # 1. Medien / Bücher Suche
        try:
            r1 = api_request("GET", "/media", params={"inhaberid": inhaberid, "q": begriff})
            if r1.status_code == 200:
                for row in r1.json():
                    self.tree.insert("", "end", values=(row.get('dbid'), row.get('name'), row.get('typ'), row.get('standort'), "BÜCHER_TAB"))
        except Exception as e:
            logging.error(f"Suche Media Fehler: {e}")

        # 2. Anime Suche
        try:
            r2 = api_request("GET", "/anime", params={"q": begriff})
            if r2.status_code == 200:
                for row in r2.json():
                    self.tree.insert("", "end", values=(row.get('afssid'), row.get('titel'), "Anime (AFSS)", row.get('playlist_local', 'Digital'), "ANIME_TAB"))
        except Exception as e:
            logging.error(f"Suche Anime Fehler: {e}")

        # 3. Filme / Serien Suche
        try:
            r3 = api_request("GET", "/filme", params={"inhaberid": inhaberid, "q": begriff})
            if r3.status_code == 200:
                for row in r3.json():
                    self.tree.insert("", "end", values=(row.get('dbid'), row.get('titel'), row.get('typ'), row.get('standort'), "VIDEO_TAB"))
        except Exception as e:
            logging.error(f"Suche Filme Fehler: {e}")

    def on_double_click(self, event):
        item_id = self.tree.selection()[0]
        werte = self.tree.item(item_id, "values")
        dbid = werte[0]
        ziel_tab_kennung = werte[4]

        tab_mapping = {
            "ANIME_TAB": 1,
            "BÜCHER_TAB": 2,
            "VIDEO_TAB": 4
        }

        if ziel_tab_kennung in tab_mapping:
            idx = tab_mapping[ziel_tab_kennung]
            self.notebook.select(idx)
            messagebox.showinfo("Springe zu...", f"Wechsle zu Tab...\nID {dbid} wird geladen.")
            ziel_modul = self.notebook.winfo_children()[idx]
            if hasattr(ziel_modul, "lade_datensatz"):
                ziel_modul.lade_datensatz(dbid)

    def create_widgets(self):
        lbl = tk.Label(self, text="🔎 Globale Datenbank-Suche (via API)", font=("Arial", 14, "bold"), pady=10)
        lbl.pack()

        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=20)

        self.suche_entry = tk.Entry(search_frame, font=("Arial", 12))
        self.suche_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.suche_entry.bind("<Return>", self.suche_starten)

        btn = tk.Button(search_frame, text="Suchen", command=self.suche_starten, bg="#90ee90", width=15)
        btn.pack(side="left")

        columns = ("ID", "Titel", "Typ", "Standort", "InternerTyp")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("ID", text="Medien-ID")
        self.tree.heading("Titel", text="Titel / Name")
        self.tree.heading("Typ", text="Kategorie")
        self.tree.heading("Standort", text="Lagerort")
        self.tree.column("InternerTyp", width=0, stretch=tk.NO)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree.bind("<Double-1>", self.on_double_click)

# -------------------- HAUPT-GUI LOGIK --------------------

def zeige_hauptfenster(username):
    global hauptfenster
    hauptfenster = tk.Tk()
    hauptfenster.title(f"Bücherei 2.0 Online - Angemeldet als: {username}")
    hauptfenster.geometry("1400x900")

    menubar = tk.Menu(hauptfenster)
    design_menu = tk.Menu(menubar, tearoff=0)
    design_menu.add_command(label="Design-Einstellungen...", command=lambda: oeffne_design_einstellungen(hauptfenster))
    menubar.add_cascade(label="Design", menu=design_menu)

    def logout():
        hauptfenster.destroy()
        start_login_fenster()

    menubar.add_command(label="Logout", command=logout)
    hauptfenster.config(menu=menubar)

    notebook = ttk.Notebook(hauptfenster)

    user_info_instance = UserInfoModul(notebook, username)
    notebook.add(user_info_instance.frame, text='👤 Mein Profil')

    afss_instance = AnimeFanSubSystem(notebook)
    notebook.add(afss_instance.frame, text='📺 Anime Fan Sub System')

    medien_frame = ArtikelModul(notebook)
    notebook.add(medien_frame, text='📚 Medienverwaltung')

    schallplatten_frame = SchallplattenModul(notebook)
    notebook.add(schallplatten_frame, text='🎵 Schallplatten')

    medien_tab = FilmSerienModul(notebook)
    notebook.add(medien_tab, text="🎬 Video-Archiv")

    suche_tab = GlobaleSucheModul(notebook, notebook)
    notebook.add(suche_tab, text="🔍 Globale Suche")

    notebook.pack(expand=True, fill='both', padx=10, pady=10)

    global status_label
    status_label = tk.Label(hauptfenster, text="Bereit.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_label.pack(side=tk.BOTTOM, fill=tk.X)

    design = lade_design_einstellungen()
    wende_design_einstellungen(hauptfenster, design)

    hauptfenster.mainloop()

# -------------------- LOGIN LOGIK --------------------

def start_login_fenster():
    login_fenster = tk.Tk()
    login_fenster.title("🔐 Login")
    login_fenster.geometry("450x400")

    try:
        img = Image.open("logo.png")
        img = img.resize((295, 150), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(login_fenster, image=photo)
        logo_label.image = photo
        logo_label.pack(pady=10)
    except Exception:
        tk.Label(login_fenster, text="Bücherei 2.0", font=("Arial", 24, "bold")).pack(pady=10)

    login_frame = tk.Frame(login_fenster)
    login_frame.pack(pady=10)

    tk.Label(login_frame, text="Benutzername").grid(row=0, column=0, pady=5, sticky="w")
    eintrag_benutzer = tk.Entry(login_frame, width=30)
    eintrag_benutzer.grid(row=0, column=1, pady=5)

    tk.Label(login_frame, text="Passwort").grid(row=1, column=0, pady=5, sticky="w")
    eintrag_passwort = tk.Entry(login_frame, show="*", width=30)
    eintrag_passwort.grid(row=1, column=1, pady=5)

    def execute_login():
        benutzer = eintrag_benutzer.get().strip()
        passwort = eintrag_passwort.get()
        users = lade_config("users.json")

        if not users:
            messagebox.showerror("Fehler", "Benutzerdaten (users.json) konnten nicht geladen werden.")
            return

        passwort_hash = md5_hash(passwort)

        if benutzer in users and users[benutzer] == passwort_hash:
            login_fenster.destroy()
            zeige_hauptfenster(benutzer)
        else:
            messagebox.showerror("Fehler", "Login fehlgeschlagen!")

    button_frame = tk.Frame(login_fenster)
    button_frame.pack(pady=20)
    tk.Button(button_frame, text="Login", command=execute_login, bg="#90EE90", width=15).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="Neu Registrieren", command=lambda: webbrowser.open("https://anmeldung.buch-archiv20-software.de/"), bg="#ADD8E6", width=15).pack(side=tk.LEFT, padx=10)

    login_fenster.mainloop()

# ===================== MAIN BLOCK =====================

if __name__ == "__main__":
    send_statistics()
    start_login_fenster()
