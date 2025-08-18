#!/bin/bash

# Wechsle in das Verzeichnis, in dem das Skript liegt, um relative Pfade zu ermöglichen
cd "$(dirname "$0")"

echo "Virtuelle Umgebung wird überprüft/erstellt..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "Abhängigkeiten werden installiert..."
. venv/bin/activate
pip install -r requirements.txt

echo "Skript wird gestartet..."
python3 main.py

# Die virtuelle Umgebung wird am Ende des Skripts automatisch deaktiviert.
