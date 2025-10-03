#!/usr/bin/env python3
"""
Mattermost Update Notifier - Admin Web Interface
"""

import os
import json
import logging
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
# Removed Flask-Babel import due to compatibility issues
from dotenv import load_dotenv
from packaging import version

# Load environment variables
load_dotenv('config.env')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configuration
WEB_PORT = int(os.environ.get('WEB_PORT', 5000))
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
INSTANCES_FILE = './data/instances.json'

# Language Configuration
LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch'
}

# Simple language support without Flask-Babel for now
def get_current_language():
    return request.args.get('lang', session.get('language', 'de'))

def translate_text(text, lang=None):
    """Simple translation function"""
    if lang is None:
        lang = get_current_language()
    
    # Simple German translations
    translations = {
        'de': {
            'Dashboard': 'Dashboard',
            'Instances': 'Instanzen', 
            'Logout': 'Abmelden',
            'Admin Login': 'Admin-Anmeldung',
            'Password': 'Passwort',
            'Login': 'Anmelden',
            'Successfully logged in!': 'Erfolgreich angemeldet!',
            'Invalid password!': 'Ungültiges Passwort!',
            'Successfully logged out!': 'Erfolgreich abgemeldet!',
            'Language changed to %(lang)s': 'Sprache geändert zu %(lang)s',
            'Refresh': 'Aktualisieren',
            'Online': 'Online',
            'Updates Available': 'Updates verfügbar',
            'Update Available': 'Update verfügbar',
            'Instance Status': 'Instanz-Status',
            'Instance Management': 'Instanz-Verwaltung',
            'New Instance': 'Neue Instanz',
            'Configured Instances': 'Konfigurierte Instanzen',
            'Name': 'Name',
            'API URL': 'API URL',
            'Webhook URL': 'Webhook URL',
            'Channel': 'Channel',
            'Actions': 'Aktionen',
            'Edit': 'Bearbeiten',
            'Delete': 'Löschen',
            'No instances configured': 'Keine Instanzen konfiguriert',
            'Add your first Mattermost instance.': 'Fügen Sie Ihre erste Mattermost-Instanz hinzu.',
            'Add Instance': 'Instanz hinzufügen',
            'Delete Instance': 'Instanz löschen',
            'Are you sure you want to delete the instance': 'Sind Sie sicher, dass Sie die Instanz',
            'This action cannot be undone.': 'Diese Aktion kann nicht rückgängig gemacht werden.',
            'Cancel': 'Abbrechen',
            'Add New Mattermost Instance': 'Neue Mattermost-Instanz hinzufügen',
            'Instance Name': 'Instanz-Name',
            'Unique name to identify the instance': 'Eindeutiger Name zur Identifikation der Instanz',
            'URL to fetch the Mattermost version': 'URL zum Abrufen der Mattermost-Version',
            'Incoming webhook URL for notifications': 'Incoming Webhook URL für Benachrichtigungen',
            'Channel (optional)': 'Channel (optional)',
            'Channel for update notifications (empty = default channel)': 'Channel für Update-Benachrichtigungen (leer = Standard-Channel)',
            'Back': 'Zurück',
            'Help': 'Hilfe',
            'Finding API URL:': 'API URL finden:',
            'The API URL is usually:': 'Die API URL ist normalerweise:',
            'Creating Webhook URL:': 'Webhook URL erstellen:',
            'Go to your Mattermost → System Console → Integrations': 'Gehen Sie zu Ihrem Mattermost → System Console → Integrations',
            'Enable "Enable Incoming Webhooks"': 'Aktivieren Sie "Enable Incoming Webhooks"',
            'Go to a channel → Channel Info → Integrations': 'Gehen Sie zu einem Channel → Channel Info → Integrations',
            'Click "Incoming Webhooks" → "Add Incoming Webhook"': 'Klicken Sie auf "Incoming Webhooks" → "Add Incoming Webhook"',
            'Copy the generated webhook URL': 'Kopieren Sie die generierte Webhook-URL',
        },
        'en': {
            'Dashboard': 'Dashboard',
            'Instances': 'Instances',
            'Logout': 'Logout', 
            'Admin Login': 'Admin Login',
            'Password': 'Password',
            'Login': 'Login',
            'Successfully logged in!': 'Successfully logged in!',
            'Invalid password!': 'Invalid password!',
            'Successfully logged out!': 'Successfully logged out!',
            'Language changed to %(lang)s': 'Language changed to %(lang)s',
            'Refresh': 'Refresh',
            'Online': 'Online',
            'Updates Available': 'Updates Available',
            'Update Available': 'Update Available',
            'Instance Status': 'Instance Status',
            'Instance Management': 'Instance Management',
            'New Instance': 'New Instance',
            'Configured Instances': 'Configured Instances',
            'Name': 'Name',
            'API URL': 'API URL',
            'Webhook URL': 'Webhook URL',
            'Channel': 'Channel',
            'Actions': 'Actions',
            'Edit': 'Edit',
            'Delete': 'Delete',
            'No instances configured': 'No instances configured',
            'Add your first Mattermost instance.': 'Add your first Mattermost instance.',
            'Add Instance': 'Add Instance',
            'Delete Instance': 'Delete Instance',
            'Are you sure you want to delete the instance': 'Are you sure you want to delete the instance',
            'This action cannot be undone.': 'This action cannot be undone.',
            'Cancel': 'Cancel',
            'Add New Mattermost Instance': 'Add New Mattermost Instance',
            'Instance Name': 'Instance Name',
            'Unique name to identify the instance': 'Unique name to identify the instance',
            'URL to fetch the Mattermost version': 'URL to fetch the Mattermost version',
            'Incoming webhook URL for notifications': 'Incoming webhook URL for notifications',
            'Channel (optional)': 'Channel (optional)',
            'Channel for update notifications (empty = default channel)': 'Channel for update notifications (empty = default channel)',
            'Back': 'Back',
            'Help': 'Help',
            'Finding API URL:': 'Finding API URL:',
            'The API URL is usually:': 'The API URL is usually:',
            'Creating Webhook URL:': 'Creating Webhook URL:',
            'Go to your Mattermost → System Console → Integrations': 'Go to your Mattermost → System Console → Integrations',
            'Enable "Enable Incoming Webhooks"': 'Enable "Enable Incoming Webhooks"',
            'Go to a channel → Channel Info → Integrations': 'Go to a channel → Channel Info → Integrations',
            'Click "Incoming Webhooks" → "Add Incoming Webhook"': 'Click "Incoming Webhooks" → "Add Incoming Webhook"',
            'Copy the generated webhook URL': 'Copy the generated webhook URL',
        }
    }
    
    return translations.get(lang, {}).get(text, text)

