# 🍳 Cooked Together - Recipes proofed by Weilbäche

Eine mobile-optimierte Rezeptverwaltungs-Webanwendung mit OCR-Unterstützung, entwickelt für Familie Weilbäche.

## 📋 Features

- ✅ **Mobile-First Design** - Optimiert für Smartphone, Tablet und Desktop
- 📸 **OCR Integration** - Automatisches Auslesen von Rezepten aus Fotos
- 🔢 **Dynamische Portionsskalierung** - Zutatenmengen automatisch umrechnen
- 🏷️ **Tags & Kategorien** - Rezepte organisieren und filtern
- 💬 **Kommentarfunktion** - Feedback und Tipps zu Rezepten teilen
- 📱 **Kochmodus** - Großer Text und hoher Kontrast beim Kochen
- 🔍 **Suchfunktion** - Rezepte nach Titel, Beschreibung und Zutaten durchsuchen
- 🖼️ **Bilderverwaltung** - Rezeptfotos hochladen und anzeigen

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask, SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **OCR**: Tesseract OCR (mit deutscher Sprache), OpenCV
- **Bildverarbeitung**: Pillow, pytesseract

## 📦 Installation

**Detaillierte Anleitung:** Siehe [INSTALL.md](INSTALL.md) für vollständige Installationsschritte und Troubleshooting.

### Schnellstart (Ubuntu/Debian/Raspberry Pi):

#### Schritt 1: Tesseract OCR installieren (System-Paket)

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-deu
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0  # Für OpenCV
```

**Wichtig:** Tesseract muss zuerst als System-Paket installiert werden!

#### Schritt 2: Installation überprüfen

```bash
tesseract --version  # Sollte 4.x.x oder höher zeigen
tesseract --list-langs | grep deu  # Sollte 'deu' ausgeben
```

#### Schritt 3: Virtual Environment erstellen

```bash
cd /home/juliane/src/CookedTogether/recipe_app
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

#### Schritt 4: Python-Abhängigkeiten installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Schritt 4: Datenbank initialisieren

Die Datenbank wird automatisch beim ersten Start erstellt. Alternativ:

```bash
python3 app.py
```

Die App läuft nun unter: `http://localhost:5000`

## 🚀 Verwendung

### Server starten

```bash
cd /home/juliane/src/CookedTogether/recipe_app
source venv/bin/activate
python3 app.py
```

Die Anwendung ist dann unter `http://localhost:5000` erreichbar.

### Raspberry Pi Deployment

1. **Projekt auf Raspberry Pi kopieren**:
   ```bash
   scp -r recipe_app/ pi@raspberrypi.local:/home/pi/
   ```

2. **Auf dem Raspberry Pi**:
   ```bash
   cd /home/pi/recipe_app
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python3 app.py
   ```

3. **Autostart einrichten** (optional):

   Erstelle eine Systemd-Service-Datei:
   ```bash
   sudo nano /etc/systemd/system/recipe-app.service
   ```

   Inhalt:
   ```ini
   [Unit]
   Description=Cooked Together Recipe App
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/recipe_app
   ExecStart=/home/pi/recipe_app/venv/bin/python3 /home/pi/recipe_app/app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Service aktivieren:
   ```bash
   sudo systemctl enable recipe-app
   sudo systemctl start recipe-app
   ```

## 📁 Projektstruktur

```
recipe_app/
├── app.py                  # Haupt-Flask-Anwendung
├── config.py               # Konfiguration (DB, Upload-Ordner)
├── models.py               # Datenbankmodelle (SQLAlchemy)
├── ocr.py                  # OCR-Logik für Rezepterkennung
├── requirements.txt        # Python-Abhängigkeiten
├── database.db             # SQLite-Datenbank (wird automatisch erstellt)
├── README.md               # Diese Datei
│
├── uploads/                # Hochgeladene Rezeptbilder
│
├── templates/              # HTML-Templates (Jinja2)
│   ├── base.html          # Basis-Template
│   ├── index.html         # Rezeptliste
│   ├── recipe.html        # Rezept-Detailansicht
│   └── add_recipe.html    # Rezept hinzufügen
│
└── static/                 # Statische Dateien
    ├── css/
    │   └── style.css      # CSS mit Mobile-First Design
    └── js/
        └── portions.js    # JavaScript für Portionsskalierung
