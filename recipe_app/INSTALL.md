# 🚀 Installation Guide - Cooked Together

## Schnellstart für Ubuntu/Debian/Raspberry Pi OS

### ✅ Schritt 1: System-Pakete installieren

```bash
# System-Pakete aktualisieren
sudo apt-get update

# Tesseract OCR mit deutscher Sprache installieren
sudo apt-get install -y tesseract-ocr tesseract-ocr-deu

# Optional: Weitere Sprachen installieren
# sudo apt-get install tesseract-ocr-eng  # Englisch

# OpenCV System-Abhängigkeiten (für Raspberry Pi wichtig)
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0

# Python 3 und pip (falls nicht vorhanden)
sudo apt-get install -y python3 python3-pip python3-venv
```

**Wichtig:** Tesseract muss als System-Paket installiert werden, da pytesseract nur ein Python-Wrapper ist!

### ✅ Schritt 2: Tesseract-Installation überprüfen

```bash
# Tesseract-Version prüfen
tesseract --version

# Sollte ausgeben:
# tesseract 4.x.x oder höher

# Verfügbare Sprachen prüfen
tesseract --list-langs

# Sollte 'deu' (Deutsch) enthalten
```

### ✅ Schritt 3: Virtual Environment erstellen

```bash
cd /home/juliane/src/CookedTogether/recipe_app

# Virtual Environment erstellen
python3 -m venv venv

# Virtual Environment aktivieren
source venv/bin/activate

# Prompt sollte jetzt (venv) anzeigen
```

### ✅ Schritt 4: Python-Pakete installieren

```bash
# Pip upgraden
pip install --upgrade pip

# Alle Dependencies installieren
pip install -r requirements.txt

# Das kann 2-5 Minuten dauern
```

### ✅ Schritt 5: App starten

```bash
# Noch im aktivierten venv
python3 app.py

# Output sollte sein:
# * Running on http://0.0.0.0:5000
```

### ✅ Schritt 6: Testen

Browser öffnen: `http://localhost:5000`

---

## 🔍 OCR-Pipeline testen

### Test 1: Tesseract direkt testen

```bash
# Tesseract direkt auf einem Bild testen
tesseract testbild.jpg output -l deu --psm 4

# Ergebnis in output.txt prüfen
cat output.txt
```

### Test 2: Python OCR-Modul testen

```python
from ocr import RecipeOCR

ocr = RecipeOCR(language='deu')
result = ocr.process_image('pfad/zum/rezeptbild.jpg')

print("Titel:", result['title'])
print("Zutaten:", len(result['ingredients']))
print("Beschreibung:", result['description'][:100])
```

---

## 🔧 Troubleshooting

### Problem: "pytesseract.TesseractNotFoundError"

**Lösung:** Tesseract ist nicht als System-Paket installiert

```bash
# Tesseract installieren
sudo apt-get install tesseract-ocr tesseract-ocr-deu

# Installation prüfen
which tesseract
# Sollte: /usr/bin/tesseract ausgeben
```

### Problem: "Sprache 'deu' nicht gefunden"

**Lösung:** Deutsches Sprachpaket fehlt

```bash
# Deutsche Sprache installieren
sudo apt-get install tesseract-ocr-deu

# Verfügbare Sprachen prüfen
tesseract --list-langs
```

### Problem: OpenCV-Fehler auf Raspberry Pi

**Lösung:** System-Abhängigkeiten fehlen

```bash
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev
```

### Problem: "Auto-Rotation fehlgeschlagen"

**Ursache:** Tesseract OSD (Orientation and Script Detection) benötigt zusätzliche Trainingsdaten

**Lösung:**

```bash
# OSD Trainingsdaten installieren
sudo apt-get install tesseract-ocr-osd

# Oder Alternative: OSD im Code deaktivieren (ocr.py)
# Fallback ist bereits implementiert
```

### Problem: OCR erkennt keinen Text

**Mögliche Ursachen:**
1. Bild zu dunkel/zu hell → Preprocessing sollte das korrigieren
2. Bild zu klein → Mindestens 300 DPI empfohlen
3. Handschrift → Tesseract funktioniert nur mit gedrucktem Text
4. Falsche Sprache → Sicherstellen dass `deu` installiert ist

**Debug-Modus aktivieren:**

