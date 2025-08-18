# Buechrein-2.0-Online-Python

## Projektbeschreibung

Dieses Projekt ist eine Online-Version von "Buechrein 2.0", umgesetzt in Python. Ziel ist es, Bücher und Medien zu verwalten und verschiedene Funktionen online zur Verfügung zu stellen.  
**Es handelt sich um ein digitales Archiv für alle Medien**, das die zentrale Verwaltung, Suche und Organisation von Büchern, Zeitschriften, Filmen, Musik und weiteren Medientypen ermöglicht.

Weitere Informationen und eine Übersicht gibt es auf der offiziellen Webseite:  
👉 [https://buch-archiv20-software.de/](https://buch-archiv20-software.de/)

## Abhängigkeiten

Um das Projekt auszuführen, müssen folgende Python-Bibliotheken installiert sein:

- `flask` (Web-Framework)
- `requests` (HTTP-Anfragen)
- `sqlalchemy` (Datenbank-ORM)
- `jinja2` (Template-Engine)
- `werkzeug` (WSGI-Toolkit)
- Weitere Abhängigkeiten können im Quellcode oder in einer requirements.txt-Datei aufgeführt sein.

Installiere die Abhängigkeiten am besten über pip:

```bash
pip install flask requests sqlalchemy jinja2 werkzeug
```

## Starten der Anwendung

### Unter Linux

Unter Linux kann das Projekt problemlos über das Skript `start.sh` gestartet werden:

```bash
./start.sh
```

### Unter Windows

Aktuell gibt es Probleme mit dem Startskript `start.bat` unter Windows. Die Anwendung lässt sich derzeit nicht zuverlässig starten. Es wird empfohlen, stattdessen ein Linux-System zu verwenden oder das Projekt manuell über die Kommandozeile zu starten.

Manueller Start unter Windows (als Beispiel):

```cmd
python main.py
```

## Hinweise

- Stelle sicher, dass alle Abhängigkeiten installiert sind.
- Für die aktuellsten Informationen zu Fehlern und Problemen siehe die Issues im GitHub-Repository.
- Beiträge und Fehlerberichte sind willkommen!

---

**Status:** Startskript funktioniert unter Linux, unter Windows gibt es derzeit Probleme mit `start.bat`.
