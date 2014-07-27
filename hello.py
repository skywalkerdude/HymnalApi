import os, requests, re, simplejson as json
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)

URL_FORMAT = 'http://www.hymnal.net/en/hymn/%s'
LYRICS_REGEX = '<div class="stanza-num">\d+</div>.*?<td>(.*?)</td>'
CHORUS_REGEX = '<td class="chorus">(.*?)</td>'
# http://www.regular-expressions.info/examples.html
TAG_REGEX = r'<%(TAG)s\b[^>]*>(.*?)</%(TAG)s>'
EXTERNAL_LYRICS_URL_REGEX = r'<a href="(.*?)".*View Lyrics \(external site\)'
EXTERNAL_LYRICS_TABLE_REGEX = '<table width=500>(.*?)</table>'
debug = True

def log(msg):
    if (debug):
        print msg

@app.route('/')
def intro():
    return 'Welcome to my API'

def get_data(regex, string):
    return re.compile(regex, re.DOTALL).findall(string)

def get_meta_data(regex, string, multiple_result = False):
    # get data according to regex
    result = get_data(regex, string)
    # if result has nothing, then return empty string
    if len(result) < 1:
        rtn = ""
    else:
        # find all of the hyperlink data, which contains the actual text of the tag.
        # eg: <a href="http://online.recoveryversion.org/BibleChapters.asp?fcid=239021&lcid=239021" target="_blank">Revelation 22</a>
        result = re.compile(TAG_REGEX % {'TAG': "a"}, re.DOTALL).findall(result[0])
        
        if len(result) == 0:
            # length is 0, that means there were no hyperlinks, so set rtn to empty string
            rtn = ""
        elif len(result) == 1:
            # there was exactly 1 hyperlink, set rtn to first entry
            rtn = result[0]
        else:
            # otherwise return rtn as is
            rtn = result

    # if the caller is expecting a list, then convert rtn into a list if it isn't already. Otherwise, just return rtn as is
    if multiple_result:
        if type(rtn) == list:
            return rtn
        else:
            return [rtn]
    else:
        return rtn

def fetch_external(url):
    r = requests.get(url)
    log(re.compile(EXTERNAL_LYRICS_TABLE_REGEX, re.DOTALL).findall(r.content))
    return url

# takes all instances of &nbsp; and replaces it with a space, which is what it represents
def convert_whitespaces(string):
    return string.replace('&nbsp;', ' ')

def get_lyrics(content):
    match = re.compile(EXTERNAL_LYRICS_URL_REGEX).search(content)
    if match:
        return fetch_external(match.group(1))
    lyrics = get_data(LYRICS_REGEX, content)

    # there were no lyrics, so lets try to find lyrics without a stanza number
    if len(lyrics) == 0:
        # find everything in the lyrics table
        raw_lyrics = re.compile('<div class="col-xs-12 lyrics">.*?<table>(.*?)</table>', re.DOTALL).findall(content)
        # if this is still empty, then there really aren't any lyrics :(
        if len(raw_lyrics) == 0:
            return ""
        # filter out the cells with no class or id
        tagless_lyrics =re.compile('<td>(.*?)</td>',re.DOTALL).findall(raw_lyrics[0])
        # only consider itm if content is not whitespace
        lyrics = [ item for item in tagless_lyrics if convert_whitespaces(item).strip() != '']
    return lyrics

@app.route('/hymn/<path:hymn_path>')
def hymn_path(hymn_path):
    # data to be returned as json
    data = {}
    
    # make http GET request to song path
    r = requests.get(URL_FORMAT % hymn_path)
    log('request sent for: %s' % hymn_path)
    
    # create BeautifulSoup object out of html content
    soup = BeautifulSoup(r.content)
    log('soup created!')
    
    # fill in title
    data[soup.title.name] = soup.title.string
    
    # extract meta data (Category, Subcategory, etc)
    meta_data = {}
    meta_data_divs = soup.findAll('div',{'class':'row'})
    for div in meta_data_divs:
        labels = div.find_all("label", {"class":"col-xs-5 col-sm-4 text-right"})
        if len(labels) == 0:
            continue
        for label in labels:
            title = label.text.replace(':','')
            values = []
            children = label.findNextSibling().findChildren()
            for child in children:
                value = child.text
                link = child.get('href')
                values.append({'value' : value, 'link' : link})
            meta_data[title] = values
    data['meta_data'] = meta_data

    lyrics = get_lyrics(r.content)
    log('lyrics: %s' % lyrics)
    chorus = get_data(CHORUS_REGEX, r.content)
    log('chorus: %s' % chorus)
    #data = {'title': title, 'category': category, 'subcategory': subcategory, 'key': key, 'time': time, 'meter': meter, 'hymn_code': hymn_code, 'scriptures': scriptures, 'lyrics': lyrics, 'chorus': chorus, 'piano_sheet_url': piano_sheet_url, 'guitar_sheet_url': guitar_sheet_url, 'mp3_url': mp3_url}
    return json.dumps(data, sort_keys=True, indent=2)

@app.route('/esther_sucks')
def esther_sucks():
    return 'Wow, very good Joseph, Esther does suck!'

if __name__ == '__main__':
    app.run(debug=True)

#test songs: 1151, ns/157, h/1197, h/17