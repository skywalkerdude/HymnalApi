from bs4 import BeautifulSoup

NAME = 'name'
PATH = 'path'

# extracts all links out of a container into a dictionary
def extract_links(container, name_path = NAME):
     # find all link elements of the div
    elements = container.findAll('a')
    
    # list of results to return
    search_results = []
    
    for element in elements:
        # clear children to get rid of any excess info that we don't want
        # eg: <span class="label label-default">New Tunes</span> elements
        clear_children(element)
    
        # create search_result dictionary
        search_result = {}
        search_result[name_path] = element.getText().strip()
        search_result[PATH] = element.get('href')
        search_results.append(search_result)

    return search_results

# clears all children of a particular soup element
def clear_children(element):
    children = element.findChildren()
    for child in children:
        child.clear()