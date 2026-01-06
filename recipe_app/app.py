"""
Haupt-Flask-Anwendung für "Cooked Together - Recipes proofed by Weilbäche"
Verwaltet alle Routen, Datenbankinitialisierung und OCR-Integration
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
from config import Config
from models import db, Recipe, Ingredient, Comment, Tag
from ocr import RecipeOCR
from chefkoch_scraper import ChefkochScraper

app = Flask(__name__)
app.config.from_object(Config)

# Datenbank initialisieren
db.init_app(app)

# OCR-Handler initialisieren
ocr_handler = RecipeOCR(
    language=app.config['OCR_LANGUAGE']
)

# Chefkoch-Scraper initialisieren
chefkoch_scraper = ChefkochScraper()


@app.after_request
def add_security_headers(response):
    """
    Fügt Sicherheitsheader zu allen Antworten hinzu
    """
    # Content Security Policy - erlaubt nur bestimmte Quellen
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' https://api.mymemory.translated.net; "
        "font-src 'self'; "
        "frame-ancestors 'none';"
    )

    # Verhindert MIME-Type Sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # XSS-Schutz (für ältere Browser)
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Verhindert Clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # Erzwingt HTTPS (wenn in Produktion)
    if not app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions Policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

    return response


def allowed_file(filename):
    """
    Prüft, ob die hochgeladene Datei ein erlaubtes Format hat

    Args:
        filename: Name der Datei

    Returns:
        True wenn erlaubt, sonst False
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def resize_image(input_path, max_width=1200, max_height=1200, quality=85):
    """
    Verkleinert ein Bild auf maximale Breite/Höhe unter Beibehaltung des Seitenverhältnisses
    
    Args:
        input_path: Pfad zum Original-Bild
        max_width: Maximale Breite in Pixeln (Standard: 1200)
        max_height: Maximale Höhe in Pixeln (Standard: 1200)
        quality: JPEG-Qualität 1-100 (Standard: 85)
    
    Returns:
        None (überschreibt Original-Datei)
    """
    try:
        with Image.open(input_path) as img:
            # Konvertiere RGBA zu RGB falls nötig
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Berechne neue Größe unter Beibehaltung des Seitenverhältnisses
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Speichere optimiertes Bild
            img.save(input_path, 'JPEG', quality=quality, optimize=True)
    except Exception as e:
        print(f"Fehler beim Verkleinern des Bildes: {e}")
        # Falls Fehler auftritt, behalte Original-Datei


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Stellt hochgeladene Bilder bereit
    
    Args:
        filename: Name der Bilddatei
    
    Returns:
        Bilddatei aus dem uploads-Ordner
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/')
def index():
    """
    Startseite: Zeigt alle Rezepte mit Such- und Filterfunktion

    Query-Parameter:
        search: Suchbegriff für Titel, Beschreibung, Zutaten
        tags: Komma-getrennte Liste von Tag-Namen für Filterung
    """
    # Suchbegriff aus Query-Parameter
    search_term = request.args.get('search', '').strip()

    # Tag-Filter aus Query-Parameter (mehrere möglich)
    tags_param = request.args.get('tags', '').strip()
    selected_tags = [t.strip().lower() for t in tags_param.split(',') if t.strip()] if tags_param else []

    # Basis-Query für Rezepte
    query = Recipe.query

    # Suchfilter anwenden
    if search_term:
        # Suche in Titel, Beschreibung, Zutaten und Tags
        search_pattern = f'%{search_term}%'

        # Rezepte mit passendem Titel oder Beschreibung
        query = query.filter(
            db.or_(
                Recipe.title.ilike(search_pattern),
                Recipe.description.ilike(search_pattern)
            )
        )

        # TODO: Zusätzliche Suche in Zutaten und Tags
        # Dies erfordert komplexere Joins

    # Tag-Filter anwenden (mehrere Tags mit UND-Verknüpfung)
    if selected_tags:
        for tag_name in selected_tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag:
                query = query.filter(Recipe.tags.contains(tag))

    # Rezepte nach Erstellungsdatum sortieren (neueste zuerst)
    recipes = query.order_by(Recipe.created_at.desc()).all()

    # Alle verfügbaren Tags für Filter-Pills
    all_tags = Tag.query.order_by(Tag.name).all()

    return render_template('index.html',
                           recipes=recipes,
                           search_term=search_term,
                           selected_tags=selected_tags,
                           all_tags=all_tags)


@app.route('/recipes/<int:recipe_id>')
def view_recipe(recipe_id):
    """
    Detailansicht eines Rezepts mit Zutaten, Kommentaren und Tags

    Args:
        recipe_id: ID des anzuzeigenden Rezepts
    """
    recipe = Recipe.query.get_or_404(recipe_id)

    # Kommentare nach Datum sortieren (älteste zuerst)
    comments = Comment.query.filter_by(recipe_id=recipe_id)\
        .order_by(Comment.created_at.asc()).all()

    return render_template('recipe.html',
                           recipe=recipe,
                           comments=comments)


