"""
Datenbank-Migrationsskript
Fügt die neuen Spalten 'source' und 'source_url' zur recipes-Tabelle hinzu
"""

import sqlite3
import os

# Pfad zur Datenbank
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def migrate_database():
    """Führt die Migration durch"""

    if not os.path.exists(DB_PATH):
        print(f"Datenbank nicht gefunden: {DB_PATH}")
        print("Die Datenbank wird beim ersten Start der App automatisch erstellt.")
        return

    print(f"Verbinde mit Datenbank: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Prüfen, ob die Spalte 'source' bereits existiert
        cursor.execute("PRAGMA table_info(recipes)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'source' not in columns:
            print("Füge Spalte 'source' hinzu...")
            cursor.execute("ALTER TABLE recipes ADD COLUMN source VARCHAR(100)")
            print("✅ Spalte 'source' hinzugefügt")
        else:
            print("ℹ️  Spalte 'source' existiert bereits")

        if 'source_url' not in columns:
            print("Füge Spalte 'source_url' hinzu...")
            cursor.execute("ALTER TABLE recipes ADD COLUMN source_url VARCHAR(500)")
            print("✅ Spalte 'source_url' hinzugefügt")
        else:
            print("ℹ️  Spalte 'source_url' existiert bereits")

        conn.commit()
        print("\n✅ Migration erfolgreich abgeschlossen!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Fehler bei der Migration: {str(e)}")
        raise

    finally:
        conn.close()

if __name__ == '__main__':
    print("=== Datenbank-Migration ===\n")
    migrate_database()
