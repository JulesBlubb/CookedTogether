"""
Datenbankmodelle für die Rezepte-Anwendung
Definiert Recipe, Ingredient, Comment, Tag und RecipeTag-Modelle
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Recipe(db.Model):
    """
    Hauptmodell für Rezepte
    Speichert Titel, Beschreibung, Bild, Portionen und Zeitangaben
    """
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(300), nullable=True)
    base_portions = db.Column(db.Integer, default=4, nullable=False)
    prep_time_minutes = db.Column(db.Integer, nullable=True)
    cook_time_minutes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Beziehungen zu anderen Tabellen
    # cascade='all, delete-orphan' sorgt dafür, dass beim Löschen eines Rezepts
    # auch alle zugehörigen Zutaten und Kommentare gelöscht werden
    ingredients = db.relationship('Ingredient', backref='recipe', lazy=True,
                                  cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='recipe', lazy=True,
                               cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='recipe_tags', backref='recipes', lazy='dynamic')

    def __repr__(self):
        return f'<Recipe {self.title}>'


class Ingredient(db.Model):
    """
    Zutatenliste für ein Rezept
    Speichert Name, Menge und Einheit
    """
    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Ingredient {self.amount} {self.unit} {self.name}>'


class Comment(db.Model):
    """
    Kommentare zu Rezepten
    Speichert Autor (optional), Inhalt und Zeitstempel
    """
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=True, default='Anonym')
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Comment by {self.author_name} on Recipe {self.recipe_id}>'


class Tag(db.Model):
    """
    Tags/Kategorien für Rezepte (z.B. Vegetarisch, Dessert, Schnell)
    Case-insensitive gespeichert
    """
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<Tag {self.name}>'

    @staticmethod
    def get_or_create(tag_name):
        """
        Findet einen existierenden Tag oder erstellt einen neuen
        Tag-Namen werden in Kleinbuchstaben gespeichert (case-insensitive)
        """
        tag_name = tag_name.strip().lower()
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        return tag


# Many-to-Many Beziehungstabelle zwischen Recipe und Tag
recipe_tags = db.Table('recipe_tags',
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipes.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)
