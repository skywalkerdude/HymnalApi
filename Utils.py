from bs4 import BeautifulSoup

NAME = 'name'
PATH = 'path'

# clears all children of a particular soup element
def clear_children(element):
    map(lambda child: child.clear(), element.findChildren())

# extracts all links out of a container into a dictionary
def extract_links(container, name_key = NAME, path_key=PATH, should_clear_children=True):
     # find all link elements of the div
    elements = container.findAll('a')
    
    # list of results to return
    search_results = []
    
    for element in elements:
        if should_clear_children:
            # clear children to get rid of any excess info that we don't want
            # eg: <span class="label label-default">New Tunes</span> elements
            clear_children(element)
    
        # search_results dictionary with attributes name_key and value_key
        search_result = {}
        search_result[name_key] = element.text.strip()
        search_result[path_key] = element.get('href')
        search_results.append(search_result)

    return search_results

def is_last_page(soup, current_page):
    
    pages = soup.find('ul', {'class':'pagination'})
    
    # if pages is None, return True
    if not pages:
        return True
    
    for string in pages.stripped_strings:
        try:
            num = int(string)
            if num > current_page:
                return False
        except ValueError:
            continue
    return True

# extracts search results from a single soup page
def extract_results_single_page(soup):
    
    # finds div element with class as 'list-group'
    list_group = soup.find('div',{'class':'list-group'})
    
    # if there is no 'list-group' class, then return empty list
    if list_group is None:
        return []
    
    # extract all links from the div
    return extract_links(list_group)