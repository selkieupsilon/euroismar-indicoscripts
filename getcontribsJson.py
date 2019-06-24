# Script to obtain JSON of contributions for the typesetters

import hashlib
import hmac
import urllib
import time

import json
import requests

from ConfigParser import SafeConfigParser as ConfigParser

from datetime import datetime as dt

config = ConfigParser()
config.read('config.ini')

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

if __name__ == '__main__':
    API_KEY = config.get('default','API_KEY')
    SECRET_KEY = config.get('default','SECRET_KEY')
    PATH = config.get('default','PATH')
    PREFIX = config.get('default','PREFIX')
    PARAMS = {
        'pretty': 'yes',
        'detail': 'contributions'
    }

signedurl = PREFIX+build_indico_request(PATH, PARAMS, API_KEY, SECRET_KEY)

print ("requesting JSON")
response = requests.get(signedurl)

print ("loading JSON")
data = json.loads(response.text)

#with open ("raw_contrib-http-export.json","r") as read_file:
#    data = json.load(read_file)

contribs = data.get('results')[0].get('contributions')

print ("tidy up JSON")
now = dt.now()
timestamp = now.strftime("%Y%m%d-%H%M")

with open("clean_contrib_"+timestamp+".json", "w") as write_file:
    json.dump(contribs, write_file)

print ("done")