Die OCR gibt bereits Debug-Ausgaben in der Konsole aus:
```
✅ Bild um 90° gedreht
📄 Erkannter Text (XXX Zeichen):
--------------------------------------------------
[erkannter Text]
--------------------------------------------------
✅ Geparst: X Zutaten gefunden
```

---

## 📊 OCR-Optimierungen

### Bessere Ergebnisse durch gute Fotos

**✅ Gute Fotos:**
- Gut beleuchtet (natürliches Licht)
- Text gerade (parallele Kamera)
- Hohe Auflösung (mindestens 1200x900 px)
- Klarer Fokus
- Hoher Kontrast (schwarzer Text auf weißem Papier)

**❌ Problematische Fotos:**
- Schatten über Text
- Verwackelt/unscharf
- Schräge Perspektive
- Zu kleine Auflösung
- Handgeschriebener Text

### PSM-Modi (Page Segmentation Mode)

Standard ist PSM 4 (single column of text). Bei Problemen kann man in `ocr.py` experimentieren:

```python
# In ocr.py, Zeile 29:
self.psm = 4  # Ändern zu:

# PSM 3 = Automatic page segmentation
# PSM 4 = Single column of text (DEFAULT - gut für Rezepte)
# PSM 6 = Uniform block of text
```

---

## 🎯 Erwartete OCR-Genauigkeit

Bei **guten Fotos** (siehe oben):
- ✅ **Titel-Erkennung:** ~95%
- ✅ **Zutaten mit Einheiten:** ~85-90%
- ✅ **Zeitangaben:** ~90%
- ✅ **Beschreibung:** ~80-85%

Bei **problematischen Fotos:**
- ⚠️ Genauigkeit kann unter 50% fallen

**Wichtig:** Nutzer sollten OCR-Ergebnisse immer überprüfen!

---

## 🔄 Vergleich: EasyOCR vs. Tesseract

| Feature | EasyOCR (alt) | Tesseract (neu) |
|---------|---------------|-----------------|
| Installation | Sehr groß (~2GB) | Klein (~50MB) |
| Raspberry Pi | Sehr langsam | Schnell |
| Deutsch | Gut | Ausgezeichnet |
| Auto-Rotation | ❌ Keine | ✅ Ja (OSD) |
| Offline | ✅ Ja | ✅ Ja |
| CPU-Performance | Schlecht | Gut |

**➡️ Tesseract ist für dieses Projekt die bessere Wahl!**

---

## 📱 Raspberry Pi Spezifika

### Empfohlene Raspberry Pi Modelle

- ✅ **Raspberry Pi 4** (4GB+) - Optimal
- ✅ **Raspberry Pi 3B+** - Funktioniert, langsamer OCR
- ⚠️ **Raspberry Pi Zero** - Sehr langsam, nicht empfohlen

### Performance-Erwartungen

| Modell | OCR-Zeit pro Bild |
|--------|-------------------|
| RPi 4 (4GB) | ~2-4 Sekunden |
| RPi 3B+ | ~5-8 Sekunden |
| Desktop PC | ~1-2 Sekunden |

### Raspberry Pi Autostart (Optional)

Siehe [README.md](README.md) für Systemd-Service-Konfiguration.

---

## ✅ Erfolgreiche Installation prüfen

```bash
# 1. Virtual Environment aktiviert?
echo $VIRTUAL_ENV
# Sollte: /home/juliane/src/CookedTogether/recipe_app/venv ausgeben

# 2. Tesseract installiert?
tesseract --version
# Sollte: tesseract 4.x.x oder höher

# 3. Deutsche Sprache verfügbar?
tesseract --list-langs | grep deu
# Sollte: deu ausgeben

# 4. Python-Pakete installiert?
pip list | grep -E "Flask|pytesseract|opencv"
# Sollte alle drei Pakete zeigen

# 5. App läuft?
curl http://localhost:5000
# Sollte HTML zurückgeben
```

---

## 🆘 Support

Bei Problemen:
1. Konsolen-Output prüfen (DEBUG-Ausgaben)
2. `tesseract --version` und `tesseract --list-langs` prüfen
3. Logs in der Terminal-Ausgabe ansehen
4. Bild-Qualität überprüfen

**Viel Erfolg!** 🎉