# Mock _ function for templates
def _(text):
    return translate_text(text)

# Configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_instances():
    """Load instances from JSON file"""
    try:
        with open(INSTANCES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f'Instances file not found: {INSTANCES_FILE}')
        return []
    except json.JSONDecodeError as e:
        logging.error(f'Invalid JSON in instances file: {e}')
        return []
    except Exception as e:
        logging.error(f'Error loading instances: {e}')
        return []

def save_instances(instances):
    """Save instances to JSON file"""
    try:
        # Ensure data directory exists
        os.makedirs('./data', exist_ok=True)
        
        with open(INSTANCES_FILE, 'w') as f:
            json.dump(instances, f, indent=4)
        return True
    except Exception as e:
        logging.error(f'Error saving instances: {e}')
        return False

def get_instance_status(api_url):
    """Get status and version of a Mattermost instance"""
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Version' in data:
            return {
                'status': 'online',
                'version': data['Version'],
                'error': None
            }
        else:
            return {
                'status': 'error',
                'version': None,
                'error': 'Version field not found in API response'
            }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'offline',
            'version': None,
            'error': str(e)
        }
    except Exception as e:
        return {
            'status': 'error',
            'version': None,
            'error': str(e)
        }

def get_latest_version():
    """Get latest Mattermost version from releases page"""
    try:
        from requests_html import HTMLSession
        session = HTMLSession()
        r = session.get('https://releases.mattermost.com', timeout=30)
        r.raise_for_status()
        
        # Parse version from download URLs
        import re
        regex = r'https:\/\/releases\.mattermost\.com\/\d+\.\d+\.\d+\/mattermost-team-\d+\.\d+\.\d+-linux-amd64\.tar\.gz'
        downloadUrls = re.findall(regex, r.text)
        
        if downloadUrls:
            versions = re.findall(r'\d+\.\d+\.\d+', downloadUrls[0])
            if versions:
                return versions[0]
        
        return None
    except Exception as e:
        logging.error(f'Error getting latest version: {e}')
        return None

