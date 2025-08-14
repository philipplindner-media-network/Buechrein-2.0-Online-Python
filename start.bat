@echo off

echo rem In das Verzeichnis der Batch-Datei wechseln
cd /d "%~dp0"

echo Virtuelle Umgebung erstellen...
python -m venv venv

echo Abhängigkeiten installieren...
venv\Scripts\pip install -r requirements.txt

echo Skript starten...
venv\Scripts\python main.py

pause
