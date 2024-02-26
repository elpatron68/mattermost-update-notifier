#!/bin/python3
import re
import threading
import time
import requests
import logging
import json
from os.path import exists
from requests_html import HTMLSession
from packaging import version

def readinstances():
    try:
        f = open('./data/instances.json')
    except:
        logging.warning('❌ Failed to read instances from file: ./data/instances.json')
        exit(1)
    data = json.load(f)
    if data:
        logging.debug('✅ Instances loaded.')
    else:
        logging.warning('❌ Empty or malformatted instances file: ./data/instances.json')
        exit(1)
    return data

def getLatestVersion():
    downloadUrl = ""

    session = HTMLSession()
    r = session.get('https://docs.mattermost.com/install/install-tar.html')
    htmlPageText=r.text

    # https://releases.mattermost.com/7.10.0/mattermost-7.10.0-linux-amd64.tar.gz
    regex = r'https:\/\/releases\.mattermost\.com\/\d+\.\d+\.\d+\/mattermost-\d+\.\d+\.\d+-linux-amd64\.tar\.gz'
    downloadUrl = ''
    version = ''

    try:
        downloadUrl = re.findall(regex, htmlPageText)[0]
    except:
        logging.warning('⚠️ Failed parsing Mattermost download url.')
        pass

    try:
        version = re.findall(r'\d+\.\d+\.\d+', downloadUrl)[0]
    except:
        logging.warning('⚠️ Failed parsing Mattermost version information.')
        pass
    logging.info('Latest Mattermost version from releases.mattermost.com: ' + version)
    return downloadUrl, version

def readLastversion(enum):
    # Alternativ: Versionsabfrage via API
    # https://forum.mattermost.com/t/how-to-get-mattermost-version-via-rest-api/15022
    filename = './data/lastversion{enum}.txt'.format(enum = enum)
    try:
        with open(filename, 'r') as file:
            result = file.read().rstrip()
    except:
        logging.warning('⚠️ Failed to read file: ' + filename)
    return result

def writeLastversion(enum, version):
    filename = './data/lastversion{enum}.txt'.format(enum = enum)
    try:
        with open(filename, 'w') as file:
            file.write(version)
    except:
        logging.warning('⚠️ Failed to write file: ' + filename)

def isNewer(latestVersion, lastVerion):
    return version.parse(latestVersion) > version.parse(lastVerion)

def sendMM(url, text):
    headers = {'Content-Type': 'application/json',}
    # values = '{ "channel": "' + CHANNEL + '", "text": "' + text + '"}'
    values = '{ "text": "' + text + '"}'
    response = requests.post(url, headers=headers, data=values)
    return response.status_code

def main():
    thread = threading.Thread(target=timer_thread)
    thread.start()
    
def timer_thread():
    index = 0
    logging.info('Parsing Mattermost website for latest version and download link.')
    url, ver = getLatestVersion()
    logging.info('Reading instances from configuration file.')
    instances = readinstances()
    
    for instance in instances:
        index += 1
        logging.info('Checking instance: ' + instance['name'])
        
        # Create new file if not exists
        if not exists('./data/lastversion' + str(index) + '.txt'):
            writeLastversion(str(index), '0.0.0')

        installedversion = readLastversion(str(index))
        logging.info('Last version notified: ' + installedversion)
        if (isNewer(ver, installedversion)):
            writeLastversion(str(index), ver)
            logging.info('New Mattermost version found, information updated:')
            logging.info('Former version: ' + installedversion)
            logging.info('Latest version: ' + ver)
            logging.info('Download URL:   ' + url)
            text = 'New Mattermost version found!\nLatest version: ' + ver + '\nFormer version: ' + installedversion + '\nDownload URL: ' + url + '\n[Release notes](https://docs.mattermost.com/install/self-managed-changelog.html)\n'
            result = sendMM(url=instance['url'], text=text)
            logging.info('Message sent: ' + str(result))
        else:
            logging.info('Nothing to do (instance is up-to-date).')
    logging.info('Sleeping for 1 hour...')
    time.sleep(3600) # Warte 1 Stunde

if __name__ == "__main__":       
    logging.basicConfig(
        format = '%(asctime)s %(levelname)-8s %(message)s',
        level = logging.INFO,
        datefmt = '%Y-%m-%d %H:%M:%S')
    logging.info('Starting Mattermost update checker')
    main()