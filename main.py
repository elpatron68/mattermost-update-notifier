#!/bin/python3
import re
# from urllib import response
import requests
from os.path import exists
from requests_html import HTMLSession
from packaging import version

class INSTANCE():
    def __init__(self, name, url, channel, lfdnr):
        self.name = name
        self.url = url
        self.channel = channel

INSTANCES = []
INSTANCES.append(INSTANCE('medisoft', 'https://mattermost.medisoftware.org/hooks/t9yywpo8db8pdrog9xrigayyuh', ''))
INSTANCES.append(INSTANCE('joerg', 'https://s16.jl.sb/hooks/ijdhxb3ertbhtc1qr6ak9tzojr',''))

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
        pass

    try:
        version = re.findall(r'\d+\.\d+\.\d+', downloadUrl)[0]
    except:
        pass

    return downloadUrl, version

def readLastversion(enum):
    filename = 'lastversion{enum}.txt'.format(enum = enum)
    with open(filename, 'r') as file:
        result = file.read().rstrip()
    return result

def writeLastversion(enum, version):
    filename = 'lastversion{enum}.txt'.format(enum = enum)
    with open(filename, 'w') as file:
        file.write(version)

def isNewer(latestVersion, lastVerion):
    return version.parse(latestVersion) > version.parse(lastVerion)

def sendMM(url, text):
    headers = {'Content-Type': 'application/json',}
    # values = '{ "channel": "' + CHANNEL + '", "text": "' + text + '"}'
    values = '{ "text": "' + text + '"}'
    response = requests.post(url, headers=headers, data=values)
    return response.status_code

if __name__ == "__main__":
    index = 0
    for instance in INSTANCES:
        index += 1
        print('Checking instance: ' + instance.name)
        if not exists('lastversion' + str(index) + '.txt'):
            writeLastversion(str(index), '0.0.0')

        url, ver = getLatestVersion()
        installedversion = readLastversion(str(index))
        if (isNewer(ver, installedversion)):
            writeLastversion(str(index), ver)
            print('New Mattermost version found, information updated:')
            print('Former version: ' + installedversion)
            print('Latest version: ' + ver)
            print('Download URL:   ' + url)
            text = 'New Mattermost version found!\nLatest version: ' + ver + '\nFormer version: ' + installedversion + '\nDownload URL: ' + url + '\n[Release notes](https://docs.mattermost.com/install/self-managed-changelog.html)\n'
            result = sendMM(url=instance.url, text=text)
            print('Message sent: ' + str(result))
            print()
        else:
            print('Nothing to do (instance is up-to-date).')