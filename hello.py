import os, requests, re, sys
import pdb
import simplejson as json
from flask import Flask

app = Flask(__name__)

URL_FORMAT = "http://www.hymnal.net/en/hymn/%s"
TITLE_REGEX = '<title>(.*)</title>'
META_INFO_REGEX = '%s:.*?<div class="col-xs-7 col-sm-8 no-padding">(.*?)<\/div>'
CATEGORY_REGEX = META_INFO_REGEX % 'Category'
SUBCATEGORY_REGEX = META_INFO_REGEX % 'Subcategory'
KEY_REGEX = META_INFO_REGEX % 'Key'
TIME_REGEX = META_INFO_REGEX % 'Time'
METER_REGEX = META_INFO_REGEX % 'Meter'
HYMN_CODE_REGEX = META_INFO_REGEX % 'Hymn Code'
SCRIPTURES_REGEX = META_INFO_REGEX % 'Scriptures'
LYRICS_REGEX = '<div class="stanza-num">\d+</div>.*?<td>(.*?)</td>'
CHORUS_REGEX = '<td class="chorus">(.*?)</td>'
SHEET_MUSIC_REGEX = '%s hidden">.*?<span class="svg">(.*?)</span>'
MP3_REGEX = '<source src="(.*?)" type="audio/mpeg"/>'
# http://www.regular-expressions.info/examples.html
TAG_REGEX = r'<%(TAG)s\b[^>]*>(.*?)</%(TAG)s>'
EXTERNAL_LYRICS_URL_REGEX = '<div class="col-xs-12 lyrics">.*?<a href="(.*?)".*?>.*View Lyrics (external site)</a>'
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
    match = re.compile(EXTERNAL_LYRICS_URL_REGEX, re.DOTALL).search(content)
    log('Match: %s' % match)
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
    r = requests.get(URL_FORMAT % hymn_path)
    log('request sent for: %s' % hymn_path)
    title = re.compile(TITLE_REGEX).findall(r.content)[0]
    log('title: %s' % title)
    category = get_meta_data(CATEGORY_REGEX, r.content)
    log('category: %s' % category)
    subcategory = get_meta_data(SUBCATEGORY_REGEX, r.content)
    log('subcategory: %s' % subcategory)
    key = get_meta_data(KEY_REGEX, r.content)
    log('key: %s' % key)
    time = get_meta_data(TIME_REGEX, r.content)
    log('time: %s' % time)
    meter = get_meta_data(METER_REGEX, r.content)
    log('meter: %s' % meter)
    hymn_code = get_meta_data(HYMN_CODE_REGEX, r.content)
    log('hymn_code: %s' % hymn_code)
    scriptures = get_meta_data(SCRIPTURES_REGEX, r.content, True)
    log('scriptures: %s' % scriptures)
    lyrics = get_lyrics(r.content)
    log('lyrics: %s' % lyrics)
    chorus = get_data(CHORUS_REGEX, r.content)
    log('chorus: %s' % chorus)
    piano_sheet_url = get_data(SHEET_MUSIC_REGEX % 'piano', r.content)
    log('piano_sheet_url: %s' % piano_sheet_url)
    guitar_sheet_url = get_data(SHEET_MUSIC_REGEX % 'guitar', r.content)
    log('guitar_sheet_url: %s' % guitar_sheet_url)
    mp3_url = get_data(MP3_REGEX, r.content)
    log('mp3_url: %s' % mp3_url)
    data = {'title': title, 'category': category, 'subcategory': subcategory, 'key': key, 'time': time, 'meter': meter, 'hymn_code': hymn_code, 'scriptures': scriptures, 'lyrics': lyrics, 'chorus': chorus, 'piano_sheet_url': piano_sheet_url, 'guitar_sheet_url': guitar_sheet_url, 'mp3_url': mp3_url}
    return json.dumps(data, sort_keys=True, indent=2)

@app.route('/esther_sucks')
def esther_sucks():
    return 'Wow, very good Joseph, Esther does suck!'

if __name__ == '__main__':
    app.run(debug=True)

#test songs: 1151, ns/157, h/1197, h/17