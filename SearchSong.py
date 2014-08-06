import os, requests, re, simplejson as json
from bs4 import BeautifulSoup
from flask import Blueprint

search_song = Blueprint('search_song', __name__)

URL_FORMAT = 'http://www.hymnal.net/en/search/all/all/%s/%d'

# maximum number of times we can loop, to avoid infinite loops
MAX_LOOP_COUNT = 100

debug = False

def log(msg):
    if (debug):
        print msg

# clears all children of a particular soup element
def clear_children(element):
    children = element.findChildren()
    for child in children:
        child.clear()

# extracts search results from a single soup page
def extract_results_single_page(soup):
    # list of results to return
    search_results = []
    
    # finds div element with class as 'list-group'
    list_group = soup.find('div',{'class':'list-group'})
    
    # if there is no 'list-group' class, then return empty list
    if list_group is None:
        return []
    
    # find all link elements of the div
    search_result_elements = list_group.findAll('a')

    for element in search_result_elements:
        # clear children to get rid of the annoying
        # <span class="label label-default">New Tunes</span> elements
        clear_children(element)
        
        # create search_result dictionary
        search_result = {}
        search_result['title'] = element.getText().strip()
        search_result['link'] = element.get('href')
        
        # append to results
        search_results.append(search_result)
    return search_results

@search_song.route('/search/<search_parameter>')
def search_hymn_all(search_parameter):
    # data to be returned as json
    json_data = {}
    
    # fill in search parameter
    json_data['search_parameter'] = search_parameter
    
    # start at page 1.
    # This is here because Hymnal.net returns the results in pages, so to find all
    # search results, we need to keep track and go through every page
    page_num = 1
    
    search_results = []
    
    # keep looping until we find a page with 0 results
    # or if we reach MAX_LOOP_COUNT
    for loop in range(MAX_LOOP_COUNT):
    
        # make http GET request to search page
        r = requests.get(URL_FORMAT % (search_parameter, page_num))
        log('request sent for: %s, Page %d' % (search_parameter, page_num))
    
        # create BeautifulSoup object out of html content
        soup = BeautifulSoup(r.content)
        
        # extract results from the single page
        page_results = extract_results_single_page(soup)

        if len(page_results) == 0:
            # end of results, so break out of loop
            break
        else:
            # otherwise append results to search_results list and increment page_num
            search_results.extend(page_results)
            page_num += 1

    json_data['search_results'] = search_results

    return json.dumps(json_data, sort_keys=False)