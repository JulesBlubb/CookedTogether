Project: Family Recipe Collection Webpage with the title "Cooked Together - Recipes proofed by Weilbäche"
Target: Localhost → Raspberry Pi
Tech Stack: Python + Flask + SQLite
Focus: Mobile-first, family usability, comments, tags, cooking mode

PHASE 0 – Global Constraints (Agent Rules)

    Use Python 3
    Use Flask
    Use SQLite
    No heavy frameworks
    Images stored on filesystem

    Code must run on:

        Ubuntu (localhost)

        Raspberry Pi OS (ARM)

Step 1.1 – Create Virtual Environment
    python3 -m venv venv
    source venv/bin/activate

Step 1.2 – Install Dependencies
pip install flask flask-sqlalchemy flask-wtf pillow easyocr opencv-python
PHASE 2 – Project Structure:

Step 2.1 – Create Folder Layout
recipe_app/
├── app.py
├── config.py
├── models.py
├── ocr.py
├── requirements.txt
├── database.db
├── uploads/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── recipe.html
│   └── add_recipe.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── portions.js

PHASE 3 – Configuration:

Step 3.1 – config.py
Agent must define:

    SQLite database path
    Upload folder
    Secret key

- Ensure EasyOCR language model files are downloaded once (e.g., German: easyocr.Reader(['de']))
- Ensure OCR preprocessing works on Raspberry Pi (grayscale, optional resizing)
PHASE 4 – Database Models:
4.1 Recipe Model:
    id
    title
    description
    image_path
    base_portions
    prep_time_minutes (optional)
    cook_time_minutes (optional)

4.2 Ingredient Model
    id
    recipe_id
    name
    amount
    unit
4.3 Comment Model
    - id
    - recipe_id (FK)
    - author_name (optional)
    - content
    - created_at (timestamp)

2.4 Tag / Category Models

Tag
    - id
    - name


RecipeTag
    - recipe_id
    - tag_id

    Agent must:

    Define relationships
    Cascade delete
    Many-to-many relationship for tags
    Case-insensitive tag names

PHASE 5 – Backend Routes

Add Recipe:

    POST /add

    Handles: title, description, base portions, prep/cook time, ingredients, image, tags

    Validates input

    Saves image to /uploads

    Saves Recipe, Ingredients, Tags

    If image uploaded for OCR, pre-fill form fields (see PHASE 6)
View Recipe:

    GET /recipes/<id>

    Returns recipe + ingredients

    Returns comments

    Returns tags

    Includes base portions

Add Comment:

    POST /recipes/<id>/comments

    Validates content

    Saves timestamp

    Redirects back to recipe page

Search Recipes:

    GET /?search=term

    Searches: recipe title, description, ingredient names, tag names

    Returns unique recipes

Filter by Tag:

    GET /?tag=<tagname>

    Filters recipes by selected tag

PHASE 4 – Frontend Pages

    1. Index Page

        Lists all recipes

        Search bar

        Tag filter pills

    2. Recipe Page

        Image, ingredients, description, prep/cook time, tags

        Portion control with + / - buttons

        Comments section (list + add form)

        “Cooking Mode” button

    3.Add Recipe Page

        Form for title, description, prep/cook time, base portions

        Image upload (optional OCR autofill)  

        Dynamic ingredient rows (name, amount, unit)

        Tags input (comma-separated)

        Submit button

PHASE 5 – Portion Scaling

JavaScript handles dynamic scaling

Formula: scaled_amount = original * (new_portions / base_portions)

UX:

    Round to 1–2 decimals

    Fraction display if possible

    Base portions always visible

PHASE 6 – Lightweight OCR Autofill (New)

Objective: Pre-fill recipe form from uploaded image

Steps Agent Must Implement:
1. Image Upload

    Store in /uploads

    Pass image path to OCR function

2. OCR Processing (ocr.py)

    Use EasyOCR: reader = easyocr.Reader(['de'])

    Preprocess image:

        Grayscale

        Resize if too large

        Optional thresholding for clarity

    Extract raw text

3. Text Parsing

    Heuristics / regex rules:

        First line → Title

        Lines with numbers/units → Ingredients

        Remaining text → Description / instructions

    Optional: detect prep/cook time using regex (\d+ ?min)

4. Form Autofill

    Return parsed data as JSON

    Frontend pre-populates Add Recipe form fields

    User verifies / edits before saving

5. Constraints

    CPU-only, runs on Raspberry Pi

    Provide fallback if OCR fails → manual form entry

PHASE 7 – Cooking Mode

Requirements:

    Full-screen layout

    Large font

    High contrast

    Ingredients always visible

    Steps clearly separated

    Portion control remains accessible

    Toggle via CSS class (.cooking-mode)

    Works on mobile browsers

PHASE 8 – Comments Section

    Display all comments ordered by date (oldest → newest)

    Form to add new comment:

        Optional name

        Textarea (max 500 chars)

        Submit button

    No authentication required

    Mobile-friendly input

PHASE 9 – Tags / Categories

    Tags added on recipe creation

    Displayed as clickable pills

    Clicking a tag filters recipe list

    Tags reusable across recipes

PHASE 10 – Mobile-First Rules

    Vertical stacking layout

    Buttons ≥ 44px height

    Avoid hover interactions

    Readable on one-hand phone use

    Optional dark mode

    Cooking mode optimized for tablet/phone

PHASE 11 – Image Handling

    Accept only jpg/png

    Save to /uploads

    Store file path in database

    Display images in recipe view

PHASE 12 – Testing Checklist

    Add recipe with ingredients, tags, image

    Add comment

    Portion scaling works

    Search & tag filters work

    Cooking mode readable

    Mobile usability check (buttons, fonts, layout)

    Images display correctly