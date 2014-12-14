import os, requests, simplejson as json, Utils, Constants
from bs4 import BeautifulSoup
from flask import Blueprint, request

list_song = Blueprint('list_song', __name__)

URL_FORMAT = 'http://www.hymnal.net/%s'
SONG_INDEX_PATH_FORMAT = 'en/song-index/%s'
SONG_INDEX_LETTER_PATH_FORMAT = 'en/song-index/%s/%s'
SCRIPTURE_PATH_FORMAT = 'en/scripture-songs/%s'
SONG_CATEGORIES_PATH_FORMAT = 'en/song-categories/%s'

# error message constants
SONG_TYPE = 'song_type'
SEARCH_LETTER = 'letter'
EMPTY_RESULT_ERROR_MESSAGE = 'Unfortunately, there are no songs in this category. Please try again.'

# constants for get_list_scripture
TESTAMENT = 'testament'
BOOK_NAME = 'book_name'
LINK = 'link'
VERSE_REF = 'verse_ref'
SONGS = 'songs'
BOOK_CONTENT = 'book_contents'
BOOKS = 'books'

# Constants for get_index_buttons
BUTTONS = 'buttons'

debug = False

def log(msg):
    if (debug):
        print msg

@list_song.route('/list')
# args: song_type, letter, testament
def get_list():
    
    # initialize arguments
    song_type = request.args.get('song_type', type=str)
    letter = request.args.get('letter', type=str)
    testament = request.args.get('testament', type=str)
    
    # make song_type lower case if it isn't None
    if song_type is not None:
        song_type = song_type.lower()
    
    # error checking
    message = None
    if song_type is None:
        message = {Constants.PUBLIC : Constants.ERROR_MESSAGE % SONG_TYPE}
    elif (song_type == 'h' or song_type =='ns') and letter is None:
        message = {Constants.PUBLIC : Constants.ERROR_MESSAGE % SEARCH_LETTER}
    elif song_type == 'scripture' and testament is None:
        message = {Constants.PUBLIC: Constants.ERROR_MESSAGE % TESTAMENT}

    # if message is not None, then return 400 with the message
    if message is not None:
        message['status_code'] = 400
        return (json.dumps(message), 400)
    
    # if song_type is scripture, we have to handle it a little bit differently
    if (song_type == 'scripture'):
        return get_list_scripture(testament)
    
    # data to be returned as json
    json_data = {}

    if song_type == 'nt' or song_type == 'c':
        # New Tunes and Children's songs aren't listed by letter, so create path without the letter
        path = SONG_INDEX_PATH_FORMAT % song_type
    else:
        # make letter uppercase if it isn't already
        letter = letter.upper()
        
        # create url
        path = SONG_INDEX_LETTER_PATH_FORMAT % (song_type, letter)


    # make http GET request
    r = requests.get(URL_FORMAT % path)
    log('index buttons request sent for: %s' % path)

    # create BeautifulSoup object out of html content
    soup = BeautifulSoup(r.content)

    # extract results
    results = Utils.extract_results_single_page(soup)

    if len(results) == 0:
        json_data[Constants.EMPTY_LIST_MESSAGE] = EMPTY_RESULT_ERROR_MESSAGE
    json_data[Constants.RESULTS] = results

    return json.dumps(json_data, sort_keys=False)

def get_list_scripture(testament):
    # make testament lower case if it isn't already
    testament = testament.lower()
    
    # data to be returned as json
    json_data = {}
    
    # hymnal.net path to list of scripture songs
    path = SCRIPTURE_PATH_FORMAT % testament

    # make http GET request
    r = requests.get(URL_FORMAT % path)
    log('index buttons request sent for: %s' % path)

    # create BeautifulSoup object out of html content
    soup = BeautifulSoup(r.content)

    # find all div's with class 'panel-default,' which is the div containing the bible book name
    book_divs = soup.findAll('div', {'class': 'panel-default'})
    
    # list of bible books with songs about them
    books = []
    
    for book_div in book_divs:
        # book object with attributes book_name and book_content
        book = {}
        
        # name of the book
        book[BOOK_NAME] = book_div.text.strip()

        # list of chapters each containing songs from that chapter
        book_content = []

        # initialize next_div to increment in the loop
        next_div = book_div

        # loop will break when there are no more siblings with verse references
        while True:
            
            # increment to next sibling
            next_div = next_div.next_sibling
            
            try:
                # find div with the verse reference
                verse_ref_div = next_div.find('div',{'class' : 'verse-ref'})
                
                # extract name and link of verse reference
                verse_ref = Utils.extract_links(verse_ref_div, path_key = LINK, should_clear_children = False)[0]
                
                # div of the songs that are from that verse reference
                songs_div = verse_ref_div.next_sibling
                
                # if songs_div is a space or new line, skip and go to next sibling
                if len(str(songs_div).strip()) == 0:
                    songs_div = songs_div.next_sibling
                
                # extract song name and path
                songs = Utils.extract_links(songs_div)

                # chapter dictionary with attributes verse_reference and a list of songs from that verse reference
                chapter = {}
                chapter[VERSE_REF] = verse_ref
                chapter[SONGS] = songs
                book_content.append(chapter)
            except TypeError:
                # indicates that the div was just a space or new line, so skip
                continue
            except AttributeError:
                # indicates that there are no more siblings with verse references, so break out of loop
                break

        book[BOOK_CONTENT] = book_content
        books.append(book)
    
    json_data[BOOKS] = books
    
    return json.dumps(json_data, sort_keys=False)

@list_song.route('/list/index_buttons/<song_type>')
def get_index_buttons(song_type):
    # data to be returned as json
    json_data = {}
    
    # create path
    path = SONG_CATEGORIES_PATH_FORMAT % song_type
    
    # make http GET request
    r = requests.get(URL_FORMAT % path)
    log('index buttons request sent for: %s' % path)
        
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

# test paths: list/nt/2, list/nt/5, list/h/b/2, list/h/b/3, list/h/b/4, list/scripture/nt, list/index_buttons/h