import json
import os
import mysql.connector
import tkinter as tk
from tkinter import messagebox, ttk
import hashlib
import xml.etree.ElementTree as ET
import requests

# --- Konfiguration der API (Standardwerte) ---
DEFAULT_API_URL = "https://philipp-lindner-server.de/schalplatte/api/search.php"
DEFAULT_API_TOKEN = "51e5dc0287c199cb2d80a4f18ba16fbb"
SERVER_LIST_URL = "https://server.buch-archiv20-software.de/server_liste.json"

# -------------------- JSON-Laden und Serverauswahl --------------------

def load_servers_from_json(url):
    """Lädt Serverinformationen direkt von der Web-URL als JSON."""
    servers = []
    try:
        print(f"Lade Serverliste von: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            for server_data in data:
                required_keys = ["host", "user", "pass", "dbname"]
                if all(key in server_data and server_data[key] for key in required_keys):

                    # Korrektur 1: Schlüssel "pass" in "password" umbenennen
                    server_data["password"] = server_data.pop("pass")

                    # Korrektur 2: Schlüssel "dbname" in "database" umbenennen (DER FEHLER WURDE HIER BEHOBEN)
                    server_data["database"] = server_data.pop("dbname")

                    if "sn" not in server_data:
                        server_data["sn"] = "Unbekannter Server"
                    servers.append(server_data)

        if not servers:
             messagebox.showwarning("Laden", "JSON-Datei von der URL geladen, aber keine gültigen Server-Einträge gefunden.")
             print("Es wurden keine gültigen Server-Einträge gefunden.")

    except requests.exceptions.Timeout:
        messagebox.showerror("Netzwerkfehler", "Zeitüberschreitung beim Laden der Serverliste von der URL.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Netzwerkfehler", f"Fehler beim Laden der Serverliste von der URL: {e}")
    except json.JSONDecodeError:
        messagebox.showerror("Fehler", "Fehler beim Parsen der JSON-Datei. Die Serverliste ist möglicherweise ungültig.")
    except Exception as e:
        messagebox.showerror("Allgemeiner Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    return servers

# -------------------- GUI für Serverauswahl (wenn JSON erfolgreich) --------------------

def server_selection_gui(servers, main_root):
    """Zeigt eine GUI zur Auswahl des Servers und liefert die rohen DB-Daten zurück."""

    server_names = [s['sn'] for s in servers]
    selected_db_data = {}

    def select_and_close():
        nonlocal selected_db_data
        selected_name = combo_server.get()
        if not selected_name:
            messagebox.showwarning("Auswahl fehlt", "Bitte wählen Sie einen Server aus.")
            return

        selected_data = next((s for s in servers if s['sn'] == selected_name), None)

        if selected_data:
            # DIESER ABSCHNITT FUNKTIONIERT NUN, DA DIE SCHLÜSSEL UMBENANNT WURDEN
            selected_db_data = {
                "host": selected_data["host"],
                "user": selected_data["user"],
                "password": selected_data["password"],
                "database": selected_data["database"] # <--- KeyError: 'database' ist behoben
            }
            selection_window.destroy()
        else:
            messagebox.showerror("Fehler", "Serverdaten konnten nicht gefunden werden.")


    selection_window = tk.Toplevel(main_root)
    selection_window.title("1/3 Server Auswahl (von URL)")
    selection_window.geometry("400x150")

    tk.Label(selection_window, text="Bitte wählen Sie den Datenbankserver:").pack(pady=10)

    combo_server = ttk.Combobox(selection_window, values=server_names, state="readonly", width=40)
    if server_names:
        combo_server.set(server_names[0])
    combo_server.pack(pady=5)

    tk.Button(selection_window, text="Weiter zur Prüfung", command=select_and_close).pack(pady=10)

    selection_window.grab_set()
    main_root.wait_window(selection_window)

    return selected_db_data

# ... (Der Rest des Codes der setup.py bleibt unverändert) ...

# Hier ist der Rest des Codes, damit Sie die komplette Datei haben:
def manual_config_gui(main_root):
    """Zeigt eine GUI zur manuellen Eingabe der DB-Konfiguration (Fallback)."""
    manual_db_data = {}

    def save_and_continue():
        nonlocal manual_db_data

        host = entry_host.get()
        user = entry_user.get()
        password = entry_password.get()
        database = entry_database.get()

        if not host or not user or not database:
            messagebox.showwarning("Fehlende Daten", "Host, Benutzer und Datenbankname sind Pflichtfelder.")
            return

        manual_db_data = {
            "host": host,
            "user": user,
            "password": password,
            "database": database
        }
        manual_window.destroy()

    manual_window = tk.Toplevel(main_root)
    manual_window.title("1/3 Manuelle DB-Eingabe (Fallback)")
    manual_window.geometry("400x300")

    tk.Label(manual_window, text="Laden der Serverliste fehlgeschlagen.", fg="red", font=("Arial", 10, "bold")).pack(pady=5)
    tk.Label(manual_window, text="Bitte geben Sie die Datenbank-Zugangsdaten manuell ein:").pack(pady=5)

    tk.Label(manual_window, text="Host:").pack(pady=2)
    entry_host = tk.Entry(manual_window, width=35)
    entry_host.pack()

    tk.Label(manual_window, text="Benutzername:").pack(pady=2)
    entry_user = tk.Entry(manual_window, width=35)
    entry_user.pack()

    tk.Label(manual_window, text="Passwort:").pack(pady=2)
    entry_password = tk.Entry(manual_window, width=35, show="*")
    entry_password.pack()

    tk.Label(manual_window, text="Datenbankname:").pack(pady=2)
    entry_database = tk.Entry(manual_window, width=35)
    entry_database.pack()

    tk.Button(manual_window, text="Speichern und prüfen", command=save_and_continue, bg="yellow").pack(pady=10)

    manual_window.grab_set()
    main_root.wait_window(manual_window)

    return manual_db_data

# -------------------- Konfigurationsprüfung und Speicherung --------------------

def config_review_gui(initial_db_config, initial_api_token, main_root, inhaber_data):
    """Zeigt ein Fenster zur Prüfung und manuellen Korrektur der Konfiguration."""

    final_configs = {}

    def save_and_proceed():
        nonlocal final_configs

        # 1. DB-Konfiguration speichern (für DB-Abruf)
        db_config_final = {
            "host": entry_host.get(),
            "user": entry_user.get(),
            "password": entry_password.get(),
            "database": entry_database.get()
        }

        try:
            with open("db_config.json", "w") as f:
                json.dump(db_config_final, f, indent=4)
            print("✅ db_config.json erfolgreich gespeichert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern von db_config.json fehlgeschlagen: {e}")
            return

        # 2. config.json speichern (nur API Token und Platzhalter Inhaber-Daten)
        config_data_final = {
            "api_url": DEFAULT_API_URL,
            "token": entry_token.get()
        }
        config_data_final.update(inhaber_data)

        try:
            with open("config.json", "w") as f:
                json.dump(config_data_final, f, indent=4)
            print("✅ config.json erfolgreich gespeichert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern von config.json fehlgeschlagen: {e}")
            return

        final_configs["db_config"] = db_config_final
        review_window.destroy()


    review_window = tk.Toplevel(main_root)
    review_window.title("2/3 Konfigurationsprüfung")
    review_window.geometry("500x480")

    tk.Label(review_window, text="Datenbank-Zugangsdaten", font=("Arial", 10, "bold")).pack(pady=5)

    # --- DB Frame ---
    db_frame = tk.Frame(review_window, padx=10, pady=10, relief=tk.GROOVE, borderwidth=1)
    db_frame.pack(pady=5, padx=20)

    tk.Label(db_frame, text="Host:").grid(row=0, column=0, sticky="w")
    entry_host = tk.Entry(db_frame, width=35)
    entry_host.insert(0, initial_db_config.get("host", ""))
    entry_host.grid(row=0, column=1)

    tk.Label(db_frame, text="User:").grid(row=1, column=0, sticky="w")
    entry_user = tk.Entry(db_frame, width=35)
    entry_user.insert(0, initial_db_config.get("user", ""))
    entry_user.grid(row=1, column=1)

    tk.Label(db_frame, text="Passwort:").grid(row=2, column=0, sticky="w")
    entry_password = tk.Entry(db_frame, width=35, show="*")
    entry_password.insert(0, initial_db_config.get("password", ""))
    entry_password.grid(row=2, column=1)

    tk.Label(db_frame, text="Datenbank:").grid(row=3, column=0, sticky="w")
    entry_database = tk.Entry(db_frame, width=35)
    entry_database.insert(0, initial_db_config.get("database", ""))
    entry_database.grid(row=3, column=1)

    # --- API Frame ---
    tk.Label(review_window, text="API-Daten und Inhaber-Info", font=("Arial", 10, "bold")).pack(pady=10)
    api_frame = tk.Frame(review_window, padx=10, pady=10, relief=tk.GROOVE, borderwidth=1)
    api_frame.pack(pady=5, padx=20)

    tk.Label(api_frame, text="API URL:").grid(row=0, column=0, sticky="w")
    tk.Label(api_frame, text=DEFAULT_API_URL, fg="gray").grid(row=0, column=1, sticky="w")

    tk.Label(api_frame, text="API Token (Schallplatten Suche):", fg="blue").grid(row=1, column=0, sticky="w")
    entry_token = tk.Entry(api_frame, width=35)
    entry_token.insert(0, initial_api_token)
    entry_token.grid(row=1, column=1)

    tk.Label(api_frame, text="InhaberID (Platzhalter):").grid(row=2, column=0, sticky="w")
    tk.Label(api_frame, text=inhaber_data.get("inhaberid", "Wird aus DB gelesen"), fg="gray").grid(row=2, column=1, sticky="w")

    tk.Button(review_window, text="Speichern & Datenbank verbinden (Weiter zu 3/3)", command=save_and_proceed, bg="#90EE90").pack(pady=20)

    review_window.grab_set()
    main_root.wait_window(review_window)

    return final_configs

# -------------------- Hilfsfunktionen für DB und JSON --------------------

def load_db_config():
    """Lädt die Datenbankkonfiguration aus db_config.json, falls vorhanden."""
    try:
        with open("db_config.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def fetch_users_from_db(db_config):
    """Holt Benutzername, Passwort-Hash und Inhaber-Daten aus der 'user'-Tabelle."""
    users_data = {}
    inhaber_data = {}
    try:
        conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT username, password, inhaberID, Name FROM user"
        cursor.execute(sql)
        results = cursor.fetchall()

        for i, row in enumerate(results):
            users_data[row["username"]] = row["password"]

            if i == 0 and not inhaber_data:
                inhaber_data["inhaberid"] = row["inhaberID"]
                inhaber_data["inhaber"] = row["Name"]

        cursor.close()
        conn.close()

        if not users_data:
             messagebox.showerror("Datenbankfehler", "Keine Benutzer in der Datenbank gefunden.")
             return {}, {}

        return users_data, inhaber_data

    except mysql.connector.Error as err:
        messagebox.showerror("Datenbankfehler", f"Verbindungsfehler: {err}")
        return {}, {}
    except Exception as e:
        messagebox.showerror("Allgemeiner Fehler", f"Ein Fehler ist aufgetreten: {e}")
        return {}, {}

def save_users_json(users_data):
    """Speichert die Benutzerdaten in users.json."""
    if users_data:
        try:
            with open("users.json", "w") as file:
                json.dump(users_data, file, indent=4)
            print("✅ users.json erfolgreich erstellt.")
            return True
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"users.json konnte nicht erstellt werden: {e}")
            return False
    return False

# -------------------- Hauptfunktion --------------------

def run_setup(root_to_destroy):
    """Führt den gesamten Setup-Prozess aus."""
    root_to_destroy.withdraw()

    db_config_initial = load_db_config()
    db_config_from_source = {}

    # --- 1. DB-Konfiguration laden oder erstellen (von JSON-URL oder manuell) ---
    if not db_config_initial:
        servers = load_servers_from_json(SERVER_LIST_URL)

        if servers:
            db_config_from_source = server_selection_gui(servers, root_to_destroy)
        else:
            db_config_from_source = manual_config_gui(root_to_destroy)

        if not db_config_from_source:
             root_to_destroy.destroy()
             return
    else:
        db_config_from_source = db_config_initial

    # --- 2. Konfigurationsprüfung und Speicherung von db_config.json / config.json (initial) ---
    final_configs = config_review_gui(
        db_config_from_source,
        DEFAULT_API_TOKEN,
        root_to_destroy,
        {"inhaberid": "Wird aus DB geladen", "inhaber": "Wird aus DB geladen"}
    )

    if not final_configs:
         root_to_destroy.destroy()
         return

    # --- 3. Datenbankabfrage (users.json erstellen) und Finalisierung von config.json ---

    db_config_final = load_db_config()

    users_data, inhaber_data = fetch_users_from_db(db_config_final)

    if not users_data or not inhaber_data:
        messagebox.showerror("Setup", "Fehler: Benutzerdaten konnten nicht aus der DB geladen werden. Prüfen Sie die Zugangsdaten!")
        root_to_destroy.destroy()
        return

    users_success = save_users_json(users_data)

    try:
        with open("config.json", "r") as f:
            config_data_api = json.load(f)
    except Exception:
        config_data_api = {"api_url": DEFAULT_API_URL, "token": DEFAULT_API_TOKEN}

    config_data_api.update(inhaber_data)

    try:
        with open("config.json", "w") as file:
            json.dump(config_data_api, file, indent=4)
        config_success = True
        print("✅ config.json (Final) erfolgreich mit Inhaber-Daten aktualisiert.")
    except Exception as e:
        messagebox.showerror("Fehler beim Speichern", f"Finalisierung config.json fehlgeschlagen: {e}")
        config_success = False


    if users_success and config_success:
        messagebox.showinfo("Setup", "Setup erfolgreich abgeschlossen! (3/3)")
    else:
        messagebox.showerror("Setup", "Setup teilweise oder vollständig fehlgeschlagen.")

    root_to_destroy.destroy()

# -------------------- GUI für Setup Start --------------------

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Setup")
    root.geometry("300x150")

    tk.Label(root, text="Klicken Sie, um die Konfigurationsdateien").pack(pady=10)
    tk.Label(root, text="aus der Datenbank zu erstellen.").pack()

    tk.Button(root, text="Start Setup", command=lambda: run_setup(root)).pack(pady=10)

    root.mainloop()
