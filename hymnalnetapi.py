import os, requests, re, simplejson as json
from bs4 import BeautifulSoup
from flask import Flask
from GetSong import get_song

app = Flask(__name__)
app.register_blueprint(get_song)

@app.route('/')
def intro():
    return 'Welcome to my API'

if __name__ == '__main__':
    app.run(debug=True)