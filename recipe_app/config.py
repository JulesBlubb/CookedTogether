"""
Konfigurationsdatei für die Rezepte-Anwendung
Definiert Datenbankpfad, Upload-Ordner und Secret Key
"""

import os
from dotenv import load_dotenv

# Basis-Verzeichnis der Anwendung
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Lade Umgebungsvariablen aus .env Datei
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    """Hauptkonfiguration für die Flask-Anwendung"""

    # Secret Key für Session-Management und CSRF-Schutz
    # In Produktion sollte dies aus einer Umgebungsvariable gelesen werden
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # SQLite Datenbank-Konfiguration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload-Ordner für Rezeptbilder
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max 16MB Upload-Größe

    # Erlaubte Bildformate
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    # OCR-Konfiguration (Tesseract)
    OCR_LANGUAGE = 'deu'  # Deutsche Sprache für Tesseract OCR

    # Authentifizierungs-Token für Rezept-Erstellung
    # WICHTIG: Dieses Token sollte geheim gehalten werden!
    # In Produktion aus Umgebungsvariable laden
    RECIPE_AUTH_TOKEN = os.environ.get('RECIPE_AUTH_TOKEN')