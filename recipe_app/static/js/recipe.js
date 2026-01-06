/**
 * Recipe.js - Rezeptseiten-Funktionalität
 * Handles cooking mode, translation, and character counter
 */

'use strict';

// Translation Toggle State
let isTranslated = false;
let originalContent = null;

// Übersetzungs-Wörterbuch für UI-Elemente
const translations = {
    'de': {
        'cooking-mode-activate': 'Kochmodus aktivieren',
        'cooking-mode-deactivate': 'Kochmodus beenden',
        'translate-btn': 'Translate',
        'portions-title': 'Portionen:',
        'portions-label': 'Portionen',
        'portions-base': 'Basis:',
        'ingredients-title': 'Zutaten',
        'preparation-title': 'Zubereitung',
        'comments-title': 'Kommentare',
        'no-comments': 'Noch keine Kommentare. Sei der Erste!',
        'add-comment-title': 'Kommentar hinzufügen',
        'author-name-label': 'Dein Name (optional):',
        'author-name-placeholder': 'Anonym',
        'comment-content-label': 'Kommentar (max. 500 Zeichen):',
        'comment-content-placeholder': 'Wie hat dir das Rezept gefallen? Hast du Tipps?',
        'submit-comment-btn': 'Kommentar absenden',
        'back-to-overview': '← Zurück zur Übersicht'
    },
    'en': {
        'cooking-mode-activate': 'Activate Cooking Mode',
        'cooking-mode-deactivate': 'Exit Cooking Mode',
        'translate-btn': 'Übersetzen',
        'portions-title': 'Servings:',
        'portions-label': 'servings',
        'portions-base': 'Base:',
        'ingredients-title': 'Ingredients',
        'preparation-title': 'Preparation',
        'comments-title': 'Comments',
        'no-comments': 'No comments yet. Be the first!',
        'add-comment-title': 'Add Comment',
        'author-name-label': 'Your Name (optional):',
        'author-name-placeholder': 'Anonymous',
        'comment-content-label': 'Comment (max. 500 characters):',
        'comment-content-placeholder': 'How did you like the recipe? Any tips?',
        'submit-comment-btn': 'Submit Comment',
        'back-to-overview': '← Back to Overview'
    }
};

/**
 * Initialize character counter for comment textarea
 */
function initCharacterCounter() {
    const contentTextarea = document.getElementById('content');
    const charCount = document.getElementById('char-count');

    if (contentTextarea && charCount) {
        contentTextarea.addEventListener('input', function() {
            charCount.textContent = this.value.length;
        });
    }
}

/**
 * Helper function to sanitize HTML
 */
function sanitizeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Cooking Mode Toggle
 */
function toggleCookingMode() {
    const recipeDetail = document.getElementById('recipe-detail');
    const btn = document.querySelector('.btn-cooking-mode');

    if (!recipeDetail || !btn) {
        console.error('Required elements not found for cooking mode');
        return;
    }

    recipeDetail.classList.toggle('cooking-mode');

    if (recipeDetail.classList.contains('cooking-mode')) {
        const deactivateText = isTranslated ? 'Exit Cooking Mode' : 'Kochmodus beenden';
        btn.innerHTML = '❌ <span>' + sanitizeHTML(deactivateText) + '</span>';
        // Zum Anfang scrollen
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        const activateText = isTranslated ? 'Activate Cooking Mode' : 'Kochmodus aktivieren';
        btn.innerHTML = '📱 <span data-i18n="cooking-mode-activate">' + sanitizeHTML(activateText) + '</span>';
    }
}

/**
 * Main translation function
 */
function translateRecipe() {
    const translateBtn = document.getElementById('translate-btn');

    if (!translateBtn) {
        console.error('Translate button not found');
        return;
    }

    if (!isTranslated) {
        // Sprache des Rezepts erkennen
        const recipeTitleElem = document.querySelector('.recipe-title');
        if (!recipeTitleElem) {
            console.error('Recipe title not found');
            return;
        }
        const recipeTitle = recipeTitleElem.textContent || '';
        const recipeDescription = document.querySelector('.recipe-description')?.textContent || '';
        const combinedText = recipeTitle + ' ' + recipeDescription;

        // Einfache Spracherkennung (Deutsch vs Englisch)
        const germanWords = ['und', 'der', 'die', 'das', 'mit', 'für', 'einen', 'eine', 'wird'];
        const englishWords = ['and', 'the', 'with', 'for', 'a', 'an', 'is', 'are'];

        let germanCount = 0;
        let englishCount = 0;

        germanWords.forEach(word => {
            if (combinedText.toLowerCase().includes(word)) germanCount++;
        });

        englishWords.forEach(word => {
            if (combinedText.toLowerCase().includes(word)) englishCount++;
        });

        const isGerman = germanCount >= englishCount;
        const targetLang = isGerman ? 'en' : 'de';
        const sourceLang = isGerman ? 'de' : 'en';

        // Original-Inhalt speichern
        saveOriginalContent();

        // Disable button während Übersetzung
        translateBtn.disabled = true;
        translateBtn.innerHTML = '⏳ <span>Translating...</span>';

        // Übersetzung durchführen
        translateContent(sourceLang, targetLang)
            .then(() => {
                // UI-Elemente übersetzen
                translateUIElements(targetLang);

                // Button-Text ändern
                const btnText = translations[targetLang]?.['translate-btn'] || 'Übersetzen';
                translateBtn.innerHTML = '🌐 <span data-i18n="translate-btn">' + sanitizeHTML(btnText) + '</span>';
                isTranslated = true;
            })
            .catch(error => {
                console.error('Translation failed:', error);
                alert('Übersetzung fehlgeschlagen. Bitte versuchen Sie es später erneut.');
            })
            .finally(() => {
                translateBtn.disabled = false;
            });
    } else {
        // Zurück zur Originalsprache
        restoreOriginalContent();

        // UI-Elemente zurücksetzen
        translateUIElements('de');

        // Button-Text zurücksetzen
        translateBtn.innerHTML = '🌐 <span data-i18n="translate-btn">Translate</span>';
        isTranslated = false;
    }
}

