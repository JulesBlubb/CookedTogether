"""
Chefkoch.de Recipe Scraper
Lädt Rezepte von Chefkoch.de und extrahiert strukturierte Daten aus dem HTML
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional


class ChefkochScraper:
    """Scraper für Chefkoch.de Rezepte"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def is_valid_chefkoch_url(self, url: str) -> bool:
        """
        Prüft, ob die URL eine gültige Chefkoch-Rezept-URL ist

        Args:
            url: Die zu prüfende URL

        Returns:
            True wenn gültig, sonst False
        """
        return bool(re.match(r'https?://(www\.)?chefkoch\.de/rezepte/', url))

    def parse_ingredient_string(self, ingredient_str: str) -> Dict[str, any]:
        """
        Parst eine Zutat aus dem Format "500 g Mehl" in strukturierte Daten

        Args:
            ingredient_str: String wie "500 g Mehl" oder "2 EL Öl"

        Returns:
            Dictionary mit amount, unit, name
        """
        ingredient_str = ingredient_str.strip()

        # Pattern: Zahl + Einheit + Name
        match = re.match(r'^([\d,\.\/½¼¾⅓⅔⅛]+)\s*([a-zA-ZäöüÄÖÜß]*)\s+(.+)$', ingredient_str)

        if match:
            amount_str = match.group(1).replace(',', '.')

            # Brüche konvertieren
            fraction_map = {'½': '0.5', '¼': '0.25', '¾': '0.75', '⅓': '0.33', '⅔': '0.67', '⅛': '0.125'}
            for frac, decimal in fraction_map.items():
                amount_str = amount_str.replace(frac, decimal)

            if '/' in amount_str and len(amount_str) <= 3:
                parts = amount_str.split('/')
                try:
                    amount_str = str(float(parts[0]) / float(parts[1]))
                except (ValueError, ZeroDivisionError):
                    amount_str = '1.0'

            try:
                amount = float(amount_str)
            except ValueError:
                amount = 1.0

            unit = match.group(2).strip()
            name = match.group(3).strip()

            return {'amount': amount, 'unit': unit, 'name': name}

        # Nur Zahl + Name
        match = re.match(r'^([\d,\.]+)\s+(.+)$', ingredient_str)
        if match:
            try:
                amount = float(match.group(1).replace(',', '.'))
            except ValueError:
                amount = 1.0
            return {'amount': amount, 'unit': '', 'name': match.group(2).strip()}

        # Fallback: Ganze Zeile als Name
        return {'amount': 1.0, 'unit': 'Stück', 'name': ingredient_str}

    def scrape_recipe(self, url: str) -> Optional[Dict]:
        """
        Scraped ein Rezept von Chefkoch.de durch HTML-Parsing

        Args:
            url: Die Chefkoch-Rezept-URL

        Returns:
            Dictionary mit Rezeptdaten oder None bei Fehler
        """
        if not self.is_valid_chefkoch_url(url):
            raise ValueError("Ungültige Chefkoch-URL")

        try:
            # Seite abrufen
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Versuche JSON-LD Schema zu finden
            recipe_data = None
            json_ld_scripts = soup.find_all('script', type='application/ld+json')

            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    # Kann ein einzelnes Objekt oder Array sein
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Recipe':
                                recipe_data = item
                                break
                    elif isinstance(data, dict) and data.get('@type') == 'Recipe':
                        recipe_data = data

                    if recipe_data:
                        break
                except (json.JSONDecodeError, AttributeError):
                    continue

            if not recipe_data:
                raise Exception("Kein Recipe-Schema im HTML gefunden. Chefkoch.de hat möglicherweise seine Struktur geändert.")

            # Daten aus Schema extrahieren
            title = recipe_data.get('name', 'Unbekanntes Rezept')

            # Beschreibung/Anleitung
            description = ''
            if 'recipeInstructions' in recipe_data:
                instructions = recipe_data['recipeInstructions']
                if isinstance(instructions, str):
                    description = instructions
                elif isinstance(instructions, list):
                    # Liste von HowToStep Objekten oder HowToSection
                    steps = []
                    for item in instructions:
                        if isinstance(item, dict):
                            # HowToSection mit itemListElement
                            if item.get('@type') == 'HowToSection' and 'itemListElement' in item:
                                for step in item['itemListElement']:
                                    if isinstance(step, dict):
                                        text = step.get('text', '')
                                        if text:
                                            steps.append(text)
                            # Direkter HowToStep
                            elif item.get('@type') == 'HowToStep' or 'text' in item:
                                text = item.get('text', '')
                                if text:
                                    steps.append(text)
                        else:
                            text = str(item)
                            if text:
                                steps.append(text)
                    description = '\n\n'.join(steps)

            # Portionen
            portions = 4
            if 'recipeYield' in recipe_data:
                yield_str = recipe_data['recipeYield']
                if isinstance(yield_str, str):
                    portions_match = re.search(r'(\d+)', yield_str)
                    if portions_match:
                        portions = int(portions_match.group(1))
                elif isinstance(yield_str, (int, float)):
                    portions = int(yield_str)

            # Zutaten
            ingredients = []
            if 'recipeIngredient' in recipe_data:
                for ing_str in recipe_data['recipeIngredient']:
                    parsed_ing = self.parse_ingredient_string(ing_str)
                    ingredients.append(parsed_ing)

            # Zeiten (ISO 8601 Format: PT30M)
            prep_time = None
            cook_time = None

            if 'prepTime' in recipe_data:
                prep_time = self.parse_iso_duration(recipe_data['prepTime'])

            if 'cookTime' in recipe_data:
                cook_time = self.parse_iso_duration(recipe_data['cookTime'])

            # Fallback auf totalTime
            if not prep_time and not cook_time and 'totalTime' in recipe_data:
                prep_time = self.parse_iso_duration(recipe_data['totalTime'])

            return {
                'title': title,
                'description': description,
                'ingredients': ingredients,
                'base_portions': portions,
                'prep_time_minutes': prep_time,
                'cook_time_minutes': cook_time,
                'source_url': url,
                'source': 'chefkoch.de'
            }

        except requests.RequestException as e:
            raise Exception(f"Fehler beim Abrufen der URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Fehler beim Parsen des Rezepts: {str(e)}")

    def parse_iso_duration(self, duration_str: str) -> Optional[int]:
        """
        Konvertiert ISO 8601 Duration (z.B. PT30M) in Minuten

        Args:
            duration_str: ISO 8601 Duration String

        Returns:
            Minuten als Integer oder None
        """
        if not duration_str:
            return None

        # Format: PT30M (30 Minuten), PT1H30M (1 Stunde 30 Minuten), PT2H (2 Stunden)
        hours = 0
        minutes = 0

        hour_match = re.search(r'(\d+)H', duration_str)
        if hour_match:
            hours = int(hour_match.group(1))

        minute_match = re.search(r'(\d+)M', duration_str)
        if minute_match:
            minutes = int(minute_match.group(1))

        total_minutes = hours * 60 + minutes
        return total_minutes if total_minutes > 0 else None
