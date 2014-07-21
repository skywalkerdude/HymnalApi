import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/esther_sucks')
def goodbye():
    return "Esther Sucks"
