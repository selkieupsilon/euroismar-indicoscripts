# Script to obtain JSON of contributions for the typesetters

import json

import hashlib
import hmac
import urllib
import time
import requests
from ConfigParser import SafeConfigParser as ConfigParser

from datetime import datetime as dt

def jsonGet(jsonFile):
    try:
        with open (jsonFile,"r") as read_file:
            jsonData = json.load(read_file)
        return jsonData

    except:
        signedUrl = signedContribsUrl()

        print ("requesting JSON")
        response = requests.get(signedUrl)
        rawdata = json.loads(response.text)

        print ("tidy up JSON")
        contribsdata = rawdata.get('results')[0].get('contributions')

        outputJsonFile(contribsdata, filename=jsonFile, timestamp=False)

        return contribsdata

def build_indico_request(path, params, api_key=None, secret_key=None, only_public=False, persistent=False):
    items = params.items() if hasattr(params, 'items') else list(params)
    if api_key:
        items.append(('apikey', api_key))
    if only_public:
        items.append(('onlypublic', 'yes'))
    if secret_key:
        if not persistent:
            items.append(('timestamp', str(int(time.time()))))
        items = sorted(items, key=lambda x: x[0].lower())
        url = '%s?%s' % (path, urllib.urlencode(items))
        signature = hmac.new(secret_key, url, hashlib.sha1).hexdigest()
        items.append(('signature', signature))
    if not items:
        return path
    return '%s?%s' % (path, urllib.urlencode(items))

def signedContribsUrl():
    config = ConfigParser()
    config.read('config.ini')
    API_KEY = config.get('default','API_KEY')
    SECRET_KEY = config.get('default','SECRET_KEY')
    PATH = config.get('default','PATH')
    PREFIX = config.get('default','PREFIX')
    PARAMS = {
        'pretty': 'yes',
        'detail': 'contributions'
    }

    return PREFIX+build_indico_request(PATH, PARAMS, API_KEY, SECRET_KEY)

def outputJsonFile(data, filesuffix="all", timestamp=True, filename=None):
    if not filename:
        filename = "clean_contrib-" + filesuffix

        if timestamp:
            now = dt.now()
            timestamp = now.strftime("%Y%m%d-%H%M")
            filename = filename + "_" + timestamp
            
        filename += ".json"
    print ("writing "+filename)

    with open (filename,"w") as write_file:
         json.dump(data, write_file)


def sortByBoardNum(posters):

    # for poster in posters:
    #     print poster.get('board_number')

    posters.sort(key=lambda k: int(k['board_number']))
    return posters



if __name__ == '__main__':
    data = jsonGet("clean_contrib-all.json")

    posterList = []
    paralleltalkList = []
    plenaryList = []
    prizeList = []

    #prizeList, plenaryList, paralleltalkList, posterList

    for contrib in data :
        contribType = contrib.get('type')
        if contribType == 'Poster':
            posterList.append(contrib)
        if contribType == 'Talk' or contribType == 'Invited talk':
            paralleltalkList.append(contrib)
        if contribType == 'Plenary talk':
            plenaryList.append(contrib)
        if contribType == 'Prize lecture':
            prizeList.append(contrib)

    contribsDict = {
        "prizes": prizeList,
        "plenarys": plenaryList,
        "paralleltalks": paralleltalkList,
        "posters": sortByBoardNum(posterList)
    }

    for key in contribsDict :
        outputJsonFile(contribsDict[key],filesuffix=key, timestamp=False)


    print ("done")