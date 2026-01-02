"""
Haupt-Flask-Anwendung für "Cooked Together - Recipes proofed by Weilbäche"
Verwaltet alle Routen, Datenbankinitialisierung und OCR-Integration
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from config import Config
from models import db, Recipe, Ingredient, Comment, Tag
from ocr import RecipeOCR

app = Flask(__name__)
app.config.from_object(Config)

# Datenbank initialisieren
db.init_app(app)

# OCR-Handler initialisieren
ocr_handler = RecipeOCR(
    language=app.config['OCR_LANGUAGE']
)


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


@app.route('/')
def index():
    """
    Startseite: Zeigt alle Rezepte mit Such- und Filterfunktion

    Query-Parameter:
        search: Suchbegriff für Titel, Beschreibung, Zutaten
        tag: Tag-Name für Filterung
    """
    # Suchbegriff aus Query-Parameter
    search_term = request.args.get('search', '').strip()

    # Tag-Filter aus Query-Parameter
    tag_filter = request.args.get('tag', '').strip()

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

    # Tag-Filter anwenden
    if tag_filter:
        tag = Tag.query.filter_by(name=tag_filter.lower()).first()
        if tag:
            query = query.filter(Recipe.tags.contains(tag))

    # Rezepte nach Erstellungsdatum sortieren (neueste zuerst)
    recipes = query.order_by(Recipe.created_at.desc()).all()

    # Alle verfügbaren Tags für Filter-Pills
    all_tags = Tag.query.order_by(Tag.name).all()

    return render_template('index.html',
                           recipes=recipes,
                           search_term=search_term,
                           tag_filter=tag_filter,
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


@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
    """
    Rezept hinzufügen - zeigt Formular an oder verarbeitet Eingaben

    GET: Zeigt leeres Formular oder OCR-vorausgefülltes Formular
    POST: Speichert neues Rezept in Datenbank
    """
    ocr_data = None

    if request.method == 'POST':
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
                image_path = filename

        # Neues Rezept erstellen
        new_recipe = Recipe(
            title=title,
            description=description,
            image_path=image_path,
            base_portions=base_portions,
            prep_time_minutes=prep_time,
            cook_time_minutes=cook_time
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
