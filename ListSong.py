import os, requests, simplejson as json, Utils, SearchSong
from bs4 import BeautifulSoup
from flask import Blueprint

list_song = Blueprint('list_song', __name__)

URL_FORMAT = 'http://www.hymnal.net/%s'
SONG_INDEX_PATH_FORMAT = 'en/song-index/%s/%d'
SONG_INDEX_LETTER_PATH_FORMAT = 'en/song-index/%s/%s/%d'
SCRIPTURE_PATH_FORMAT = 'en/scripture-songs/%s'
SONG_CATEGORIES_PATH_FORMAT = 'en/song-categories/%s'
SONG_TYPE = 'song_type'

# constants for get_list
SEARCH_LETTER = 'letter'
LETTERS = 'letters'
RESULTS = 'results'
IS_LAST_PAGE = 'is_last_page'

# constants for get_list_scripture
TESTAMENT = 'testament'
BOOK_NAME = 'book_name'
LINK = 'link'
VERSE_REF = 'verse_ref'
SONGS = 'songs'
BOOK_CONTENT = 'book_content'
BOOK = 'book'

# Constants for get_index_buttons
BUTTONS = 'buttons'

debug = False

def log(msg):
    if (debug):
        print msg

# extract a list of letters that are in this soup
def extract_letters_list(soup):
    # finds div element with class as 'letters'
    letters_div = soup.find('div',{'class':'letters'})
    if letters_div is None:
        return None
    else:
        return Utils.extract_links(letters_div)

@list_song.route('/list/<song_type>/<int:page_num>')
def get_list_no_letter(song_type, page_num):
    return get_list(song_type, None, page_num)

@list_song.route('/list/<song_type>/<letter>/<int:page_num>')
def get_list(song_type, letter, page_num):
    
    # data to be returned as json
    json_data = {}
    
    # fill in song type
    json_data[SONG_TYPE] = song_type
    
    if letter is None:
        # create path
        path = SONG_INDEX_PATH_FORMAT % (song_type, page_num)
    else:
        # make letter uppercase if it isn't already
        letter = letter.upper()
        
        # create url
        path = SONG_INDEX_LETTER_PATH_FORMAT % (song_type, letter, page_num)
        
        # fill in song letter
        json_data[SEARCH_LETTER] = letter


    # make http GET request
    r = requests.get(URL_FORMAT % path)
    log('index buttons request sent for: %s' % path)

    # create BeautifulSoup object out of html content
    soup = BeautifulSoup(r.content)

    # extract results and is_last_page using SearchSong's functions
    results = SearchSong.extract_results_single_page(soup)
    is_last_page = SearchSong.is_last_page(soup, page_num)

    json_data[RESULTS] = results
    json_data[IS_LAST_PAGE] = is_last_page

    if letter is not None:
        json_data[LETTERS] = extract_letters_list(soup)

    return json.dumps(json_data, sort_keys=False)

@list_song.route('/list/scripture/<testament>')
def get_list_scripture(testament):
    # data to be returned as json
    json_data = {}
    
    # fill in testament
    json_data[TESTAMENT] = testament
    
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
    
    json_data[BOOK] = books
    
    return json.dumps(json_data, sort_keys=False)

@list_song.route('/list/index_buttons/<song_type>')
def get_index_buttons(song_type):
    # data to be returned as json
    json_data = {}
    
    # fill in song type
    json_data[SONG_TYPE] = song_type
    
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