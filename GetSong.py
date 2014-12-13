import os, requests, re, simplejson as json, Utils, Constants
from bs4 import BeautifulSoup
from flask import Blueprint, request

get_song = Blueprint('get_song', __name__)

GET_SONG_URL_FORMAT = 'http://www.hymnal.net/en/hymn/%s'
# to create a path like h/1151 or ns/134
HYMN_PATH_FORMAT = '%s/%d'
EXTERNAL_LYRICS_TABLE_REGEX = '<table width=500>(.*?)</table>'
VERSE_TYPE = 'verse_type'
VERSE_CONTENT = 'verse_content'
CHORUS = 'chorus'
VERSE = 'verse'
NAME = 'name'
VALUE= 'value'
DATA = 'data'
HYMN_TYPE = 'hymn_type'
HYMN_NUMBER = 'hymn_number'
META_DATA = 'meta_data'
LYRICS = 'lyrics'

debug = False

def log(msg):
    if (debug):
        print msg

# returns a meta data object from it's name and data
def get_meta_data_object(name, data):
    meta_data_object = {}
    meta_data_object[NAME] = name
    meta_data_object[DATA] = data
    return meta_data_object

# creates a verse object with the stanza num and content
def create_verse(stanza_num, stanza_content):
    # create and populate verse object with verse_type and verse_content
    verse = {}
    if stanza_num == 'Chorus':
        verse[VERSE_TYPE] = CHORUS
    else :
        verse[VERSE_TYPE] = VERSE
    verse[VERSE_CONTENT] = stanza_content
    return verse

@get_song.route('/hymn')
def get_hymn():
    
    # initialize arguments
    hymn_type = request.args.get('hymn_type', type=str)
    hymn_number = request.args.get('hymn_number', type=int)
    
    # error checking
    message = None
    if hymn_type is None:
        message = {Constants.PUBLIC : Constants.ERROR_MESSAGE % HYMN_TYPE}
    elif hymn_number is None:
        message = {Constants.PUBLIC : Constants.ERROR_MESSAGE % HYMN_NUMBER}
    
    # if message is not None, then return 400 with the message
    if message is not None:
        message['status_code'] = 400
        return (json.dumps(message), 400)

    # data to be returned as json
    json_data = {}

    # create path
    path = HYMN_PATH_FORMAT % (hymn_type, hymn_number)
    
    # make http GET request to song path
    r = requests.get(GET_SONG_URL_FORMAT % path)
    log('request sent for: %s' % path)
    
    # create BeautifulSoup object out of html content
    soup = BeautifulSoup(r.content)
    
    # fill in title
    json_data[soup.title.name] = soup.title.string
    
    # extract meta data (Category, Subcategory, etc)
    meta_data = []
    # meta data contained in side bar
    sidebar = soup.find('div',{'class':'sidebar'})
    # info is in divs with common-panel
    meta_data_divs = sidebar.findChildren('div',{'class':'common-panel'})
    for div in meta_data_divs:
        # search by CSS class
        # http://www.crummy.com/software/BeautifulSoup/bs4/doc/#searching-by-css-class
        labels = div.find_all('label', class_= 'col-xs-5')
        if len(labels) == 0:
            continue
        for label in labels:
            name = label.text.replace(':','')
            data = Utils.extract_links(label.findNextSibling(), name_key=VALUE)
            
            # append meta data to meta_data list if it doesn't exist already
            meta_data_object = get_meta_data_object(name, data)
            if meta_data_object not in meta_data:
                meta_data.append(meta_data_object)
    json_data[META_DATA] = meta_data

    lyrics = []
    raw_lyrics = soup.find('div',{'class':'lyrics'})

    # for the songs with "View Lyrics (external site)"
    if raw_lyrics.find('div',{'class':'alert'}):
        # parse out url from raw_lyrics
        url = raw_lyrics.find('div',{'class':'alert'}).findChild().get('href').strip()
        
        # make http GET request to song path
        external_response = requests.get(url)
        log('request sent for: %s' % url)
        
        # BeautifulSoup randomly adds a </table> tag in the middle which screws up the scraping, so we need to use regex to find the table with the lyrics
        content = re.compile(EXTERNAL_LYRICS_TABLE_REGEX, re.DOTALL).findall(external_response.content)[0]
        
        # create BeautifulSoup object out of html content
        external_soup = BeautifulSoup(content)
        
        stanza_content = []
        # indicates which stanza we are currently parsing
        stanza_num = 0
        
        for line in external_soup.strings:
            
            # if line is empty, then skip it
            if len(line.strip()) == 0:
                continue
            
            # if line is a number or 'Chorus', it indicates that the previous stanza was finished
            if line.strip().isdigit() or line.strip() == 'Chorus':
                # stanza is finished, so append stanza to lyrics hash
                if stanza_num != 0:
                    
                    # creates a verse object with the stanza num and content
                    verse = create_verse(stanza_num, stanza_content)
                    
                    # append finished stanza to lyrics hash
                    lyrics.append(verse)

                    # reset stanza content
                    stanza_content = []
                # new stanza number
                stanza_num = line.strip()
            else:
                stanza_content.append(line)

        # after loop is over, create verse object and append to lyrics hash
        verse = create_verse(stanza_num, stanza_content)
        lyrics.append(verse)
            
        # reset stanza_content for good measure
        stanza_content = []
    else:
        for td in raw_lyrics.findAll('td'):
            stanza_content = []
        
            # skip td if it is empty or is just a number
            if len(td.text.strip()) == 0 or td.text.strip().isdigit():
                continue
 
            # for each line in the stanza, append to stanza list
            for line in td.strings:
                stanza_content.append(line)
            
            # create and populate verse object with verse_type and verse_content
            verse = {}
            if td.get('class') and 'chorus' in td.get('class'):
                verse[VERSE_TYPE] = CHORUS
            else:
                verse[VERSE_TYPE] = VERSE
            verse[VERSE_CONTENT] = stanza_content

            # append finished stanza to lyrics hash
            lyrics.append(verse)

    json_data[LYRICS] = lyrics

    return json.dumps(json_data, sort_keys=False)