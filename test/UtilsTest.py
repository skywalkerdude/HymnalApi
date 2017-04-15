import sys; sys.path.append('..')
import unittest, Utils
from bs4 import BeautifulSoup, element
from urllib import parse as urlparse
from unittest.mock import create_autospec, call
from nose.tools import assert_equal

import os, requests, re, simplejson as json

class UtilsTest(unittest.TestCase):
    # https://docs.python.org/3/library/unittest.mock.html
    # https://docs.python.org/3/library/unittest.mock.html#auto-speccing
    
    def test_clear_children(self):
        
        # set up the mocks
        element_mock = create_autospec(BeautifulSoup)
        child_mock1 = create_autospec(BeautifulSoup)
        child_mock2 = create_autospec(BeautifulSoup)
        child_mock3 = create_autospec(BeautifulSoup)
        child_mock4 = create_autospec(BeautifulSoup)
        element_mock.findChildren.return_value = [child_mock1, child_mock2, child_mock3]

        Utils.clear_children(element_mock)

        child_mock1.clear.assert_called_once_with()
        child_mock2.clear.assert_called_once_with()
        child_mock3.clear.assert_called_once_with()
        assert not child_mock4.clear.called, 'child_mock4.clear was called and should not have been'


    def test_extract_links(self):

        # set up the mocks
        container_mock = create_autospec(BeautifulSoup)
        element_mock1 = create_autospec(BeautifulSoup)
        element_mock2 = create_autospec(BeautifulSoup)
        element_mock3 = create_autospec(BeautifulSoup)
        element_mock4 = create_autospec(BeautifulSoup)
        
        # populate mocks with data
        i = 1
        for element in [element_mock1, element_mock2, element_mock3, element_mock4]:
            text = create_autospec(str)
            text.strip.return_value = 'element_mock' + str(i)
            element.text = text
            element.get.return_value = 'link' + str(i)
            i += 1
        
        container_mock.findAll.return_value = [element_mock1, element_mock2, element_mock3]

        # mock out clear_children call
        funct = Utils.clear_children
        Utils.clear_children = create_autospec(Utils.clear_children)

        # call without clear_children
        search_results = Utils.extract_links(container_mock, should_clear_children = False)
        
        # call with clear_children
        search_results = Utils.extract_links(container_mock, should_clear_children = True)

        test_results = [{'name' : 'element_mock1', 'path' : 'link1'},
                        {'name' : 'element_mock2', 'path' : 'link2'},
                        {'name' : 'element_mock3', 'path' : 'link3'}]
        assert search_results == test_results
        
        # assert that Utils.clear_children was called wich each mock element
        # http://www.voidspace.org.uk/python/mock/mock.html#mock.Mock.assert_has_calls
        # http://www.voidspace.org.uk/python/mock/helpers.html#calls-as-tuples
        calls = [call(element_mock1), call(element_mock2), call(element_mock3)]
        Utils.clear_children.assert_has_calls(calls)
        assert Utils.clear_children.call_count == 3
        
        calls = [call('a'), call('a')]
        container_mock.findAll.assert_has_calls(calls)
        container_mock.findAll.call_count == 3
        
        calls = [call(), call()]
        element_mock1.text.strip.assert_has_calls(calls)
        assert element_mock1.text.strip.call_count == 2
        element_mock2.text.strip.assert_has_calls(calls)
        assert element_mock2.text.strip.call_count == 2
        element_mock3.text.strip.assert_has_calls(calls)
        assert element_mock3.text.strip.call_count == 2
        assert not element_mock4.text.strip.called, 'element_mock4.text.strip was called and should not have been'
        
        calls = [call('href'), call('href')]
        element_mock1.get.assert_has_calls(calls)
        assert element_mock1.get.call_count == 2
        element_mock2.get.assert_has_calls(calls)
        assert element_mock2.get.call_count == 2
        element_mock3.get.assert_has_calls(calls)
        assert element_mock3.get.call_count == 2
        assert not element_mock4.get.called, 'element_mock4.get was called and should not have been'
            
        # reset extract_links back to it's original value
        Utils.clear_children = funct

    def test_is_last_page_none(self):
        # set up the mock
        soup_mock = create_autospec(BeautifulSoup)
        current_page = 3

        # set return value of find to None to test None case
        soup_mock.find.return_value = None
        assert Utils.is_last_page(soup_mock, current_page)
        soup_mock.find.assert_called_once_with('ul', {'class':'pagination'})

    def test_is_last_page_true(self):
        # set up the mock
        soup_mock = create_autospec(BeautifulSoup)
        current_page = 3

        # test case where current_page is the last page
        pages_mock = create_autospec(element.Tag)
        pages_mock.stripped_strings = ['1', '2', '3']
        soup_mock.find.return_value = pages_mock
        assert Utils.is_last_page(soup_mock, current_page)
        soup_mock.find.assert_called_once_with('ul', {'class':'pagination'})

    def test_is_last_page_false(self):
        # set up the mock
        soup_mock = create_autospec(BeautifulSoup)
        current_page = 3
    
        # test case where current_page is not the last page
        pages_mock = create_autospec(element.Tag)
        pages_mock.stripped_strings = ['1', '2', '3', '4']
        soup_mock.find.return_value = pages_mock
        assert not Utils.is_last_page(soup_mock, current_page)
        soup_mock.find.assert_called_once_with('ul', {'class':'pagination'})

    def test_is_last_page_value_error(self):
        # set up the mock
        soup_mock = create_autospec(BeautifulSoup)
        current_page = 3
    
        # Non-integer value in stripped_strings should just be skipped
        pages_mock = create_autospec(element.Tag)
        pages_mock.stripped_strings = ['1', 'str', '3', '4']
        soup_mock.find.return_value = pages_mock
        assert not Utils.is_last_page(soup_mock, current_page)
        soup_mock.find.assert_called_once_with('ul', {'class':'pagination'})

    def test_extract_results_single_page_none(self):
        # set up the mock
        soup_mock = create_autospec(BeautifulSoup)
    
        # set return value of find to None to test None case
        soup_mock.find.return_value = None
        assert Utils.extract_results_single_page(soup_mock) == []
        soup_mock.find.assert_called_once_with('div',{'class':'list-group'})

    def test_extract_results_single_page(self):
        # set up the mock
        soup_mock = create_autospec(BeautifulSoup)
        soup_mock.find.return_value = 'placeholder'
    
        # stub out extract_links since it's already tested
        funct = Utils.extract_links
        Utils.extract_links = create_autospec(Utils.extract_links)
    
        Utils.extract_results_single_page(soup_mock)
    
        soup_mock.find.assert_called_once_with('div',{'class':'list-group'})
        Utils.extract_links.assert_called_once_with('placeholder')
    
        # reset extract_links back to it's original value
        Utils.extract_links = funct

    def test_add_query_to_url(self):
        url = 'hymn'
        query = tuple()
        assert_equal('hymn', Utils.add_query_to_url(url, query))

        query = (('gb', '1'),)
        assert_equal('hymn?gb=1', Utils.add_query_to_url(url, query))

        url = 'hymn?gb=1'
        query = (('query', '2'), ('test', '1'))
        result = Utils.add_query_to_url(url, query)
        resulting_query = dict(urlparse.parse_qsl(urlparse.urlparse(result).query))
        assert_equal({'gb': '1', 'query': '2', 'test': '1'}, resulting_query)

if __name__ == '__main__':
    unittest.main()
