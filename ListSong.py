import os, requests, re, simplejson as json, Utils
from bs4 import BeautifulSoup
from flask import Blueprint

list_song = Blueprint('list_song', __name__)

URL_FORMAT = 'http://www.hymnal.net/en/song-categories/%s'

SONG_TYPE = 'song_type'
BUTTONS = 'buttons'

debug = False

def log(msg):
    if (debug):
        print msg

@list_song.route('/index_buttons/<song_type>')
def get_index_buttons(song_type):
    # data to be returned as jsonge
    json_data = {}
    
    # fill in song type
    json_data[SONG_TYPE] = song_type
    
    # make http GET request
    r = requests.get(URL_FORMAT % song_type)
    log('index buttons request sent for: %s' % song_type)
        
    # create BeautifulSoup object out of html content
    soup = BeautifulSoup(r.content)
    
    # extract index button div
    index_buttons = soup.find('div', {'class' : 'index-buttons'})
    log('index buttons found')
    
    # extract all links from the div
    links = Utils.extract_links(index_buttons)
    
    # add links to json_data to be returned
    json_data[BUTTONS] = links

    return json.dumps(json_data, sort_keys=False)