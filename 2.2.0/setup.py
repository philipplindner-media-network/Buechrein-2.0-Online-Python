import json
import os
import tkinter as tk
from tkinter import messagebox
import requests

# --- Konfiguration der API (Standardwerte) ---
DEFAULT_API_URL = "https://api-buch-archiv20-software.route64.de/"
DEFAULT_API_SECRET_KEY = "Bucherei2APID"
DEFAULT_SCHALL_TOKEN = "51e5dc0287c199cb2d80a4f18ba16fbb"

# -------------------- Initialisierung von progPen.json --------------------

def init_progpen_config():
    """Erstellt eine Standard progPen.json, falls sie noch nicht existiert."""
    progpen_data = {
        "open_count": 0,
        "STATISTICS_URL": "https://api-buch-archiv20-software.route64.de/stats",
        "TMDB_API_KEY": "",
        "UPDATE_CONFIG": {
            "LOCAL_VERSION": "2.1.0"
        },
        "PROGRAMM_LINKS": {
            "WEBSITE": "https://buch-archiv20-software.de/",
            "FORUM": "https://kichan-forum.any64.de/",
            "SUPPORT_FORMULAR": "https://buch-archiv20-software.de/support",
            "GITHUB_REPO": "https://github.com/philipp-lindner/buecherei2.0"
        }
    }
    if not os.path.exists("progPen.json"):
        try:
            with open("progPen.json", "w", encoding="utf-8") as f:
                json.dump(progpen_data, f, indent=4, ensure_ascii=False)
            print("✅ progPen.json erfolgreich initialisiert.")
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen von progPen.json: {e}")

# -------------------- GUI für API-Einstellungen --------------------

def api_config_gui(main_root):
    """Zeigt eine GUI zur Eingabe der API-Schlüssel und Inhaberdaten."""
    success = False

    def save_and_proceed():
        nonlocal success

        api_key = entry_api_key.get().strip()
        schall_token = entry_token.get().strip()
        inhaber_name = entry_inhaber.get().strip()
        inhaber_id = entry_inhaber_id.get().strip()

        if not api_key or not inhaber_name or not inhaber_id:
            messagebox.showwarning("Fehlende Daten", "API Key, Inhaber Name und Inhaber ID sind Pflichtfelder.")
            return

        config_data = {
            "api_url": DEFAULT_API_URL,
            "api_secret_key": api_key,
            "token": schall_token,
            "inhaber": inhaber_name,
            "inhaberid": inhaber_id
        }

        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print("✅ config.json erfolgreich gespeichert.")
            success = True
            config_window.destroy()
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern von config.json fehlgeschlagen: {e}")

    config_window = tk.Toplevel(main_root)
    config_window.title("Bücherei 2.0 API-Einrichtung")
    config_window.geometry("480x420")

    tk.Label(config_window, text="API-Daten und Schlüssel", font=("Arial", 11, "bold")).pack(pady=10)

    api_frame = tk.Frame(config_window, padx=10, pady=10, relief=tk.GROOVE, borderwidth=1)
    api_frame.pack(pady=5, padx=20, fill="x")

    tk.Label(api_frame, text="API Base URL:").grid(row=0, column=0, sticky="w", pady=4)
    tk.Label(api_frame, text=DEFAULT_API_URL, fg="gray").grid(row=0, column=1, sticky="w", pady=4)

    tk.Label(api_frame, text="API Secret Key:", fg="blue").grid(row=1, column=0, sticky="w", pady=4)
    entry_api_key = tk.Entry(api_frame, width=32)
    entry_api_key.insert(0, DEFAULT_API_SECRET_KEY)
    entry_api_key.grid(row=1, column=1, pady=4)

    tk.Label(api_frame, text="Schallplatten API Token:").grid(row=2, column=0, sticky="w", pady=4)
    entry_token = tk.Entry(api_frame, width=32)
    entry_token.insert(0, DEFAULT_SCHALL_TOKEN)
    entry_token.grid(row=2, column=1, pady=4)

    tk.Label(config_window, text="Inhaber-Informationen", font=("Arial", 11, "bold")).pack(pady=10)

    inhaber_frame = tk.Frame(config_window, padx=10, pady=10, relief=tk.GROOVE, borderwidth=1)
    inhaber_frame.pack(pady=5, padx=20, fill="x")

    tk.Label(inhaber_frame, text="Inhaber Name:").grid(row=0, column=0, sticky="w", pady=4)
    entry_inhaber = tk.Entry(inhaber_frame, width=32)
    entry_inhaber.insert(0, "Philipp Lindner")
    entry_inhaber.grid(row=0, column=1, pady=4)

    tk.Label(inhaber_frame, text="Inhaber ID:").grid(row=1, column=0, sticky="w", pady=4)
    entry_inhaber_id = tk.Entry(inhaber_frame, width=32)
    entry_inhaber_id.insert(0, "1")
    entry_inhaber_id.grid(row=1, column=1, pady=4)

    tk.Button(
        config_window,
        text="Speichern & Setup abschließen",
        command=save_and_proceed,
        bg="#90EE90",
        font=("Arial", 10, "bold")
    ).pack(pady=20)

    config_window.grab_set()
    main_root.wait_window(config_window)

    return success

# -------------------- Hauptfunktion --------------------

def run_setup(root_to_destroy):
    root_to_destroy.withdraw()

    # 1. progPen.json initialisieren
    init_progpen_config()

    # 2. API-Konfiguration abfragen und config.json erstellen
    success = api_config_gui(root_to_destroy)

    if success:
        messagebox.showinfo("Setup", "Setup erfolgreich abgeschlossen! Das Programm ist nun vollständig auf API-Betrieb konfiguriert.")
    else:
        messagebox.showerror("Setup", "Setup abgebrochen oder fehlgeschlagen.")

    root_to_destroy.destroy()

# -------------------- GUI Start --------------------

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Setup - Bücherei 2.0")
    root.geometry("320x160")

    tk.Label(root, text="Bücherei 2.0 Setup", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(root, text="Konfiguriert die API-Schnittstelle.").pack()

    tk.Button(root, text="Setup jetzt starten", command=lambda: run_setup(root), bg="#90EE90", font=("Arial", 10, "bold")).pack(pady=15)

    root.mainloop()
