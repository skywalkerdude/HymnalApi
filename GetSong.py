import os, requests, re, simplejson as json, Utils, Constants, urllib, pinyin
from bs4 import BeautifulSoup
from flask import Blueprint, request

get_song = Blueprint('get_song', __name__)

GET_SONG_URL_FORMAT = 'http://www.hymnal.net/en/hymn/%s'
# to create a path like h/1151 or ns/134
HYMN_PATH_FORMAT = '%s/%s'
# ?: --> do not extract whatever is matched
# .+? --> match 1 or more of an character, but stop a the first instance
STORED_CLASSIC_LYRICS_REGEX = '(?:(?:<div class=vlinksbox>.+?<\/div>(.*)<div class=vlinksbox>)|(?:<div class="linksbox">.+?<\/div>.*?(<div class=singleverse>.*)<div class="linksbox">))'
VERSE_TYPE = 'verse_type'
VERSE_CONTENT = 'verse_content'
VERSE_TRANSLITERATION = 'transliteration'
CHORUS = 'chorus'
VERSE = 'verse'
OTHER = 'other'
NAME = 'name'
VALUE= 'value'
DATA = 'data'
HYMN_TYPE = 'hymn_type'
HYMN_NUMBER = 'hymn_number'
META_DATA = 'meta_data'
LYRICS = 'lyrics'
SVG = 'svg'
SVG_PIANO = 'Piano'
SVG_GUITAR = 'Guitar'

debug = False

def log(msg):
    if (debug):
        print(msg)

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

# extract the svg from the soup object
def extract_svg(soup):
    svgs = []
    piano_sheet_svg = get_svg_from_div(soup.find('div',{'class':SVG_PIANO.lower()}))
    if piano_sheet_svg is not None:
        svgs.append({VALUE:SVG_PIANO, 'path':piano_sheet_svg})
    guitar_sheet_svg = get_svg_from_div(soup.find('div',{'class':SVG_GUITAR.lower()}))
    if guitar_sheet_svg is not None:
        svgs.append({VALUE:SVG_GUITAR, 'path':guitar_sheet_svg})

    if len(svgs) > 0:
        return get_meta_data_object(SVG, svgs)
    else:
        return None

# helper function to extract the link for the svg from a particular div
def get_svg_from_div(div):
    if div is None:
        return None
    child = div.findChild('span', {'class','svg'})
    if child is None:
        return None
    return child.text

@get_song.route('/v2/hymn/<string:hymn_type>/<string:hymn_number>')
def get_hymn_v2(hymn_type, hymn_number):
    # pass all query parameters through
    additional_args = request.args.copy()
    return get_hymn_internal(hymn_type, hymn_number, additional_args)

@get_song.route('/hymn')
def get_hymn():
    
    # initialize arguments
    hymn_type = request.args.get('hymn_type', type=str)
    hymn_number = request.args.get('hymn_number', type=str)
    
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

    # if there are any additional query parameters, then pass them through
    additional_args = request.args.copy()
    del additional_args['hymn_type']
    del additional_args['hymn_number']
    return get_hymn_internal(hymn_type, hymn_number, additional_args)

def get_hymn_internal(hymn_type, hymn_number, additional_args):
    
    # whether or not we need to check if the song exists.
    check_exists = additional_args.get('check_exists', type=bool)

    # if there are any additional query parameters, then pass it directly to hymnal.net
    if 'check_exists' in additional_args:
        del additional_args['check_exists']

    # create path by plugging in the hymn type and number and appending all query params
    path = HYMN_PATH_FORMAT % (hymn_type, hymn_number)
    # make http GET request to song path
    r = requests.get(Utils.add_query_to_url(GET_SONG_URL_FORMAT % path, additional_args))
    log('request sent for: %s' % path)
    
    # create BeautifulSoup object out of html content
    soup = BeautifulSoup(r.text, "html.parser")

    # If the song doesn't exist, hymnal.net will randomly generate a song that doesn't make sense.
    # However, it does it at run time, meaning if you request it twice, it'll have a different title.
    if check_exists:
        r2 = requests.get(GET_SONG_URL_FORMAT % path)
        soup2 = BeautifulSoup(r2.content, "html.parser")
        if soup2.title != soup.title:
            message = {Constants.PUBLIC : Constants.NOT_REAL_SONG % (hymn_type, hymn_number)}
            message['status_code'] = 400
            return (json.dumps(message), 400)

    # data to be returned as json
    json_data = {}
    
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

    svg = extract_svg(soup)
    if svg is not None:
        meta_data.append(svg)

    json_data[META_DATA] = meta_data

    lyrics = []
    raw_lyrics = soup.find('div',{'class':'lyrics'})

    # for the songs with "View Lyrics (external site)"
    if raw_lyrics.find('div',{'class':'alert'}):
        # Only get the numerical number.
        # This is for when there is a new tune, such as #277b. The "b" doesn't matter when it comes to the lyrics.
        hymn_number = re.findall("\d+", hymn_number)[0]
        
        with open('stored/classic/{}.html'.format(hymn_number), 'r') as data:
            stored_content = data.read()
        content = re.compile(STORED_CLASSIC_LYRICS_REGEX, re.DOTALL).findall(stored_content)[0]
        # filter out the empty items and grab first non-empty item
        content = [str for str in content if str != ''][0]

        # create BeautifulSoup object out of html content
        external_soup = BeautifulSoup(content, "html.parser")
        
        stanza_content = []
        # indicates which stanza we are currently parsing
        stanza_num = 0

        # find all "div"s, which contains a verse or a chorus
        lyric_divs = external_soup.findAll("div")

        # creates a verse object with the stanza num and content
        verse = {}

        # keep track of the previous chorus so we know not to add it if it appears multiple times in a row
        previous_chorus = []

        for lyric_div in lyric_divs:
            # class name of div is "verse" or "chrous"
            isChorus = lyric_div.get("class")[0] == 'chorus'
            
            stanza_content = []
            
            for line in lyric_div.stripped_strings:
                # don't need to include the verse number in the result
                if (line.strip().isdigit()):
                    continue
                else:
                    stanza_content.append(line)

            if isChorus:
                # previous chrous is the same as the current chorus, so just reset everything and continue without appending to lyrics
                if previous_chorus == stanza_content:
                    # reset verse object for next verse
                    verse = {}
                    # reset stanza_content for good measure
                    stanza_content = []
                    continue
                else:
                    previous_chorus = stanza_content
                verse[VERSE_TYPE] = CHORUS
            else:
                verse[VERSE_TYPE] = VERSE
            verse[VERSE_CONTENT] = stanza_content

            # append finished stanza to lyrics hash
            lyrics.append(verse)
            # reset verse object for next verse
            verse = {}
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
            elif td.get('class') and 'copyright' in td.get('class'):
                verse[VERSE_TYPE] = OTHER
            elif td.get('class') and 'note' in td.get('class'):
                verse[VERSE_TYPE] = OTHER
            else:
                verse[VERSE_TYPE] = VERSE
            verse[VERSE_CONTENT] = stanza_content

            # append finished stanza to lyrics hash
            lyrics.append(verse)

    if Utils.has_transliteration(hymn_type, hymn_number):
        for lyric in lyrics:
            # split the original characters, then transliterate and add a space between them
            chars = [list(line) for line in lyric[VERSE_CONTENT]]
            lyric[VERSE_TRANSLITERATION] = [' '.join([pinyin.get(char) for char in char_list]) for char_list in chars]

    json_data[LYRICS] = lyrics

    return json.dumps(json_data, sort_keys=True)

# TODO same tune, language reference
