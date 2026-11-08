#!/bin/bash
# ==============================================================================
# Start-Skript für Bücherei 2.0 Online (API-Edition)
# Prüft Abhängigkeiten, Konfiguration und Netzwerkverbindung.
# ==============================================================================

PYTHON_CMD="python3"

# Parallele Arrays: MODULE_NAMES (Import-Name) zu PACKAGE_NAMES (pip Install-Name)
MODULE_NAMES=("requests" "PIL")
PACKAGE_NAMES=("requests" "Pillow")

# --- 1. Kritische Python-Abhängigkeiten prüfen und installieren ---
echo "🐍 Prüfe und installiere kritische Python-Abhängigkeiten..."

MISSING_DEPS=0
NUM_DEPS=${#MODULE_NAMES[@]}

for ((i=0; i<NUM_DEPS; i++)); do
    MODULE=${MODULE_NAMES[i]}
    PACKAGE=${PACKAGE_NAMES[i]}

    # Versucht, das Modul zu importieren, um die Existenz zu prüfen
    $PYTHON_CMD -c "import $MODULE" > /dev/null 2>&1

    if [ $? -ne 0 ]; then
        echo "⚠️ Kritische Abhängigkeit '$MODULE' (Paket: $PACKAGE) fehlt. Versuche Installation..."
        pip install "$PACKAGE" > /dev/null 2>&1 || pip3 install "$PACKAGE" > /dev/null 2>&1

        # Erneute Prüfung nach Installation
        $PYTHON_CMD -c "import $MODULE" > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "❌ Fehler: '$MODULE' konnte NICHT installiert oder gefunden werden."
            MISSING_DEPS=1
        fi
    fi
done

if [ $MISSING_DEPS -ne 0 ]; then
    echo "❌ Das Programm kann aufgrund fehlender kritischer Abhängigkeiten NICHT gestartet werden."
    echo "Bitte beheben Sie die pip-Fehler."
    exit 1
fi

echo "✅ Alle kritischen Python-Abhängigkeiten sind vorhanden."

# --- 2. Konfigurationsdateien prüfen und ggf. Setup starten ---
echo "⚙️ Prüfe auf notwendige Konfigurationsdateien..."

CONFIG_FILES=("config.json" "users.json" "progPen.json")
MISSING_FILE=0

for file in "${CONFIG_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Fehler: Konfigurationsdatei '$file' fehlt."
        MISSING_FILE=1
    fi
done

if [ $MISSING_FILE -eq 1 ]; then
    echo "⚠️ Starte Setup-Routine (setup.py)..."
    $PYTHON_CMD setup.py

    # Prüfung nach Setup
    for file in "${CONFIG_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            echo "❌ Setup abgeschlossen, aber '$file' fehlt weiterhin. Breche ab."
            exit 1
        fi
    done

    echo "✅ Setup erfolgreich abgeschlossen. Konfiguration ist vorhanden."
fi

# --- 3. Internetverbindung prüfen ---
echo "🌐 Prüfe Internetverbindung..."

# Versucht, Google DNS (8.8.8.8) zu pingen. Timeout 5 Sekunden.
ping -c 1 -W 5 8.8.8.8 > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Fehler: Keine aktive Internetverbindung gefunden."
    echo "Das Online-Programm kann ohne Netzwerkverbindung NICHT gestartet werden. Breche ab."
    exit 1
fi

echo "✅ Internetverbindung ist stabil."

# --- 4. Hauptprogramm starten ---
echo "🚀 Starte Hauptprogramm all.py..."
$PYTHON_CMD all.py

if [ $? -ne 0 ]; then
    echo "❌ all.py wurde mit einem Fehler beendet."
    exit 1
fi

echo "Programm erfolgreich beendet."
exit 0
