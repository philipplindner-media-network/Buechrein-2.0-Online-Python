# Changelog - Bücherei 2.0 Online
Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei festgehalten.

## [2.1.0] - Aktuelle Version (all.py)
### Hinzugefügt
- **Film- & Serien-Unterstützung**: Neue Konstanten für Film-Typen (Film, Serie) und Formate (DVD, Blu-ray, 4K UHD, etc.) hinzugefügt.
- **Online-Kontoverwaltung**: Ein direkter Button im Profil-Tab ermöglicht nun die Verwaltung des Passworts über das externe Web-Dashboard.
- **Robuster Versionsvergleich**: Die Update-Logik wurde verbessert und vergleicht nun Major-, Minor- und Patch-Versionen (z.B. 1.0.1) präzise.
- **Erweitertes Fehler-Handling**: Verbesserte Fehlermeldungen bei fehlgeschlagenen API-Anfragen oder ungültigen Server-Antworten (JSON).

## [1.1.0] - Modularisierung & Statistik (all.py)
### Hinzugefügt
- **Modulare Struktur**: Der Code wurde in Klassen wie ArtikelModul, UserInfoModul und PlayerModul unterteilt, um die Wartbarkeit zu erhöhen.
- **Statistik-System**: Integration einer Statistik-Funktion, die Systemdaten (OS, IP-Adresse, anonymisierter Nutzername) an einen Server sendet.
- **VLC-Integration**: Unterstützung für die lokale Medienwiedergabe via python-vlc hinzugefügt.
- **Profil-Tab**: Ein neuer Reiter „Mein Profil & System“ zeigt nun Benutzerdetails aus der Datenbank und Systeminformationen an.
- **Zentrale Konfiguration**: Einführung der progPen.json zur Verwaltung von URLs, Links und Update-Einstellungen.

## [1.0.1] - Grundversion (main.py)
### Hinzugefügt
- **Basis-Funktionen**: Erste Implementierung der Medienverwaltung mit GUI (Tkinter).
- **ISBN-Suche**: Integration der Google Books API zum automatischen Abruf von Metadaten (Titel, Verlag, Cover-URL) via ISBN.
- **Datenbank-Anbindung**: Grundlegende MySQL-Anbindung zum Speichern und Laden von Medieneinträgen.
- **Update-Prüfung**: Einfache Funktion zum Abgleich der lokalen Version mit einer Online-Textdatei.
- **Login-System**: Einfaches Login-Fenster mit MD5-Passworthashing und users.json.
