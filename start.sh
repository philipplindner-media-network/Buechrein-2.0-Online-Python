#!/bin/bash

echo "Virtuelle Umgebung erstellen..."
python3 -m venv venv

echo "Abhängigkeiten installieren..."
source venv/bin/activate
pip install -r requirements.txt

echo "Skript starten..."
python main.py

deactivate
