import sys; sys.path.append('..')
import hymnalnetapi, unittest, GetSong, flask, json, urllib, Utils
from unittest.mock import create_autospec, patch, MagicMock as Mock
from nose.tools import assert_equal

class FlaskrTestCase(unittest.TestCase):
    
    def setUp(self):
        hymnalnetapi.app.config['TESTING'] = True
        self.app = hymnalnetapi.app.test_client()
    
    def test_request_data(self):
        with hymnalnetapi.app.test_request_context('/hymn?hymn_type=h&hymn_number=1331'):
            assert_equal(flask.request.path, '/hymn')
            assert_equal(flask.request.args['hymn_type'], 'h')
            assert_equal(flask.request.args['hymn_number'], '1331')

    def test_get_meta_data_object(self):
        meta_data_object = GetSong.get_meta_data_object('test_name', 'test_data')
        assert_equal(meta_data_object[GetSong.NAME], 'test_name')
        assert_equal(meta_data_object[GetSong.DATA], 'test_data')

    def test_create_verse(self):
        stanza_num = 'test_stanza_num'
        stanza_content = 'test_stanza_content'
        
        # regular stanza number
        verse = GetSong.create_verse(stanza_num, stanza_content)
        assert_equal(verse[GetSong.VERSE_TYPE], GetSong.VERSE)
        assert_equal(verse[GetSong.VERSE_CONTENT], stanza_content)

        # chorus
        verse = GetSong.create_verse('Chorus', stanza_content)
        assert_equal(verse[GetSong.VERSE_TYPE], GetSong.CHORUS)
        assert_equal(verse[GetSong.VERSE_CONTENT], stanza_content)
    
    # test the negative cases that return Bad request
    def test_get_hymn_negative(self):
        rv = self.app.get('/hymn')
        assert rv.status_code == 400
        assert 'Request is missing argument: hymn_type' in rv.get_data(as_text=True)
        rv = self.app.get('/hymn?hymn_type=h')
        assert rv.status_code == 400
        assert 'Request is missing argument: hymn_number' in rv.get_data(as_text=True)
        rv = self.app.get('/hymn?hymn_type=h&hymn_number=2000&&check_exists=true')
        assert rv.status_code == 400
        assert 'Song h 2000 is not a real song' in rv.get_data(as_text=True)
        rv = self.app.get('/hymn?hymn_type=h&hymn_number=1151p&&check_exists=true')
        assert rv.status_code == 400
        assert 'Song h 1151p is not a real song' in rv.get_data(as_text=True)

    # test classical hymn 1331
    def test_h_1331(self):
        self.assert_mock_get_hymn('h', '1331')
        self.assert_get_hymn('h', '1331')

    # test classical hymn 19 -- contains copyright
    def test_h_19(self):
        self.assert_mock_get_hymn('h', '19')
        self.assert_get_hymn('h', '19')

    # test new song 157 (multiple scripture links)
    def test_ns_157(self):
        self.assert_mock_get_hymn('ns', '157')
        self.assert_get_hymn('ns', '157')

    # test classical hymn 17 (goes to external website)
    def test_h_17(self):
        # need to hard code url to external site
        self.assert_mock_get_hymn('h', '17', external_url = 'http://www.witness-lee-hymns.org/hymns/H0017.html', external_data = 'test_data/get_song_html_h_17_external.txt')
        self.assert_get_hymn('h', '17')

    # test classical hymn 10 (goes to external website but starts with '<table width=400 border=0>' instead of '<table width=500>'
    def test_h_10(self):
        # need to hard code url to external site
        self.assert_mock_get_hymn('h', '10', external_url = 'http://www.witness-lee-hymns.org/hymns/H0010.html', external_data = 'test_data/get_song_html_h_10_external.txt')
        self.assert_get_hymn('h', '10')

    # test classical hymn 1197 (multiple choruses)
    def test_h_1197(self):
        self.assert_mock_get_hymn('h', '1197')
        self.assert_get_hymn('h', '1197')

    # test song that is in the form /en/hymn/ns/6i (for Indonesian)
    def test_ns_6i(self):
        self.assert_mock_get_hymn('ns', '6i')
        self.assert_get_hymn('ns', '6i')

    # test song that is in the form /en/hymn/ch/7?gb=1&query=2 (for Indonesian)
    def test_ch_7_query_param(self):
        self.assert_mock_get_hymn('ch', '7', query_params=(('gb', '1'), ('query', '2')))
        self.assert_get_hymn('ch', '7', query_params=(('gb', '1'), ('query', '2')))

    def assert_mock_get_hymn(self, hymn_type, hymn_number, external_url = None, external_data = None, query_params = tuple()):
        stubbed_path = GetSong.HYMN_PATH_FORMAT % (hymn_type, hymn_number)

        # url to stub out
        url = GetSong.GET_SONG_URL_FORMAT % stubbed_path
        stubbed_url = Utils.add_query_to_url(url, query_params)
        
        # mock out hymnal.net response
        # https://docs.python.org/3/library/unittest.mock.html
        mock_response = Mock()
        mock_data_format = Utils.add_query_to_url('test_data/get_song_html_{}_{}', query_params)
        mock_data_format += '.txt'
        
        mock_response.text = open(mock_data_format.format(hymn_type, hymn_number), 'r').read()

        # key order doesn't matter for dict equality, so compare query parameter dicts
        def get_url(url):
            parsed_url = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qsl(parsed_url.query)
            assert_equal(dict(query_params), dict(params))
            if parsed_url.geturl() == external_url:
                return external_mock
            elif parsed_url.geturl() == stubbed_url:
                return mock_response
        
        # http://stackoverflow.com/questions/15753390/python-mock-requests-and-the-response
        # http://mock.readthedocs.org/en/latest/patch.html
        external_mock = Mock()
        if (external_url):
            external_mock.text = open(external_data.format(hymn_type, hymn_number), 'r').read()
            patcher = patch('requests.get', Mock(side_effect=get_url))
        else :
            patcher = patch('requests.get', Mock(side_effect=get_url))
        
        # start patcher, do assertions, then stop patcher
        patcher.start()
        self.assert_get_hymn(hymn_type, hymn_number, query_params)
        patcher.stop()

    def assert_get_hymn(self, hymn_type, hymn_number, query_params = tuple()):
        # checks that two meta data objects are equal
        def check_meta_data(expected, actual):
            assert_equal(len(expected), len(actual))
            for i in range(len(expected)):
                assert_equal(expected[i]['name'], actual[i]['name'])
                # don't check value of 'See Also' field because it changes every request
                if expected[i]['name'] == 'See Also':
                    continue
                else:
                    assert_equal(expected[i]['data'], actual[i]['data'])
        # checks that two lyrics objects are equal
        def check_lyrics(expected, actual):
            assert_equal(len(expected), len(actual))
            for i in range(len(expected)):
                assert_equal(expected[i]['verse_type'], actual[i]['verse_type'])
                assert_equal(expected[i]['verse_content'], actual[i]['verse_content'])
                if 'transliteration' in expected[i]:
                    assert_equal(expected[i]['transliteration'], actual[i]['transliteration'])

        # open saved test data
        expected_result_path = Utils.add_query_to_url('test_data/get_song_{}_{}'.format(hymn_type,hymn_number), query_params)
        expected_result_path += '.txt'
        expected_result = json.loads(open(expected_result_path, 'r').read())
        # make request to get hymn
        query_params = (('hymn_type', hymn_type), ('hymn_number', hymn_number)) + query_params
        path = Utils.add_query_to_url('hymn', query_params)
        rv = self.app.get(path)
        actual_result = json.loads(rv.get_data(as_text=True))
        # assert that components are equal
        assert_equal(expected_result['title'], actual_result['title'])
        check_meta_data(expected_result['meta_data'], actual_result['meta_data'])
        check_lyrics(expected_result['lyrics'], actual_result['lyrics'])

if __name__ == '__main__':
    unittest.main()
