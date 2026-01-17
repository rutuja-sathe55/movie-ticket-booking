// Theme switcher: applies selected theme by setting data-theme on <body>
(function () {
    const THEME_KEY = 'cinebook_theme';
    const body = document.getElementById('page-body') || document.body;

    function applyTheme(name) {
        if (!name || name === 'default') {
            body.removeAttribute('data-theme');
            localStorage.removeItem(THEME_KEY);
            return;
        }
        body.setAttribute('data-theme', name);
        localStorage.setItem(THEME_KEY, name);
    }

    // Initialize from localStorage
    document.addEventListener('DOMContentLoaded', () => {
        const saved = localStorage.getItem(THEME_KEY) || 'default';
        applyTheme(saved);

        // Wire up dropdown buttons
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const t = btn.getAttribute('data-theme');
                applyTheme(t);
                // close bootstrap dropdown (works with bootstrap bundle)
                const dropdown = bootstrap.Dropdown.getOrCreateInstance(document.getElementById('themeDropdown'));
                dropdown.hide();
            });
        });
    });
})();
