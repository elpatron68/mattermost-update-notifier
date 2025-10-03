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
from flask_babel import Babel, gettext as _, ngettext, lazy_gettext
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

# Internationalization Configuration
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
    if language in app.config['LANGUAGES']:
        session['language'] = language
        flash(_('Language changed to %(lang)s', lang=app.config['LANGUAGES'][language]), 'success')
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

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('./data', exist_ok=True)
    
    logging.info(f'🌐 Starting Mattermost Update Notifier Web Interface on port {WEB_PORT}')
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False)