```

## 🗃️ Datenbank-Schema

### Recipe (Rezepte)
- `id` - Primary Key
- `title` - Titel des Rezepts
- `description` - Zubereitungsanleitung
- `image_path` - Pfad zum Rezeptbild
- `base_portions` - Basis-Portionen
- `prep_time_minutes` - Vorbereitungszeit
- `cook_time_minutes` - Kochzeit
- `created_at` - Erstellungsdatum

### Ingredient (Zutaten)
- `id` - Primary Key
- `recipe_id` - Foreign Key zu Recipe
- `name` - Name der Zutat
- `amount` - Menge
- `unit` - Einheit (g, ml, EL, etc.)

### Comment (Kommentare)
- `id` - Primary Key
- `recipe_id` - Foreign Key zu Recipe
- `author_name` - Name des Autors (optional)
- `content` - Kommentartext
- `created_at` - Zeitstempel

### Tag (Tags/Kategorien)
- `id` - Primary Key
- `name` - Tag-Name (case-insensitive)

### RecipeTag (Many-to-Many)
- `recipe_id` - Foreign Key zu Recipe
- `tag_id` - Foreign Key zu Tag

## 🔍 OCR-Funktionalität

Die OCR-Funktion verwendet **Tesseract OCR** mit intelligenten Optimierungen:

1. **Bild hochladen** im "Neues Rezept"-Formular
2. **"Text erkennen"** klicken
3. **Automatische Verarbeitung:**
   - ✅ **Automatische Bildrotation** (erkennt richtige Orientierung)
   - ✅ **Preprocessing** (Gaussian Blur + Adaptive Thresholding)
   - ✅ **OCR mit deutscher Sprache** (PSM 4 für Text-Blöcke)
   - ✅ **Intelligentes Parsing** mit Heuristiken
4. **Formular wird automatisch ausgefüllt:**
   - Titel (erste sinnvolle Zeile)
   - Zutaten (Zeilen mit Zahlen + Einheiten wie g, ml, EL, TL, etc.)
   - Beschreibung (verbleibender Text)
   - Zeiten (falls erkennbar)
   - Portionen (falls erkennbar)

**OCR-Optimierungen:**
- 🔹 Automatische Drehung korrigiert falsch orientierte Fotos
- 🔹 Adaptive Thresholding entfernt Papierstruktur
- 🔹 Verbesserte Einheiten-Erkennung (20+ deutsche Einheiten)
- 🔹 Zwei Pattern-Matcher für Zutaten (mit/ohne Einheit)

**Beste Ergebnisse:**
- Gut beleuchtetes Foto
- Hohe Auflösung (mind. 1200x900 px)
- Klarer Fokus, kein Verwackeln
- Gedruckter Text (keine Handschrift)

**Hinweis**: OCR-Ergebnisse sollten immer überprüft werden!

## 📱 Kochmodus

Der Kochmodus bietet:
- ✅ Vollbild-Layout
- ✅ Große Schrift
- ✅ Hoher Kontrast (dunkler Hintergrund)
- ✅ Zutaten bleiben sichtbar
- ✅ Keine Ablenkungen (Kommentare ausgeblendet)

**Aktivierung**: Button "Kochmodus aktivieren" auf der Rezeptseite

## 🎨 Mobile-First Design

Die App ist optimiert für:
- 📱 **Smartphones** (320px - 767px)
- 📱 **Tablets** (768px - 1023px)
- 💻 **Desktop** (1024px+)

Design-Prinzipien:
- Buttons mindestens 44px hoch (Touch-friendly)
- Vertikales Layout auf Mobilgeräten
- Keine Hover-Interaktionen (mobile-kompatibel)
- Einhändige Bedienung möglich

## 🔧 Konfiguration

Konfiguration in `config.py`:

```python
# Secret Key (in Produktion ändern!)
SECRET_KEY = 'your-secret-key-here'

# Datenbank
SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'

# Upload-Ordner
UPLOAD_FOLDER = 'uploads/'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max 16MB

# OCR
OCR_LANGUAGES = ['de']  # Deutsch
OCR_GPU = False  # CPU-only für Raspberry Pi
```

## 🧪 Testing-Checkliste

- [ ] Rezept mit Bild, Zutaten und Tags hinzufügen
- [ ] OCR-Funktion mit Rezeptfoto testen
- [ ] Portionsskalierung (+ / - Buttons)
- [ ] Kommentar hinzufügen
- [ ] Suche nach Rezeptnamen
- [ ] Tag-Filter verwenden
- [ ] Kochmodus aktivieren
- [ ] Mobile-Ansicht testen (responsive)

## 🐛 Troubleshooting

**Siehe [INSTALL.md](INSTALL.md) für vollständige Troubleshooting-Anleitung!**

### Tesseract nicht gefunden

```bash
# Tesseract OCR installieren
sudo apt-get install tesseract-ocr tesseract-ocr-deu

# Prüfen ob installiert
tesseract --version
tesseract --list-langs
```

### OCR erkennt keinen Text

```bash
# Debug-Modus: Konsolen-Output beobachten
# Die App zeigt:
# ✅ Bild um X° gedreht
# 📄 Erkannter Text (XXX Zeichen)
# ✅ Geparst: X Zutaten gefunden

# Wenn keine/falsche Rotation:
sudo apt-get install tesseract-ocr-osd
```

### OpenCV Fehler auf Raspberry Pi

```bash
# Zusätzliche Systemabhängigkeiten installieren
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
```

### Datenbank-Fehler

```bash
# Datenbank zurücksetzen
rm database.db
python3 app.py  # Erstellt neue Datenbank
```

## 📄 Lizenz

Dieses Projekt ist für den privaten Gebrauch der Familie Weilbäche erstellt.

## 👨‍💻 Autor

Erstellt mit ❤️ für Familie Weilbäche

---

## 🚀 Nächste Schritte

1. Virtual Environment aktivieren: `source venv/bin/activate`
2. Dependencies installieren: `pip install -r requirements.txt`
3. App starten: `python3 app.py`
4. Browser öffnen: `http://localhost:5000`
5. Erstes Rezept hinzufügen! 🍳

**Viel Spaß beim Kochen!** 🎉
