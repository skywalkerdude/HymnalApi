import hymnalnetapi, unittest, ListSong, flask, json
from mock import create_autospec
from nose.tools import assert_equal

class FlaskrTestCase(unittest.TestCase):
    
    def setUp(self):
        hymnalnetapi.app.config['TESTING'] = True
        self.app = hymnalnetapi.app.test_client()
    
    def test_request_data(self):
        with hymnalnetapi.app.test_request_context('/search?search_paramter=Drink&page_num=2'):
            assert_equal(flask.request.path, '/search')
            assert_equal(flask.request.args['search_paramter'], 'Drink')
            assert_equal(flask.request.args['page_num'], '2')
    
    # test the negative cases that return Bad request
    def test_list_song_negative(self):
        rv = self.app.get('/search')
        assert rv.status_code == 400
        assert 'Request is missing argument: search_parameter' in rv.data

    # test searching for all the songs matching a particular search parameter
    def test_search_all(self):
        self.assert_list_results(search_parameter='drink')
    
    # test searching for a specific page of songs matching a particular search parameter
    def test_search_all(self):
        self.assert_list_results(search_parameter='drink', page_num=3)

    def assert_list_results(self, search_parameter, page_num = None):
        if page_num is None:
            rv = self.app.get('search?search_parameter={}'.format(search_parameter))
            expected_result = json.loads(open('test_data/search_song_{}.txt'.format(search_parameter)).read())
        else:
            rv = self.app.get('search?search_parameter={}&page_num={}'.format(search_parameter, page_num))
            expected_result = json.loads(open('test_data/search_song_{}_{}.txt'.format(search_parameter, page_num)).read())
        
        actual_result = json.loads(rv.data)
        assert_equal(actual_result, expected_result)

if __name__ == '__main__':
    unittest.main()