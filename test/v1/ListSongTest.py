import sys; sys.path.append('..')
import hymnalnetapi, unittest, ListSong, flask, json, pdb
from unittest.mock import create_autospec, patch, Mock
from nose.tools import assert_equal

class FlaskrTestCase(unittest.TestCase):
    
    def setUp(self):
        hymnalnetapi.app.config['TESTING'] = True
        self.app = hymnalnetapi.app.test_client()
        self.app.url_mapping = self.build_url_mapping()
        self.app.html_mapping = self.build_html_mapping()
    
    def test_request_data(self):
        with hymnalnetapi.app.test_request_context('/list?song_type=lb&letter=g&testament=ot'):
            assert_equal(flask.request.path, '/list')
            assert_equal(flask.request.args['song_type'], 'lb')
            assert_equal(flask.request.args['letter'], 'g')
            assert_equal(flask.request.args['testament'], 'ot')
    
    # test the negative cases that return Bad request
    def test_list_song_negative(self):
        rv = self.app.get('/list')
        assert rv.status_code == 400
        assert 'Request is missing argument: song_type' in rv.get_data(as_text=True)
        rv = self.app.get('/list?song_type=h')
        assert rv.status_code == 400
        assert 'Request is missing argument: letter' in rv.get_data(as_text=True)
        rv = self.app.get('/list?song_type=scripture&letter=g')
        assert rv.status_code == 400
        assert 'Request is missing argument: testament' in rv.get_data(as_text=True)

    # test listing classical hymns
    def test_list_h(self):
        self.assert_classical_hymn('g')

    # test listing new songs
    def test_list_ns(self):
        self.assert_new_song('g')

    # test listing new tunes
    def test_list_nt(self):
        self.assert_new_tune()
    
    # test listing scripture songs
    def test_list_scripture(self):
        self.assert_scripture_song('ot')
        self.assert_scripture_song('nt')

    def assert_classical_hymn(self, letter):
        song_type = 'h'
        self.assert_mock_list_results(self.app.url_mapping[(song_type, letter)], song_type=song_type, letter=letter)
    
    def assert_new_song(self, letter):
        song_type='ns'
        self.assert_mock_list_results(self.app.url_mapping[(song_type, letter)], song_type=song_type, letter=letter)

    def assert_new_tune(self):
        song_type='nt'
        self.assert_mock_list_results(self.app.url_mapping[song_type], song_type=song_type)
    
    def assert_scripture_song(self, testament):
        song_type='scripture'
        self.assert_mock_list_results(self.app.url_mapping[(song_type, testament)], song_type=song_type, testament=testament)
    
    def assert_mock_list_results(self, url, song_type, letter = None, testament = None):
        # mock out hymnal.net response
        mock_response = Mock()
        mock_response.content = open(self.app.html_mapping[url], 'r').read()
        
        patcher = patch('requests.get', Mock(side_effect = lambda k: {url: mock_response}.get(k, 'unhandled request %s' % k)))
        patcher.start()
        self.assert_list_results(song_type, letter, testament)
        patcher.stop()

    def assert_list_results(self, song_type, letter = None, testament = None):
        if song_type == 'h' or song_type == 'ns':
            # make request to get hymn from hymnal.net
            rv = self.app.get('list?song_type={}&letter={}'.format(song_type, letter))
            actual_result = json.loads(rv.get_data(as_text=True))
            # open saved test data
            expected_result = json.loads(open('test_data/list_song_{}_{}.txt'.format(song_type, letter), 'r').read())

        elif song_type == 'nt':
            # make request to get hymn from hymnal.net
            rv = self.app.get('list?song_type={}'.format(song_type))
            actual_result = json.loads(rv.get_data(as_text=True))
            # open saved test data
            expected_result = json.loads(open('test_data/list_song_{}.txt'.format(song_type), 'r').read())

        elif song_type == 'scripture':
            # make request to get hymn from hymnal.net
            rv = self.app.get('list?song_type={}&testament={}'.format(song_type, testament))
            actual_result = json.loads(rv.get_data(as_text=True))
            # open saved test data
            expected_result = json.loads(open('test_data/list_song_{}_{}.txt'.format(song_type, testament), 'r').read())

        assert_equal.__self__.maxDiff = None
        assert_equal(actual_result, expected_result)

    def build_url_mapping(self):
        return {
            ('h', 'g'): 'http://www.hymnal.net/en/song-index/h/G',
            ('ns', 'g'): 'http://www.hymnal.net/en/song-index/ns/G',
            'nt': 'http://www.hymnal.net/en/song-index/nt',
            ('scripture', 'ot') : 'http://www.hymnal.net/en/scripture-songs/ot',
            ('scripture', 'nt') : 'http://www.hymnal.net/en/scripture-songs/nt'
        }

    def build_html_mapping(self):
        return {
            'http://www.hymnal.net/en/song-index/h/G': 'test_data/list_song_html_h_g.txt',
            'http://www.hymnal.net/en/song-index/ns/G': 'test_data/list_song_html_ns_g.txt',
            'http://www.hymnal.net/en/song-index/nt': 'test_data/list_song_html_nt.txt',
            'http://www.hymnal.net/en/scripture-songs/ot': 'test_data/list_song_html_scripture_ot.txt',
            'http://www.hymnal.net/en/scripture-songs/nt': 'test_data/list_song_html_scripture_nt.txt'
    }

if __name__ == '__main__':
    unittest.main()
