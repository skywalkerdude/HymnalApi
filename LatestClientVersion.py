import simplejson as json
from flask import Blueprint, redirect

latest_client_version = Blueprint('latest_client_verison', __name__)

LATEST_CLIENT_VERSION = 'latest_client_version'

@latest_client_version.route('/latestVersionNumberAndroid')
def get_latest_android_version_number():
    return json.dumps({LATEST_CLIENT_VERSION : 15}, sort_keys=False)

@latest_client_version.route('/latestVersionAndroid')
def get_hymn():
    return redirect("https://drive.google.com/file/d/0B3XbhMal4IMvOG9wTkVZbVlLNUk/view?usp=sharing", code=302)
