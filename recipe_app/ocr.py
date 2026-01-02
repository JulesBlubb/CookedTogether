"""
Pragmatische OCR-Pipeline für Rezepterkennung
Multi-Strategie-Ansatz: Testet verschiedene Preprocessing-Methoden und wählt die beste
"""

import re
import cv2
import numpy as np
from PIL import Image
import pytesseract
from typing import Dict, List, Tuple


class RecipeOCR:
    """
    Multi-Strategie OCR mit automatischer Best-Match-Auswahl
    """

    def __init__(self, language='deu'):
        """
        Initialisiert den OCR-Handler

        Args:
            language: Tesseract-Sprache (default: 'deu' für Deutsch)
        """
        self.language = language

    # ========================================================================
    # PREPROCESSING-STRATEGIEN
    # ========================================================================

    def preprocess_none(self, img_np: np.ndarray) -> np.ndarray:
        """Keine Preprocessing - nur Graustufen"""
        return cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

    def preprocess_otsu(self, img_np: np.ndarray) -> np.ndarray:
        """Otsu Thresholding"""
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def preprocess_clahe_otsu(self, img_np: np.ndarray) -> np.ndarray:
        """CLAHE + Otsu (gut für kontrastarme Bilder)"""
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def preprocess_sharpen_otsu(self, img_np: np.ndarray) -> np.ndarray:
        """Schärfen + Otsu (gut für leicht unscharfe Bilder)"""
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        _, thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def preprocess_bilateral_otsu(self, img_np: np.ndarray) -> np.ndarray:
        """Bilateral Filter + Otsu (Edge-preserving)"""
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    # ========================================================================
    # MULTI-STRATEGIE OCR
    # ========================================================================

    def extract_text_multi_strategy(self, image_path: str) -> Tuple[str, str, int]:
        """
        Testet mehrere Strategien und wählt die beste

        Args:
            image_path: Pfad zum Bild

        Returns:
            (best_text, best_strategy, confidence_score)
        """
        try:
            # Bild laden
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Auto-Rotation
            try:
                osd = pytesseract.image_to_osd(img)
                rotate_match = re.search(r'Rotate: (\d+)', osd)
                if rotate_match:
                    rotate = int(rotate_match.group(1))
                    if rotate != 0:
                        img = img.rotate(rotate, expand=True)
                        print(f"✅ Bild um {rotate}° gedreht")
            except Exception as e:
                print(f"⚠️  Auto-Rotation übersprungen: {e}")

            # NumPy konvertieren
            img_np = np.array(img)
            img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

            # Strategien definieren
            strategies = [
                ("Graustufen", self.preprocess_none, [4, 6]),
                ("Otsu", self.preprocess_otsu, [4, 6]),
                ("CLAHE+Otsu", self.preprocess_clahe_otsu, [3, 4]),
                ("Schärfen+Otsu", self.preprocess_sharpen_otsu, [3, 4]),
                ("Bilateral+Otsu", self.preprocess_bilateral_otsu, [4, 6]),
            ]

            results = []

            # Alle Strategien testen
            for strategy_name, preprocess_func, psm_modes in strategies:
                processed = preprocess_func(img_np)

                for psm in psm_modes:
                    config = f'--psm {psm} --oem 3'
                    text = pytesseract.image_to_string(processed, lang=self.language, config=config)

                    # Qualität bewerten
                    score = self._evaluate_text_quality(text)

                    results.append({
                        'text': text,
                        'strategy': f"{strategy_name} + PSM {psm}",
                        'score': score
                    })

                    print(f"   {strategy_name:20} PSM {psm}: {score} Punkte ({len(text)} Zeichen)")

            # Beste Strategie wählen
            best = max(results, key=lambda x: x['score'])

            print(f"\n🏆 Beste Strategie: {best['strategy']} ({best['score']} Punkte)")

            return best['text'], best['strategy'], best['score']

        except Exception as e:
            print(f"❌ Fehler bei OCR: {e}")
            import traceback
            traceback.print_exc()
            return "", "Fehler", 0

    def _evaluate_text_quality(self, text: str) -> int:
        """
        Bewertet die Qualität des extrahierten Textes

        Args:
            text: Extrahierter Text

        Returns:
            Score (höher = besser)
        """
        score = 0

        # Basis: Textlänge (aber nicht zu viel Wert)
        score += min(len(text) // 10, 30)

        # Anzahl Wörter
        words = text.split()
        score += min(len(words) * 2, 40)

        # Anzahl Zeilen
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        score += min(len(lines) * 3, 30)

        # Hat deutsche Buchstaben?
        if re.search(r'[a-zA-ZäöüÄÖÜß]{3,}', text):
            score += 20

        # Hat Zahlen? (für Zutaten wichtig)
        if re.search(r'\d+', text):
            score += 10

        # Hat typische Einheiten?
        units = r'(g|kg|ml|l|EL|TL|Stück|Prise)'
        if re.search(units, text, re.IGNORECASE):
            score += 15

        # Hat sehr lange erste Zeile? (wahrscheinlich Titel)
        if lines:
            first_line = lines[0]
            if 5 < len(first_line) < 60:
                score += 20

        # Negativ: Zu viele Sonderzeichen
        special_chars = len(re.findall(r'[£€$@#%&*_+=<>{}\\|~`]', text))
        score -= special_chars * 2

        # Negativ: Zu viele einzelne Zeichen
        single_chars = sum(1 for word in words if len(word) == 1)
        score -= single_chars

        return max(0, score)

    # ========================================================================
    # PARSING
    # ========================================================================

    def parse_recipe(self, text: str) -> Dict:
        """
        Parst Rezeptdaten aus Text

        Args:
            text: Extrahierter Text

        Returns:
            Dictionary mit Rezeptdaten
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        if not lines:
            return self._empty_recipe()

        recipe_data = {
            'title': '',
            'description': '',
            'ingredients': [],
            'prep_time': None,
            'cook_time': None,
            'portions': 4
        }

        # Titel: Erste sinnvolle Zeile
        title_found = False
        first_line_idx = 0

        for i, line in enumerate(lines):
            # Titel sollte 3-60 Zeichen haben und nicht mit Zahl starten
            if 3 <= len(line) <= 60 and not re.match(r'^\s*\d+', line):
                # Keine typische Zutat
                if not self._is_ingredient_line(line):
                    recipe_data['title'] = line
                    first_line_idx = i + 1
                    title_found = True
                    break

        if not title_found and lines:
            recipe_data['title'] = lines[0]
            first_line_idx = 1

        # Rest parsen
        remaining_lines = lines[first_line_idx:]
        ingredients = self._extract_ingredients(remaining_lines)

        # Beschreibung = Nicht-Zutaten
        description_lines = []
        for line in remaining_lines:
            if not self._is_ingredient_line(line):
                # Zeitangaben extrahieren
                time_match = re.search(
                    r'(\d+(?:[.,]\d+)?)\s*(min|minute|minuten|std|stunde|stunden)',
                    line, re.IGNORECASE
                )
                if time_match:
                    time_val = float(time_match.group(1).replace(',', '.'))
                    if 'std' in time_match.group(2).lower() or 'stunde' in time_match.group(2).lower():
                        time_val *= 60

                    if recipe_data['prep_time'] is None:
                        recipe_data['prep_time'] = int(time_val)
                    elif recipe_data['cook_time'] is None:
                        recipe_data['cook_time'] = int(time_val)

                # Portionen
                portion_match = re.search(
                    r'(\d+)\s*(portion|portionen|personen|pers\.?)',
                    line, re.IGNORECASE
                )
                if portion_match:
                    recipe_data['portions'] = int(portion_match.group(1))

                if line != recipe_data['title']:
                    description_lines.append(line)

        recipe_data['ingredients'] = ingredients
        recipe_data['description'] = '\n'.join(description_lines)

        return recipe_data

    def _is_ingredient_line(self, line: str) -> bool:
        """Prüft ob Zeile eine Zutat ist"""
        unit_pattern = r'(g|kg|mg|ml|cl|l|dl|EL|TL|Msp|Prise|Prisen|Stück|Stck|St\.|Bd|Bund|Scheibe|Scheiben|Tasse|Tassen|Dose|Dosen|Pack|Packung|Becher)'

        # Pattern 1: Zahl + Einheit
        if re.match(rf'^\s*\d+(?:[.,]\d+)?\s*({unit_pattern})', line, re.IGNORECASE):
            return True

        # Pattern 2: Zahl am Anfang + Wort
        if re.match(r'^\s*\d+(?:[.,]\d+)?\s+[a-zA-ZäöüÄÖÜß]', line):
            return True

        return False

    def _extract_ingredients(self, lines: List[str]) -> List[Dict]:
        """Extrahiert Zutaten aus Zeilen"""
        ingredients = []
        unit_pattern = r'(g|kg|mg|ml|cl|l|dl|EL|TL|Msp|Prise|Prisen|Stück|Stck|St\.|Bd|Bund|Scheibe|Scheiben|Tasse|Tassen|Dose|Dosen|Pack|Packung|Becher)'

        for line in lines:
            # Pattern 1: Zahl + Einheit + Name
            match1 = re.match(
                rf'^\s*(\d+(?:[.,]\d+)?)\s*({unit_pattern})\s+(.+)$',
                line, re.IGNORECASE
            )

            if match1:
                ingredients.append({
                    'amount': float(match1.group(1).replace(',', '.')),
                    'unit': match1.group(2),
                    'name': match1.group(3).strip()
                })
                continue

            # Pattern 2: Zahl + Name (ohne Einheit)
            match2 = re.match(r'^\s*(\d+(?:[.,]\d+)?)\s+([a-zA-ZäöüÄÖÜß].+)$', line)

            if match2:
                amount = float(match2.group(1).replace(',', '.'))
                name = match2.group(2).strip()

                # Erste Wort Einheit?
                first_word = name.split()[0] if name else ''
                if re.match(unit_pattern, first_word, re.IGNORECASE):
                    unit = first_word
                    name = ' '.join(name.split()[1:])
                else:
                    unit = 'Stück'

                ingredients.append({
                    'amount': amount,
                    'unit': unit,
                    'name': name
                })

        return ingredients

    def _empty_recipe(self) -> Dict:
        """Leere Rezeptstruktur"""
        return {
            'title': '',
            'description': '',
            'ingredients': [],
            'prep_time': None,
            'cook_time': None,
            'portions': 4
        }

    # ========================================================================
    # MAIN WORKFLOW
    # ========================================================================

    def process_image(self, image_path: str) -> Dict:
        """
        Kompletter OCR-Workflow mit Multi-Strategie-Ansatz

        Args:
            image_path: Pfad zum Rezeptbild

        Returns:
            Dictionary mit Rezeptdaten + confidence
        """
        try:
            print("\n" + "="*60)
            print("🔍 OCR-PIPELINE (Multi-Strategie)")
            print("="*60)

            # Multi-Strategie OCR
            text, strategy, ocr_score = self.extract_text_multi_strategy(image_path)

            if not text or len(text.strip()) < 10:
                print("⚠️  Kein oder zu wenig Text erkannt")
                return {
                    **self._empty_recipe(),
                    'confidence': 'low',
                    'doc_type': 'unknown'
                }

            # Debug
            print(f"\n📄 Erkannter Text ({len(text)} Zeichen):")
            print("-" * 60)
            print(text[:500])
            if len(text) > 500:
                print("...")
            print("-" * 60)

            # Parsen
            recipe_data = self.parse_recipe(text)

            # Confidence basierend auf OCR-Score und Parsing
            confidence = self._calculate_confidence(recipe_data, ocr_score)

            print(f"\n✅ Geparst: {len(recipe_data['ingredients'])} Zutaten")
            print(f"🎯 Confidence: {confidence.upper()}")
            print("="*60 + "\n")

            return {
                **recipe_data,
                'confidence': confidence,
                'doc_type': 'auto'
            }

        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten: {e}")
            import traceback
            traceback.print_exc()

            return {
                **self._empty_recipe(),
                'confidence': 'low',
                'doc_type': 'unknown'
            }

    def _calculate_confidence(self, recipe_data: Dict, ocr_score: int) -> str:
        """
        Berechnet Confidence Level

        Args:
            recipe_data: Geparste Rezeptdaten
            ocr_score: OCR-Qualitätsscore

        Returns:
            'low', 'medium', oder 'high'
        """
        score = 0

        # OCR-Score einbeziehen (max 40)
        score += min(ocr_score // 2, 40)

        # Titel vorhanden? +20
        if recipe_data['title'] and len(recipe_data['title']) > 3:
            score += 20

        # Zutaten gefunden? +10 pro Zutat (max 30)
        score += min(len(recipe_data['ingredients']) * 10, 30)

        # Beschreibung vorhanden? +10
        if recipe_data['description'] and len(recipe_data['description']) > 20:
            score += 10

        print(f"   Confidence Score: {score}/100")

        if score >= 70:
            return 'high'
        elif score >= 35:
            return 'medium'
        else:
            return 'low'
