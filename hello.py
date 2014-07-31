import os, requests, re, simplejson as json
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)

URL_FORMAT = 'http://www.hymnal.net/en/hymn/%s'
EXTERNAL_LYRICS_TABLE_REGEX = '<table width=500>(.*?)</table>'
VERSE_TYPE = 'verse_type'
VERSE_CONTENT = 'verse_content'
CHORUS = 'chorus'
VERSE = 'verse'
NAME = 'name'
DATA = 'data'

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

@app.route('/')
def intro():
    return 'Welcome to my API'

@app.route('/hymn/<path:hymn_path>')
def hymn_path(hymn_path):
    # data to be returned as json
    json_data = {}
    
    # make http GET request to song path
    r = requests.get(URL_FORMAT % hymn_path)
    log('request sent for: %s' % hymn_path)
    
    # create BeautifulSoup object out of html content
    soup = BeautifulSoup(r.content)
    
    # fill in title
    json_data[soup.title.name] = soup.title.string
    
    # extract meta data (Category, Subcategory, etc)
    meta_data = []
    meta_data_divs = soup.findAll('div',{'class':'row'})
    for div in meta_data_divs:
        labels = div.find_all("label", {"class":"col-xs-5 col-sm-4 text-right"})
        if len(labels) == 0:
            continue
        for label in labels:
            name = label.text.replace(':','')
            data = []
            children = label.findNextSibling().findAll('a')
            for child in children:
                value = child.text
                link = child.get('href')
                data.append({'value' : value, 'link' : link})
            # append meta data to meta_data list
            meta_data.append(get_meta_data_object(name, data))
    json_data['meta_data'] = meta_data

    lyrics = []
    raw_lyrics = soup.find('div',{'class':'lyrics'})

    # for the songs with "View Lyrics (external site)"
    if raw_lyrics.find('div',{'class':'alert'}):
        # parse out url from raw_lyrics
        url = raw_lyrics.find('div',{'class':'alert'}).findChild().get('href').strip()
        
        # make http GET request to song path
        external_response = requests.get(url)
        log('request sent for: %s' % url)
        
        # BeautifulSoup randomly adds a </table> tag, so we need to use regex to find the table with the lyrics
        content = re.compile(EXTERNAL_LYRICS_TABLE_REGEX, re.DOTALL).findall(external_response.content)[0]
        
        # create BeautifulSoup object out of html content
        external_soup = BeautifulSoup(content)
        
        stanza_content = []
        # indicates which stanza we are currently parsing
        stanza_num = 0
        
        for line in external_soup.stripped_strings:
            # if line is a number or 'Chorus', it indicates that the previous stanza was finished
            if line.isdigit() or line == 'Chorus':
                # stanza is finished, so append stanza to lyrics hash
                if stanza_num != 0:

                    # create and populate verse object with verse_type and verse_content
                    verse = {}
                    if stanza_num == 'Chorus':
                        verse[VERSE_TYPE] = CHORUS
                    else :
                        verse[VERSE_TYPE] = VERSE
                    verse[VERSE_CONTENT] = stanza_content
                    
                    # append finished stanza to lyrics hash
                    lyrics.append(verse)

                    # reset stanza content
                    stanza_content = []
                # new stanza number
                stanza_num = line
            else:
                stanza_content.append(line)
    else:
        for td in raw_lyrics.findAll('td'):
            stanza_content = []
        
            # skip td if it is empty or is just a number
            if len(td.text.strip()) == 0 or td.text.strip().isdigit():
                continue
 
            # for each line in the stanza, append to stanza list
            for line in td.stripped_strings:
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

    json_data['lyrics'] = lyrics

    return json.dumps(json_data, sort_keys=False)

if __name__ == '__main__':
    app.run(debug=True)

#test songs: 1151, ns/157, h/1197, h/17