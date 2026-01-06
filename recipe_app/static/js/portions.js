/**
 * Portions.js - Dynamische Portionsskalierung für Rezepte
 * Skaliert Zutatenmenge basierend auf gewünschter Portionenzahl
 */

// Globale Variable für aktuelle Portionen (wird in recipe.html gesetzt)
let currentPortions = BASE_PORTIONS || 4;

/**
 * Erhöht die Portionenzahl um 0.5
 */
function incrementPortions() {
    if (currentPortions < 50) { // Max 50 Portionen
        currentPortions += 0.5;
        updatePortions();
    }
}

/**
 * Verringert die Portionenzahl um 0.5
 */
function decrementPortions() {
    if (currentPortions > 0.5) { // Min 0.5 Portion
        currentPortions -= 0.5;
        updatePortions();
    }
}

/**
 * Aktualisiert die Anzeige und alle Zutatenmenge
 */
function updatePortions() {
    // Portionenanzahl aktualisieren
    const portionDisplay = document.getElementById('current-portions');
    if (portionDisplay) {
        // Halbe Portionen als "½" anzeigen
        if (currentPortions % 1 === 0.5) {
            const wholePart = Math.floor(currentPortions);
            if (wholePart > 0) {
                portionDisplay.textContent = `${wholePart} ½`;
            } else {
                portionDisplay.textContent = '½';
            }
        } else {
            portionDisplay.textContent = currentPortions;
        }
    }

    // Alle Zutaten aktualisieren
    updateIngredients();
}

/**
 * Berechnet und aktualisiert alle Zutatenmenge
 */
function updateIngredients() {
    const ingredientsList = document.getElementById('ingredients-list');
    if (!ingredientsList) return;

    const ingredients = ingredientsList.querySelectorAll('.ingredient-item');

    ingredients.forEach(ingredient => {
        const baseAmount = parseFloat(ingredient.dataset.baseAmount);
        const unit = ingredient.dataset.unit;
        const name = ingredient.dataset.name;

        if (isNaN(baseAmount)) return;

        // Neue Menge berechnen
        const scaledAmount = (baseAmount * currentPortions) / BASE_PORTIONS;

        // Menge formatieren
        const formattedAmount = formatAmount(scaledAmount);

        // Anzeige aktualisieren
        const amountSpan = ingredient.querySelector('.ingredient-amount');
        if (amountSpan) {
            amountSpan.textContent = formattedAmount;
        }
    });
}

/**
 * Formatiert eine Menge für bessere Lesbarkeit
 *
 * @param {number} amount - Die zu formatierende Menge
 * @returns {string} Formatierte Menge (ggf. als Bruch)
 */
function formatAmount(amount) {
    // Rundung auf 2 Dezimalstellen
    const rounded = Math.round(amount * 100) / 100;

    // Ganze Zahlen ohne Dezimalstellen anzeigen
    if (Number.isInteger(rounded)) {
        return rounded.toString();
    }

    // Versuche, häufige Brüche zu erkennen
    const fractions = [
        { decimal: 0.25, text: '¼' },
        { decimal: 0.33, text: '⅓' },
        { decimal: 0.5, text: '½' },
        { decimal: 0.66, text: '⅔' },
        { decimal: 0.75, text: '¾' }
    ];

    // Ganzzahligen Teil und Dezimalteil trennen
    const wholePart = Math.floor(rounded);
    const decimalPart = rounded - wholePart;

    // Prüfen, ob Dezimalteil einem Bruch entspricht (mit Toleranz)
    for (let fraction of fractions) {
        if (Math.abs(decimalPart - fraction.decimal) < 0.05) {
            if (wholePart > 0) {
                return `${wholePart} ${fraction.text}`;
            } else {
                return fraction.text;
            }
        }
    }

    // Falls kein passender Bruch, mit 1-2 Dezimalstellen anzeigen
    if (rounded < 1) {
        return rounded.toFixed(2);
    } else if (rounded < 10) {
        return rounded.toFixed(1);
    } else {
        return rounded.toFixed(0);
    }
}

/**
 * Initialisierung beim Laden der Seite
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initiale Anzeige aktualisieren
    updatePortions();

    // Optional: Tastatursteuerung für Portionen
    document.addEventListener('keydown', function(e) {
        // Nur auf Rezeptseite aktiv
        if (!document.getElementById('ingredients-list')) return;

        // Plus-Taste oder Pfeil nach oben
        if (e.key === '+' || e.key === 'ArrowUp') {
            e.preventDefault();
            incrementPortions();
        }

        // Minus-Taste oder Pfeil nach unten
        if (e.key === '-' || e.key === 'ArrowDown') {
            e.preventDefault();
            decrementPortions();
        }
    });
});

/**
 * Service Worker für Offline-Funktionalität (optional für zukünftige Erweiterung)
 */
if ('serviceWorker' in navigator) {
    // Auskommentiert - kann später aktiviert werden
    // window.addEventListener('load', function() {
    //     navigator.serviceWorker.register('/sw.js');
    // });
}