/**
 * Translate UI elements
 */
function translateUIElements(lang) {
    // Alle Elemente mit data-i18n Attribut übersetzen
    document.querySelectorAll('[data-i18n]').forEach(elem => {
        const key = elem.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            elem.textContent = translations[lang][key];
        }
    });

    // Placeholder-Texte übersetzen
    document.querySelectorAll('[data-i18n-placeholder]').forEach(elem => {
        const key = elem.getAttribute('data-i18n-placeholder');
        if (translations[lang] && translations[lang][key]) {
            elem.placeholder = translations[lang][key];
        }
    });
}

/**
 * Save original content before translation
 */
function saveOriginalContent() {
    const titleElem = document.querySelector('.recipe-title');
    if (!titleElem) {
        console.error('Cannot save content: title element not found');
        return;
    }

    originalContent = {
        title: titleElem.textContent || '',
        description: document.querySelector('.recipe-description')?.innerHTML || '',
        ingredients: []
    };

    document.querySelectorAll('.ingredient-name').forEach(elem => {
        originalContent.ingredients.push(elem.textContent || '');
    });
}

/**
 * Restore original content after translation
 */
function restoreOriginalContent() {
    if (!originalContent) {
        console.warn('No original content to restore');
        return;
    }

    const titleElem = document.querySelector('.recipe-title');
    if (titleElem) {
        titleElem.textContent = originalContent.title;
    }

    const descElem = document.querySelector('.recipe-description');
    if (descElem && originalContent.description) {
        descElem.innerHTML = originalContent.description;
    }

    const ingredientElems = document.querySelectorAll('.ingredient-name');
    ingredientElems.forEach((elem, index) => {
        if (index < originalContent.ingredients.length) {
            elem.textContent = originalContent.ingredients[index];
        }
    });
}

/**
 * Translate content using external API
 */
async function translateContent(sourceLang, targetLang) {
    // Titel übersetzen
    const titleElem = document.querySelector('.recipe-title');
    if (titleElem && titleElem.textContent) {
        const translatedTitle = await translateText(titleElem.textContent, sourceLang, targetLang);
        titleElem.textContent = translatedTitle;
    }

    // Beschreibung übersetzen
    const descriptionElem = document.querySelector('.recipe-description');
    if (descriptionElem && descriptionElem.innerHTML) {
        const lines = descriptionElem.innerHTML.split('<br>');
        const translatedLines = await Promise.all(
            lines.map(line => translateText(line.trim(), sourceLang, targetLang))
        );
        descriptionElem.innerHTML = translatedLines.join('<br>');
    }

    // Zutaten übersetzen (mit Rate Limiting)
    const ingredientNames = document.querySelectorAll('.ingredient-name');
    for (let i = 0; i < ingredientNames.length; i++) {
        const elem = ingredientNames[i];
        if (elem.textContent) {
            const translated = await translateText(elem.textContent, sourceLang, targetLang);
            elem.textContent = translated;

            // Kleine Verzögerung um Rate Limits zu vermeiden
            if (i < ingredientNames.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
    }
}

/**
 * Translate individual text using MyMemory API
 */
async function translateText(text, sourceLang, targetLang) {
    if (!text || text.trim() === '') return text;

    try {
        // MyMemory Translation API (kostenlos, kein API-Key erforderlich)
        const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${sourceLang}|${targetLang}`;

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

        const response = await fetch(url, {
            signal: controller.signal,
            headers: {
                'Accept': 'application/json'
            }
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.responseStatus === 200 && data.responseData?.translatedText) {
            return data.responseData.translatedText;
        } else {
            console.error('Übersetzungsfehler:', data);
            return text;
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('Übersetzung Timeout:', error);
        } else {
            console.error('Fehler bei der Übersetzung:', error);
        }
        return text;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initCharacterCounter();
});
