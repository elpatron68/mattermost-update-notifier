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

def getInstanceVersion(apiUrl):
    try:
        response = requests.get(apiUrl)
        data = response.json()
        version = data['Version']
    except:
        logging.warning('❌ Failed to read instance version from api.')
    return version

def getLatestVersion():
    downloadUrl = ""

    session = HTMLSession()
    try:
        r = session.get('https://docs.mattermost.com/deploy/server/linux/deploy-tar.html')
        htmlPageText=r.text
    except:
        logging.warning('❌ Failed to get latest version from Mattermost website')
        pass

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
    filename = './data/lastnotifiedversion{enum}.txt'.format(enum = enum)
    try:
        with open(filename, 'r') as file:
            result = file.read().rstrip()
    except:
        logging.warning('⚠️ Failed to read file: ' + filename)
    return result

def writeLastversion(enum, version):
    filename = './data/lastnotifiedversion{enum}.txt'.format(enum = enum)
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
    try:
        response = requests.post(url, headers=headers, data=values)
    except:
        logging.warning("⚠️ Failed to send Mattermost notification.")
    return response.status_code
    
def timer_thread():
    index = 0
    logging.info('Parsing Mattermost website for latest version and download link.')
    url, ver = getLatestVersion()
    if not ver == '' or url == '':
        logging.info('Reading instances from configuration file.')
        instances = readinstances()
        
        for instance in instances:
            index += 1
            
            logging.info('Checking instance: ' + instance['name'])
            installedVersion = getInstanceVersion(instance['api'])
            logging.info('Installed Mattermost version: ' + installedVersion)
            
            # Create new file if not exists
            if not exists('./data/lastnotifiedversion' + str(index) + '.txt'):
                writeLastversion(str(index), '0.0.0')

            if (isNewer(ver, installedVersion)):
                logging.info('New Mattermost version found, information updated:')
                logging.info('Former version: ' + installedVersion)
                logging.info('Latest version: ' + ver)
                logging.info('Download URL:   ' + url)
                notifiedversion = readLastversion(str(index))
                logging.info('Last version notified about: ' + installedVersion)
                if isNewer(ver, notifiedversion):
                    text = 'New Mattermost version found!\nLatest version: ' + ver + '\nFormer version: ' + installedVersion + '\nDownload URL: ' + url + '\n[Release notes](https://docs.mattermost.com/install/self-managed-changelog.html)\n'
                    result = sendMM(url=instance['url'], text=text)
                    writeLastversion(str(index), ver)
                    logging.info('Message sent: ' + str(result))
                else:
                    logging.info('Update available, but user has been notified, yet.')
            else:
                logging.info('Nothing to do (instance is up-to-date).')
        logging.info('Sleeping for ' + str(round(INTERVAL/60)) + ' minutes...')
        return

def CheckForUpdate(scheduler): 
    # schedule the next call first
    scheduler.enter(INTERVAL, 1, CheckForUpdate, (scheduler,))
    logging.info("Scheduler: Starting update check...")
    timer_thread()

if __name__ == "__main__":
    logging.basicConfig(
        format = '%(asctime)s %(levelname)-8s %(message)s',
        level = logging.INFO,
        datefmt = '%Y-%m-%d %H:%M:%S')
    logging.info('Starting Mattermost update checker')
    if not INTERVAL:
        INTERVAL = 3600
    logging.info('Set check interval to ' + str(INTERVAL) + ' seconds')
    my_scheduler = sched.scheduler(time.time, time.sleep)
    my_scheduler.enter(10, 1, CheckForUpdate, (my_scheduler,))
    my_scheduler.run()