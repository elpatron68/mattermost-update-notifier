#!/bin/python3
import re
import sched, time
import time
import requests
import logging
import json
import os
from os.path import exists
from requests_html import HTMLSession
from packaging import version

try:
    INTERVAL = int(os.environ['CHECKINVERVAL']) 
except:
    INTERVAL = 1800

def readinstances():
    try:
        with open('./data/instances.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        logging.error('❌ Instances file not found: ./data/instances.json')
        return None
    except json.JSONDecodeError as e:
        logging.error(f'❌ Invalid JSON in instances file: {str(e)}')
        return None
    except PermissionError:
        logging.error('❌ Permission denied reading instances file: ./data/instances.json')
        return None
    except Exception as e:
        logging.error(f'❌ Unexpected error reading instances file: {str(e)}')
        return None
    
    if not data or not isinstance(data, list):
        logging.error('❌ Empty or malformatted instances file')
        return None
    
    # Validate instance structure
    for i, instance in enumerate(data):
        if not isinstance(instance, dict) or 'name' not in instance or 'api' not in instance or 'url' not in instance:
            logging.error(f'❌ Invalid instance structure at index {i}: missing required fields (name, api, url)')
            return None
    
    logging.debug('✅ Instances loaded.')
    return data

def getInstanceVersion(apiUrl, max_retries=3):
    version = None  # Initialize version variable
    
    # Validate input
    if not apiUrl or not isinstance(apiUrl, str):
        logging.warning(f'❌ Invalid API URL provided: {apiUrl}')
        return None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(apiUrl, timeout=30)
            response.raise_for_status()  # Raise exception for HTTP errors
            data = response.json()
            if 'Version' in data:
                version = data['Version']
                if attempt > 0:
                    logging.info(f'✅ Successfully retrieved version from {apiUrl} on attempt {attempt + 1}')
                break
            else:
                logging.warning(f'❌ Version field not found in API response from {apiUrl}')
                break
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logging.warning(f'⚠️ Attempt {attempt + 1} failed for {apiUrl}: {str(e)}, retrying...')
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logging.warning(f'❌ Failed to read instance version from api {apiUrl} after {max_retries} attempts: {str(e)}')
        except (ValueError, KeyError) as e:
            logging.warning(f'❌ Failed to parse API response from {apiUrl}: {str(e)}')
            break
        except Exception as e:
            logging.warning(f'❌ Unexpected error reading instance version from {apiUrl}: {str(e)}')
            break
    
    return version

def getLatestVersion(max_retries=3):
    downloadUrl = ""
    version = ""

    for attempt in range(max_retries):
        session = HTMLSession()
        try:
            r = session.get('https://releases.mattermost.com', timeout=30)
            r.raise_for_status()
            htmlPageText = r.text
            break
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logging.warning(f'⚠️ Attempt {attempt + 1} failed to get latest version from Mattermost website: {str(e)}, retrying...')
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logging.warning(f'❌ Failed to get latest version from Mattermost website after {max_retries} attempts: {str(e)}')
                return "", ""
        except Exception as e:
            logging.warning(f'❌ Unexpected error getting latest version: {str(e)}')
            return "", ""

    # https://releases.mattermost.com/10.9.0/mattermost-team-10.9.0-linux-amd64.tar.gz
    regex = r'https:\/\/releases\.mattermost\.com\/\d+\.\d+\.\d+\/mattermost-team-\d+\.\d+\.\d+-linux-amd64\.tar\.gz'

    try:
        downloadUrls = re.findall(regex, htmlPageText)
        if downloadUrls:
            downloadUrl = downloadUrls[0]
        else:
            logging.warning('⚠️ No download URLs found on Mattermost releases page.')
            return "", ""
    except Exception as e:
        logging.warning(f'⚠️ Failed parsing Mattermost download url: {str(e)}')
        return "", ""

    try:
        versions = re.findall(r'\d+\.\d+\.\d+', downloadUrl)
        if versions:
            version = versions[0]
        else:
            logging.warning('⚠️ No version found in download URL.')
            return "", ""
    except Exception as e:
        logging.warning(f'⚠️ Failed parsing Mattermost version information: {str(e)}')
        return "", ""
    
    logging.info('Latest Mattermost version from releases.mattermost.com: ' + version)
    return downloadUrl, version

def readLastversion(enum):
    # Alternativ: Versionsabfrage via API
    # https://forum.mattermost.com/t/how-to-get-mattermost-version-via-rest-api/15022
    filename = './data/lastnotifiedversion{enum}.txt'.format(enum = enum)
    try:
        with open(filename, 'r') as file:
            result = file.read().rstrip()
            return result
    except FileNotFoundError:
        logging.warning(f'⚠️ File not found: {filename}')
        return "0.0.0"
    except PermissionError:
        logging.warning(f'⚠️ Permission denied reading file: {filename}')
        return "0.0.0"
    except Exception as e:
        logging.warning(f'⚠️ Failed to read file {filename}: {str(e)}')
        return "0.0.0"

def writeLastversion(enum, version):
    filename = './data/lastnotifiedversion{enum}.txt'.format(enum = enum)
    try:
        with open(filename, 'w') as file:
            file.write(version)
        logging.debug(f'✅ Written version {version} to {filename}')
    except PermissionError:
        logging.error(f'❌ Permission denied writing file: {filename}')
    except OSError as e:
        logging.error(f'❌ OS error writing file {filename}: {str(e)}')
    except Exception as e:
        logging.error(f'❌ Failed to write file {filename}: {str(e)}')

def isNewer(latestVersion, lastVerion):
    try:
        return version.parse(latestVersion) > version.parse(lastVerion)
    except Exception as e:
        logging.warning(f'⚠️ Failed to compare versions "{latestVersion}" and "{lastVerion}": {str(e)}')
        return False

def sendMM(url, text):
    # Validate input
    if not url or not isinstance(url, str):
        logging.warning(f'❌ Invalid URL provided for notification: {url}')
        return None
    if not text or not isinstance(text, str):
        logging.warning(f'❌ Invalid text provided for notification: {text}')
        return None
    
    headers = {'Content-Type': 'application/json',}
    # Escape special characters in text to prevent JSON injection
    escaped_text = text.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
    values = '{ "text": "' + escaped_text + '"}'
    try:
        response = requests.post(url, headers=headers, data=values, timeout=30)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.RequestException as e:
        logging.warning(f"⚠️ Failed to send Mattermost notification to {url}: {str(e)}")
        return None
    except Exception as e:
        logging.warning(f"⚠️ Unexpected error sending notification to {url}: {str(e)}")
        return None
    
def timer_thread():
    index = 0
    successful_checks = 0
    failed_checks = 0
    
    logging.info('Parsing Mattermost website for latest version and download link.')
    url, ver = getLatestVersion()
    
    if not ver or not url:
        logging.error('❌ Failed to get latest Mattermost version, skipping this check cycle.')
        return
    
    logging.info('Reading instances from configuration file.')
    instances = readinstances()
    
    if not instances:
        logging.error('❌ No valid instances found, skipping this check cycle.')
        return
    
    logging.info(f'📋 Found {len(instances)} instances to check')
    
    for instance in instances:
        index += 1
        
        logging.info(f'🔍 Checking instance {index}/{len(instances)}: {instance["name"]}')
        installedVersion = getInstanceVersion(instance['api'])
        
        if not installedVersion:
            logging.warning(f'⚠️ Could not determine version for instance {instance["name"]}, skipping.')
            failed_checks += 1
            continue
        
        successful_checks += 1
        logging.info(f'✅ Instance {instance["name"]} version: {installedVersion}')
        
        # Create new file if not exists
        if not exists('./data/lastnotifiedversion' + str(index) + '.txt'):
            writeLastversion(str(index), '0.0.0')

        if isNewer(ver, installedVersion):
            logging.info('🆕 New Mattermost version found, information updated:')
            logging.info(f'📊 Former version: {installedVersion}')
            logging.info(f'📊 Latest version: {ver}')
            logging.info(f'📊 Download URL: {url}')
            notifiedversion = readLastversion(str(index))
            logging.info(f'📊 Last version notified about: {notifiedversion}')
            if isNewer(ver, notifiedversion):
                text = f'New Mattermost version found!\nLatest version: {ver}\nFormer version: {installedVersion}\nDownload URL: {url}\n[Release notes](https://docs.mattermost.com/about/mattermost-v10-changelog.html)\n'
                result = sendMM(url=instance['url'], text=text)
                if result:
                    writeLastversion(str(index), ver)
                    logging.info(f'📤 Message sent successfully: HTTP {result}')
                else:
                    logging.warning('⚠️ Failed to send notification, not updating notified version.')
            else:
                logging.info('ℹ️ Update available, but user has been notified already.')
        else:
            logging.info('✅ Nothing to do (instance is up-to-date).')
    
    logging.info(f'📈 Check cycle completed: {successful_checks} successful, {failed_checks} failed')
    logging.info(f'💤 Sleeping for {round(INTERVAL/60)} minutes...')
    return

def CheckForUpdate(scheduler): 
    # schedule the next call first
    scheduler.enter(INTERVAL, 1, CheckForUpdate, (scheduler,))
    logging.info("Scheduler: Starting update check...")
    try:
        timer_thread()
    except Exception as e:
        logging.error(f"❌ Unexpected error in update check cycle: {str(e)}")
        logging.info("Continuing with next scheduled check...")

if __name__ == "__main__":
    # Configure logging with more detailed format
    logging.basicConfig(
        format = '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        level = logging.INFO,
        datefmt = '%Y-%m-%d %H:%M:%S')
    
    logging.info('🚀 Starting Mattermost update checker')
    logging.info(f'📊 Check interval: {INTERVAL} seconds ({INTERVAL/60:.1f} minutes)')
    
    # Log environment information
    try:
        import sys
        logging.info(f'🐍 Python version: {sys.version}')
        logging.info(f'📁 Working directory: {os.getcwd()}')
    except Exception as e:
        logging.warning(f'⚠️ Could not log environment info: {str(e)}')
    
    # Validate data directory exists
    if not os.path.exists('./data'):
        logging.error('❌ Data directory ./data does not exist!')
        exit(1)
    
    if not os.path.exists('./data/instances.json'):
        logging.error('❌ Instances configuration file ./data/instances.json does not exist!')
        exit(1)
    
    my_scheduler = sched.scheduler(time.time, time.sleep)
    logging.info('⏰ Scheduler initialized, starting first check in 10 seconds...')
    my_scheduler.enter(10, 1, CheckForUpdate, (my_scheduler,))
    
    try:
        my_scheduler.run()
    except KeyboardInterrupt:
        logging.info('🛑 Received interrupt signal, shutting down gracefully...')
    except Exception as e:
        logging.error(f'❌ Fatal error in scheduler: {str(e)}')
        exit(1)