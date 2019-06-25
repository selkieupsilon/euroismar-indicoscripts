# Script to obtain JSON of contributions for the typesetters

import json

import hashlib
import hmac
import urllib
import time
import requests
from ConfigParser import SafeConfigParser as ConfigParser

from datetime import datetime as dt

import argparse

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

def outputJsonFile(data,fileprefix=None, filesuffix="all", timestamp=True, filename=None):
    if not filename:
        if not fileprefix:
            fileprefix = "clean_contrib-"
        filename = fileprefix + filesuffix

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
    #     try:
    #         # check posters have board_numbers
    #     except:
    #         # complain if there are posters without board numbers
    #     print (poster.get('board_number'))

    posters.sort(key=lambda k: int(k['board_number']))
    return posters

def sortByStartTime(talks):
    for talk in talks:
        try:
            starttimeDict = talk.get("startDate")
            starttimeStr = starttimeDict["date"] + " " + starttimeDict["time"]
        except:
            print ("Warning: unscheduled talk in exported JSON list.")
            return
        #print (starttimeStr)

    talks.sort(key=lambda t: dt.strptime(t['startDate']['date']+' '+t['startDate']['time'],"%Y-%m-%d %H:%M:%S"))
    return talks

# def checkRoomStartTime(paralleltalks):
#     for talk in paralleltalks:
#         try:
#             room = talk.get("room")
#             starttimeDict = talk.get("startDate")
#             starttimeStr = starttimeDict["date"] + " " + starttimeDict["time"]
#         except:
#             print ("Warning: something wrong.")
#             return
#         print (room, starttimeStr)

def sortByRoomTime(paralleltalks):
    for talk in paralleltalks:
        try:
            room = talk.get("room")
        except:
            print ("Warning: talk without assigned room in exported JSON list.")
            return
        #print (room)

    sortRoomOrder = {
        "Max Kade Auditorium": 0,
        "Lecture Hall A": 1,
        "Lecture Hall B": 2,
        "Lecture Hall C": 3,
        "Lecture Hall D": 4,
    }

    paralleltalks.sort(key=lambda t: sortRoomOrder[str(t['room'])])
    paralleltalks = sortByStartTime(paralleltalks)
    return paralleltalks

def TTtextoutput(x):
    textList = []
    textList.append(x["startDate"]["date"]+" "+x["startDate"]["time"]+" - "+x["endDate"]["time"])
    textList.append(x["room"])
    textList.append(x["session"])

    try:
        textList.append(x["speakers"][0]["first_name"]+" "+x["speakers"][0]["last_name"])
    except:
        textList.append("no speaker")
        pass
    textList.append(x["title"])
    return textList

if __name__ == '__main__':
    data = jsonGet("contrib-all.json")

    posterList = []
    paralleltalkList = []
    plenaryList = []
    prizeList = []
    introList = []

    #prizeList, plenaryList, paralleltalkList, posterList
    #this division drops any "contributions" that are outside these categories

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
        if contribType == 'Introduction':
            introList.append(contrib)

    contribsDict = {
        "prize-PR": sortByStartTime(prizeList),
        "plenary-PL": sortByStartTime(plenaryList),
        "parallelsessions-PS": sortByRoomTime(paralleltalkList),
        "posters": sortByBoardNum(posterList)
    }

    parser = argparse.ArgumentParser(description = "Gets contributions from one event using HTTP API, then sort into JSON files for typesetting. See github: selkieupsilon/euroismar-indicoscripts")
    parser.add_argument('--timestamp', action='store_true', help='add timestamp to output files')
    args = parser.parse_args()

    for key in contribsDict :
        outputJsonFile(contribsDict[key],fileprefix="abstract_", filesuffix=key, timestamp=args.timestamp)

    timetable = sortByRoomTime(prizeList + plenaryList + paralleltalkList + introList)

    #outputJsonFile(timetable, fileprefix="timetable_", timestamp=args.timestamp)

    TTtalkList = [] 
    for talk in timetable:
        TTtalkList.append(TTtextoutput(talk))
    outputJsonFile(TTtalkList, fileprefix="timetable_titles_", timestamp=args.timestamp)

    print ("done")