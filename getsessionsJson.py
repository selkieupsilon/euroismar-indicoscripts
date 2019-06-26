# Script to obtain JSON of sessions for the typesetters to put into the program pages

import json

import hashlib
import hmac
import urllib
import time
import requests
from ConfigParser import SafeConfigParser as ConfigParser

from datetime import datetime as dt

import argparse

from collections import OrderedDict

def jsonGet(jsonFile):
    try:
        with open (jsonFile,"r") as read_file:
            jsonData = json.load(read_file)
        return jsonData

    except:
        signedUrl = signedSessionsUrl()
        print signedUrl

        print ("requesting JSON")
        response = requests.get(signedUrl)
        rawdata = json.loads(response.text)

        print ("tidy up JSON")
        sessionsdata = rawdata.get('results')[0].get('sessions')

        outputJsonFile(sessionsdata, filename=jsonFile, timestamp=False)

        return sessionsdata

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

def signedSessionsUrl():
    config = ConfigParser()
    config.read('config.ini')
    API_KEY = config.get('default','API_KEY')
    SECRET_KEY = config.get('default','SECRET_KEY')
    PATH = config.get('default','PATH')
    PREFIX = config.get('default','PREFIX')
    PARAMS = {
        'pretty': 'yes',
        'detail': 'sessions'
    }

    return PREFIX+build_indico_request(PATH, PARAMS, API_KEY, SECRET_KEY)

def outputJsonFile(data,fileprefix=None, filesuffix="all", timestamp=True, filename=None):
    if not filename:
        if not fileprefix:
            fileprefix = "sessions-"
        filename = fileprefix + filesuffix

        if timestamp:
            now = dt.now()
            timestamp = now.strftime("%Y%m%d-%H%M")
            filename = filename + "_" + timestamp
            
        filename += ".json"
    print ("writing "+filename)

    with open (filename,"w") as write_file:
         json.dump(data, write_file)


def sortByStartTime(talks): # works also for sessions
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

def sortByRoomTime(paralleltalks): # works also for sessions
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
        "": 5
    }

    paralleltalks.sort(key=lambda t: sortRoomOrder[str(t['room'])])
    paralleltalks = sortByStartTime(paralleltalks)
    return paralleltalks

# def TTtextoutput(x):
#     textList = []
#     textList.append(x["startDate"]["date"]+" "+x["startDate"]["time"]+" - "+x["endDate"]["time"])
#     textList.append(x["room"])
#     textList.append(x["session"])

#     try:
#         textList.append(x["speakers"][0]["first_name"]+" "+x["speakers"][0]["last_name"])
#     except:
#         textList.append("no speaker")
#         pass
#     textList.append(x["title"])
#     return textList

def parseDateTime(item, timepoint):
    # item - structured JSON data containing startDate, endDate
    # timepoint - str, for Indico JSON export: starDate or endDate
    dtDict = item.get(timepoint)
    dtStr = dtDict["date"] + " " + dtDict["time"]
    return dtStr[:-3]  # strip seconds

def parseTime(item, timepoint):
    # item - structured JSON data containing startDate, endDate
    # timepoint - str, for Indico JSON export: starDate or endDate
    dtDict = item.get(timepoint)
    dtStr = dtDict["time"]
    return dtStr[:-3]  # strip seconds

def processTitle(title):
    sep = ":"
    titleNoSessionNum = title.rsplit(sep,1)[0]
    return str(titleNoSessionNum)

def prettyStartEnd(data, start, end):
    return parseDateTime(data, start) + "-" + parseTime(data, end)

def getInitials(name):
    initials = ''.join([x[0].upper()+'.' for x in name.split(' ')])
    initials = initials+' '
    return initials


def parseSession(data):
    parsedData = OrderedDict({})

    #print processTitle(data["title"]) 
    parsedData["session-title"] = processTitle(data["title"])
    parsedData["session-time"] = prettyStartEnd(data, "startDate", "endDate")
    parsedData["room"] = data["room"]

    parsedContribs = []
    contribsUnsorted = data["contributions"]
    contribs = sortByStartTime(contribsUnsorted)
    
    for talk in contribs:
        parsedTalk = OrderedDict({})
        if data["session"]["type"] != u"Plenary lecture":
            try: 
                speaker = talk["speakers"][0]
                parsedTalk["speaker"] = getInitials(speaker["first_name"])+speaker["last_name"]
            except:
                # posters
                pass
        else:
            try: 
                speaker = talk["speakers"][0]
                parsedTalk["speaker"] = speaker["first_name"]+' '+speaker["last_name"]
            except:
                # prizes to be announced
                pass

        parsedTalk["title"] = talk["title"]
        
        parsedTalk["time"] = prettyStartEnd(talk, "startDate", "endDate")

        parsedContribs.append(parsedTalk)
        
    parsedData["talks"] = parsedContribs
    return parsedData


if __name__ == '__main__':
    data = jsonGet("session-all.json")

    sorteddata = sortByRoomTime(data)  # sessions are sorted, but talks within a session aren't

    simplifiedSessions = []

    for session in sorteddata:
        simpleSession = parseSession(session)
        simplifiedSessions.append(simpleSession)

    parser = argparse.ArgumentParser(description = "Gets sessions from one event using HTTP API, then sort into JSON files for typesetting. See github: selkieupsilon/euroismar-indicoscripts")
    parser.add_argument('--timestamp', action='store_true', help='add timestamp to output files')
    args = parser.parse_args()

    #outputJsonFile(sorteddata, fileprefix="sessionSorted_", timestamp=args.timestamp)
    outputJsonFile(simplifiedSessions, fileprefix="sessionSimple_", timestamp=args.timestamp)

    print ("done")