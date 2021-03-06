import sys; sys.path.append('..')
import unittest, flask, json, hymnalnetapi, SearchSong
from unittest.mock import create_autospec, patch, Mock
from nose.tools import assert_equal

class FlaskrTestCase(unittest.TestCase):
    
    def setUp(self):
        hymnalnetapi.app.config['TESTING'] = True
        self.app = hymnalnetapi.app.test_client()
    
    def test_request_data(self):
        with hymnalnetapi.app.test_request_context('/v2/search/Drink/2'):
            assert_equal(flask.request.path, '/v2/search/Drink/2')
    
    # test the negative cases that return Bad request
    def test_list_song_expected_search_parameter(self):
        rv = self.app.get('/v2/search/')
        assert rv.status_code == 404
    def test_list_song_expected_page_number(self):
        rv = self.app.get('/v2/search/drink/')
        assert rv.status_code == 404

    # test searching for all the songs matching a particular search parameter
    def test_search_all(self):
        self.assert_search_results(search_parameter='drink')
    
    # test searching for a specific page of songs matching a particular search parameter
    def test_search_page(self):
        self.assert_mock_search_results(search_parameter='drink', page_num=3)
        self.assert_mock_search_results(search_parameter='God', page_num=52)
    
    def assert_mock_search_results(self, search_parameter, page_num):
        # url to stub out
        url = SearchSong.URL_FORMAT % (search_parameter, page_num)
        # mock out hymnal.net response
        mock_response = Mock()
        mock_response.content = open('test_data/search_song_html_{}_{}.txt'.format(search_parameter, page_num), 'r')
        
        patcher = patch('requests.get', Mock(side_effect = lambda k: {url: mock_response}.get(k, 'unhandled request %s' % k)))
        patcher.start()
        self.assert_search_results(search_parameter, page_num)
        patcher.stop()

    def assert_search_results(self, search_parameter, page_num = None):
        if page_num is None:
            rv = self.app.get('v2/search/{}'.format(search_parameter))
            expected_result = json.loads(open('test_data/search_song_{}.txt'.format(search_parameter)).read())
        else:
            rv = self.app.get('v2/search/{}/{}'.format(search_parameter, page_num))
            expected_result = json.loads(open('test_data/search_song_{}_{}.txt'.format(search_parameter, page_num)).read())
        
        actual_result = json.loads(rv.get_data(as_text=True))
        assert_equal(actual_result, expected_result)

if __name__ == '__main__':
    unittest.main()
