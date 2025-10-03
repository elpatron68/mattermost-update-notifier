# Internationalisierung (i18n) Implementierungsplan

## 1. Dependencies hinzufügen
```bash
pip install flask-babel babel
```

## 2. Konfiguration in webapp.py
```python
from flask_babel import Babel, gettext as _, ngettext, lazy_gettext

app.config['LANGUAGES'] = {
    'en': 'English',
    'de': 'Deutsch'
}
app.config['BABEL_DEFAULT_LOCALE'] = 'de'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'Europe/Berlin'

babel = Babel(app)

@babel.localeselector
def get_locale():
    return request.args.get('lang', session.get('language', 'de'))

@babel.timezoneselector  
def get_timezone():
    return 'Europe/Berlin'
```

## 3. Übersetzungsdateien erstellen
```bash
# Babel-Konfiguration
pybabel extract -F babel.cfg -k _l -o messages.pot .

# Deutsche Übersetzung
pybabel init -i messages.pot -d translations -l de
pybabel compile -d translations

# Englische Übersetzung  
pybabel init -i messages.pot -d translations -l en
pybabel compile -d translations
```

## 4. Template-Anpassungen (Beispiele)

### base.html
```html
<nav class="navbar">
    <a href="{{ url_for('index') }}">{{ _('Dashboard') }}</a>
    <a href="{{ url_for('instances') }}">{{ _('Instances') }}</a>
    <a href="{{ url_for('logout') }}">{{ _('Logout') }}</a>
</nav>

<!-- Sprachauswahl -->
<div class="language-selector">
    <a href="?lang=de">🇩🇪 Deutsch</a>
    <a href="?lang=en">🇺🇸 English</a>
</div>
```

### dashboard.html
```html
<h1>{{ _('Dashboard') }}</h1>
<p>{{ _('Found %(count)d instances to check', count=instances|length) }}</p>

{% if instances %}
    <table>
        <thead>
            <tr>
                <th>{{ _('Name') }}</th>
                <th>{{ _('Status') }}</th>
                <th>{{ _('Version') }}</th>
                <th>{{ _('Update Available') }}</th>
            </tr>
        </thead>
    </table>
{% else %}
    <div class="text-center">
        <h5>{{ _('No instances configured') }}</h5>
        <p>{{ _('Add your first Mattermost instance.') }}</p>
    </div>
{% endif %}
```

## 5. Python-Code Anpassungen

### Flash-Messages
```python
# Vorher
flash('Instanz erfolgreich hinzugefügt!', 'success')

# Nachher
flash(_('Instance successfully added!'), 'success')
```

### Logging-Messages
```python
# Vorher
logging.info('Checking instance: ' + instance['name'])

# Nachher  
logging.info(_('Checking instance: %(name)s', name=instance['name']))
```

## 6. Babel-Konfiguration (babel.cfg)
```
[python: **.py]
[jinja2: **/templates/**.html]
extensions=jinja2.ext.autoescape,jinja2.ext.with_
```

## 7. Build-Script für Übersetzungen
```bash
#!/bin/bash
# update_translations.sh

# Extrahiere neue Strings
pybabel extract -F babel.cfg -k _l -o messages.pot .

# Aktualisiere bestehende Übersetzungen
pybabel update -i messages.pot -d translations -l de
pybabel update -i messages.pot -d translations -l en

# Kompiliere Übersetzungen
pybabel compile -d translations
```

## Geschätzter Aufwand
- **Setup & Konfiguration**: 1-2 Stunden
- **Übersetzungsdateien**: 2-3 Stunden  
- **Template-Anpassungen**: 1-2 Stunden
- **Code-Anpassungen**: 1 Stunde
- **Testing & Debugging**: 1 Stunde

**Gesamt: 6-9 Stunden**
