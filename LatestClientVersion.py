import simplejson as json
from flask import Blueprint

latest_client_version = Blueprint('latest_client_verison', __name__)

LATEST_CLIENT_VERSION = 'latest_client_version'

@latest_client_version.route('/latestVersion')
def get_hymn():
    return json.dumps({LATEST_CLIENT_VERSION : 2}, sort_keys=False)