def verify_auth_token():
    """
    Prüft, ob ein gültiges Token im Request vorhanden ist

    Returns:
        True wenn Token gültig, sonst False
    """
    # Token aus Request-Header holen
    token = request.headers.get('X-Auth-Token', '')

    if not token:
        # Alternative: Token aus Form-Daten
        token = request.form.get('auth_token', '')

    if not token:
        # Alternative: Token aus JSON-Body
        if request.is_json:
            data = request.get_json()
            token = data.get('token', '')

    return token == app.config['RECIPE_AUTH_TOKEN']


@app.route('/auth-token')
def auth_token_page():
    """
    Zeigt die Token-Eingabeseite an
    """
    return render_template('auth_token.html')


@app.route('/verify-token', methods=['POST'])
def verify_token():
    """
    Verifiziert ein eingegebenes Token

    Returns:
        JSON mit Erfolg oder Fehler
    """
    data = request.get_json()

    if not data or 'token' not in data:
        return jsonify({'success': False, 'error': 'Kein Token angegeben'}), 400

    token = data['token'].strip()

    if token == app.config['RECIPE_AUTH_TOKEN']:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Ungültiges Token'}), 401


@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
    """
    Rezept hinzufügen - zeigt Formular an oder verarbeitet Eingaben

    GET: Zeigt leeres Formular oder OCR-vorausgefülltes Formular
    POST: Speichert neues Rezept in Datenbank
    """
    ocr_data = None

    if request.method == 'POST':
        # Token-Überprüfung für POST-Requests
        if not verify_auth_token():
            flash('Ungültiges oder fehlendes Authentifizierungs-Token!', 'error')
            return redirect(url_for('auth_token_page'))
        # Formulardaten verarbeiten
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        base_portions = request.form.get('base_portions', 4, type=int)
        prep_time = request.form.get('prep_time', None, type=int)
        cook_time = request.form.get('cook_time', None, type=int)

        # Validierung
        if not title:
            flash('Bitte einen Titel eingeben!', 'error')
            return redirect(url_for('add_recipe'))

        # Bild hochladen (falls vorhanden)
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Eindeutigen Dateinamen generieren
                import time
                filename = f"{int(time.time())}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Bild verkleinern für bessere Performance
                resize_image(filepath)
                image_path = filename

        # Quellenangaben (falls vorhanden)
        source = request.form.get('source', '').strip()
        source_url = request.form.get('source_url', '').strip()

        # Neues Rezept erstellen
        new_recipe = Recipe(
            title=title,
            description=description,
            image_path=image_path,
            base_portions=base_portions,
            prep_time_minutes=prep_time,
            cook_time_minutes=cook_time,
            source=source if source else None,
            source_url=source_url if source_url else None
        )

        db.session.add(new_recipe)
        db.session.flush()  # ID generieren ohne zu committen

        # Zutaten hinzufügen
        ingredient_names = request.form.getlist('ingredient_name[]')
        ingredient_amounts = request.form.getlist('ingredient_amount[]')
        ingredient_units = request.form.getlist('ingredient_unit[]')

        for name, amount, unit in zip(ingredient_names, ingredient_amounts, ingredient_units):
            if name.strip() and amount:
                try:
                    ingredient = Ingredient(
                        recipe_id=new_recipe.id,
                        name=name.strip(),
                        amount=float(amount),
                        unit=unit.strip()
                    )
                    db.session.add(ingredient)
                except ValueError:
                    continue  # Ungültige Mengenangabe überspringen

        # Tags hinzufügen
        tags_input = request.form.get('tags', '').strip()
        if tags_input:
            tag_names = [t.strip() for t in tags_input.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.get_or_create(tag_name)
                new_recipe.tags.append(tag)

        # In Datenbank speichern
        try:
            db.session.commit()
            flash(f'Rezept "{title}" erfolgreich hinzugefügt!', 'success')
            return redirect(url_for('view_recipe', recipe_id=new_recipe.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern: {str(e)}', 'error')
            return redirect(url_for('add_recipe'))

    # GET-Request: Formular anzeigen
    return render_template('add_recipe.html', ocr_data=ocr_data)


@app.route('/ocr-upload', methods=['POST'])
def ocr_upload():
    """
    OCR-Endpunkt: Verarbeitet hochgeladenes Bild und gibt geparste Daten zurück

    Returns:
        JSON mit extrahierten Rezeptdaten
    """
    if 'image' not in request.files:
        return jsonify({'error': 'Kein Bild hochgeladen'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'Keine Datei ausgewählt'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Ungültiges Dateiformat'}), 400

    try:
        # Bild temporär speichern
        filename = secure_filename(file.filename)
        import time
        filename = f"temp_{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Bild verkleinern für bessere Performance (vor OCR)
        resize_image(filepath)

        # OCR durchführen
        recipe_data = ocr_handler.process_image(filepath)

        # Rückgabe als JSON
        return jsonify({
            'success': True,
            'data': recipe_data,
            'image_filename': filename
        })

    except Exception as e:
        return jsonify({'error': f'OCR-Fehler: {str(e)}'}), 500


@app.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """
    Rezept bearbeiten - zeigt Formular an oder verarbeitet Änderungen

    Args:
        recipe_id: ID des zu bearbeitenden Rezepts

    GET: Zeigt ausgefülltes Formular mit aktuellen Daten
    POST: Speichert Änderungen in Datenbank
    """
    recipe = Recipe.query.get_or_404(recipe_id)

    if request.method == 'POST':
        # Token-Überprüfung für POST-Requests
        if not verify_auth_token():
            flash('Ungültiges oder fehlendes Authentifizierungs-Token!', 'error')
            return redirect(url_for('auth_token_page'))

        # Formulardaten verarbeiten
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        base_portions = request.form.get('base_portions', 4, type=int)
        prep_time = request.form.get('prep_time', None, type=int)
        cook_time = request.form.get('cook_time', None, type=int)

        # Validierung
        if not title:
            flash('Bitte einen Titel eingeben!', 'error')
            return redirect(url_for('edit_recipe', recipe_id=recipe_id))

        # Bild hochladen (falls vorhanden)
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                import time
                filename = f"{int(time.time())}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Bild verkleinern für bessere Performance
                resize_image(filepath)
                recipe.image_path = filename

        # Quellenangaben
        source = request.form.get('source', '').strip()
        source_url = request.form.get('source_url', '').strip()

        # Rezept aktualisieren
        recipe.title = title
        recipe.description = description
        recipe.base_portions = base_portions
        recipe.prep_time_minutes = prep_time
        recipe.cook_time_minutes = cook_time
        recipe.source = source if source else None
        recipe.source_url = source_url if source_url else None

        # Alte Zutaten löschen
        Ingredient.query.filter_by(recipe_id=recipe_id).delete()

        # Neue Zutaten hinzufügen
        ingredient_names = request.form.getlist('ingredient_name[]')
        ingredient_amounts = request.form.getlist('ingredient_amount[]')
        ingredient_units = request.form.getlist('ingredient_unit[]')

        for name, amount, unit in zip(ingredient_names, ingredient_amounts, ingredient_units):
            if name.strip() and amount:
                try:
                    ingredient = Ingredient(
                        recipe_id=recipe_id,
                        name=name.strip(),
                        amount=float(amount),
                        unit=unit.strip()
                    )
                    db.session.add(ingredient)
                except ValueError:
                    continue

        # Tags aktualisieren
        # Alle aktuellen Tags entfernen
        recipe.tags = []
        tags_input = request.form.get('tags', '').strip()
        if tags_input:
            tag_names = [t.strip() for t in tags_input.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.get_or_create(tag_name)
                recipe.tags.append(tag)

        # In Datenbank speichern
        try:
            db.session.commit()
            flash(f'Rezept "{title}" erfolgreich aktualisiert!', 'success')
            return redirect(url_for('view_recipe', recipe_id=recipe_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern: {str(e)}', 'error')
            return redirect(url_for('edit_recipe', recipe_id=recipe_id))

    # GET-Request: Formular mit aktuellen Daten anzeigen
    return render_template('edit_recipe.html', recipe=recipe)


@app.route('/import-chefkoch', methods=['POST'])
def import_chefkoch():
    """
    Chefkoch-Import-Endpunkt: Lädt Rezept von Chefkoch.de und gibt strukturierte Daten zurück

    Returns:
        JSON mit extrahierten Rezeptdaten
    """
    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({'error': 'Keine URL angegeben'}), 400

    url = data['url'].strip()

    if not url:
        return jsonify({'error': 'URL darf nicht leer sein'}), 400

    try:
        # Rezept scrapen
        recipe_data = chefkoch_scraper.scrape_recipe(url)

        return jsonify({
            'success': True,
            'data': recipe_data
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Import-Fehler: {str(e)}'}), 500


@app.route('/recipes/<int:recipe_id>/comments', methods=['POST'])
def add_comment(recipe_id):
    """
    Kommentar zu einem Rezept hinzufügen

    Args:
        recipe_id: ID des Rezepts
    """
    recipe = Recipe.query.get_or_404(recipe_id)

    author_name = request.form.get('author_name', '').strip() or 'Anonym'
    content = request.form.get('content', '').strip()

    # Validierung
    if not content:
        flash('Kommentar darf nicht leer sein!', 'error')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))

    if len(content) > 500:
        flash('Kommentar ist zu lang (max. 500 Zeichen)!', 'error')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))

    # Kommentar speichern
    new_comment = Comment(
        recipe_id=recipe_id,
        author_name=author_name,
        content=content
    )

    db.session.add(new_comment)

    try:
        db.session.commit()
        flash('Kommentar hinzugefügt!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Speichern: {str(e)}', 'error')

    return redirect(url_for('view_recipe', recipe_id=recipe_id))


@app.route('/init-db')
def init_database():
    """
    Initialisiert die Datenbank (nur für Entwicklung)
    Erstellt alle Tabellen
    """
    with app.app_context():
        db.create_all()
        return "Datenbank initialisiert!"


if __name__ == '__main__':
    # Upload-Ordner erstellen falls nicht vorhanden
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Datenbank initialisieren
    with app.app_context():
        db.create_all()

    # App starten
    # debug=True nur für Entwicklung, in Produktion auf False setzen
    app.run(host='0.0.0.0', port=5000, debug=True)
