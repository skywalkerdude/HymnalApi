import os, requests, re, simplejson as json
from bs4 import BeautifulSoup
from flask import Flask
from GetSong import get_song
from SearchSong import search_song
from ListSong import list_song
from LatestClientVersion import latest_client_version

app = Flask(__name__)
app.register_blueprint(get_song)
app.register_blueprint(search_song)
app.register_blueprint(list_song)
app.register_blueprint(latest_client_version)

@app.route('/')
def intro():
    return 'Welcome to my API'

if __name__ == '__main__':
    app.run(debug=True)