@app.route('/')
@require_auth
def index():
    """Main dashboard"""
    instances = load_instances()
    latest_version = get_latest_version()
    
    # Get status for each instance
    instance_statuses = []
    for i, instance in enumerate(instances):
        status = get_instance_status(instance['api'])
        instance_statuses.append({
            'index': i,
            'name': instance['name'],
            'api': instance['api'],
            'webhook': instance['url'],
            'channel': instance.get('channel', ''),
            'status': status['status'],
            'version': status['version'],
            'error': status['error'],
            'needs_update': False
        })
        
        # Check if update is needed
        if status['version'] and latest_version:
            try:
                instance_statuses[-1]['needs_update'] = version.parse(latest_version) > version.parse(status['version'])
            except:
                pass
    
    return render_template('dashboard.html', 
                         instances=instance_statuses, 
                         latest_version=latest_version)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            flash(_('Successfully logged in!'), 'success')
            return redirect(url_for('index'))
        else:
            flash(_('Invalid password!'), 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('authenticated', None)
    flash(_('Successfully logged out!'), 'success')
    return redirect(url_for('login'))

@app.route('/set_language/<language>')
def set_language(language):
    """Set language preference"""
    if language in LANGUAGES:
        session['language'] = language
        flash(_('Language changed to %(lang)s') % {'lang': LANGUAGES[language]}, 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/instances')
@require_auth
def instances():
    """Instance management page"""
    instances = load_instances()
    return render_template('instances.html', instances=instances)

@app.route('/instances/add', methods=['GET', 'POST'])
@require_auth
def add_instance():
    """Add new instance"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        api_url = request.form.get('api_url', '').strip()
        webhook_url = request.form.get('webhook_url', '').strip()
        channel = request.form.get('channel', '').strip()
        
        # Validate input
        if not name or not api_url or not webhook_url:
            flash('Name, API URL und Webhook URL sind erforderlich!', 'error')
            return render_template('add_instance.html')
        
        # Test API connection
        status = get_instance_status(api_url)
        if status['status'] == 'offline':
            flash(f'API ist nicht erreichbar: {status["error"]}', 'error')
            return render_template('add_instance.html')
        
        # Load existing instances
        instances = load_instances()
        
        # Check if name already exists
        if any(inst['name'] == name for inst in instances):
            flash('Eine Instanz mit diesem Namen existiert bereits!', 'error')
            return render_template('add_instance.html')
        
        # Add new instance
        new_instance = {
            'name': name,
            'url': webhook_url,
            'api': api_url,
            'channel': channel
        }
        
        instances.append(new_instance)
        
        if save_instances(instances):
            flash(f'Instanz "{name}" erfolgreich hinzugefügt!', 'success')
            return redirect(url_for('instances'))
        else:
            flash('Fehler beim Speichern der Instanz!', 'error')
    
    return render_template('add_instance.html')

@app.route('/instances/edit/<int:index>', methods=['GET', 'POST'])
@require_auth
def edit_instance(index):
    """Edit existing instance"""
    instances = load_instances()
    
    if not (0 <= index < len(instances)):
        flash('Ungültige Instanz!', 'error')
        return redirect(url_for('instances'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        api_url = request.form.get('api_url', '').strip()
        webhook_url = request.form.get('webhook_url', '').strip()
        channel = request.form.get('channel', '').strip()
        
        # Validate input
        if not name or not api_url or not webhook_url:
            flash('Name, API URL und Webhook URL sind erforderlich!', 'error')
            return render_template('edit_instance.html', instance=instances[index], index=index)
        
        # Test API connection
        status = get_instance_status(api_url)
        if status['status'] == 'offline':
            flash(f'API ist nicht erreichbar: {status["error"]}', 'error')
            return render_template('edit_instance.html', instance=instances[index], index=index)
        
        # Check if name already exists (excluding current instance)
        if any(inst['name'] == name and i != index for i, inst in enumerate(instances)):
            flash('Eine Instanz mit diesem Namen existiert bereits!', 'error')
            return render_template('edit_instance.html', instance=instances[index], index=index)
        
        # Update instance
        instances[index] = {
            'name': name,
            'url': webhook_url,
            'api': api_url,
            'channel': channel
        }
        
        if save_instances(instances):
            flash(f'Instanz "{name}" erfolgreich aktualisiert!', 'success')
            return redirect(url_for('instances'))
        else:
            flash('Fehler beim Speichern der Instanz!', 'error')
    
    return render_template('edit_instance.html', instance=instances[index], index=index)

@app.route('/instances/delete/<int:index>', methods=['POST'])
@require_auth
def delete_instance(index):
    """Delete instance"""
    instances = load_instances()
    
    if 0 <= index < len(instances):
        instance_name = instances[index]['name']
        instances.pop(index)
        
        if save_instances(instances):
            flash(f'Instanz "{instance_name}" erfolgreich gelöscht!', 'success')
        else:
            flash('Fehler beim Löschen der Instanz!', 'error')
    else:
        flash('Ungültige Instanz!', 'error')
    
    return redirect(url_for('instances'))

@app.route('/api/status')
@require_auth
def api_status():
    """API endpoint for status updates"""
    instances = load_instances()
    latest_version = get_latest_version()
    
    status_data = []
    for instance in instances:
        status = get_instance_status(instance['api'])
        status_data.append({
            'name': instance['name'],
            'status': status['status'],
            'version': status['version'],
            'error': status['error']
        })
    
    return jsonify({
        'instances': status_data,
        'latest_version': latest_version,
        'timestamp': datetime.now().isoformat()
    })

# Make translation function available in templates
app.jinja_env.globals.update(_=_)

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('./data', exist_ok=True)
    
    logging.info(f'🌐 Starting Mattermost Update Notifier Web Interface on port {WEB_PORT}')
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False)
