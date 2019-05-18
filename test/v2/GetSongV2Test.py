import sys; sys.path.append('..')
import hymnalnetapi, unittest, GetSong, flask, json, urllib, Utils
from unittest.mock import create_autospec, patch, MagicMock as Mock
from nose.tools import assert_equal, assert_false

class FlaskrTestCase(unittest.TestCase):
    
    def setUp(self):
        hymnalnetapi.app.config['TESTING'] = True
        self.app = hymnalnetapi.app.test_client()
    
    def test_request_data(self):
        with hymnalnetapi.app.test_request_context('/v2/hymn/h/1331'):
            assert_equal(flask.request.path, '/v2/hymn/h/1331')
    def test_request_data_check_exists(self):
        with hymnalnetapi.app.test_request_context('/v2/hymn/h/1331?check_exists=true'):
            assert_equal(flask.request.path, '/v2/hymn/h/1331')
            assert_equal(flask.request.args['check_exists'], 'true')
    def test_request_data_other_params(self):
        with hymnalnetapi.app.test_request_context('/v2/hymn/h/1331?a=b&c=d'):
            assert_equal(flask.request.path, '/v2/hymn/h/1331')
            assert_equal(flask.request.args['a'], 'b')
            assert_equal(flask.request.args['c'], 'd')

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
        rv = self.app.get('/v2/hymn/')
        assert rv.status_code == 404
    def test_get_hymn_negative(self):
        rv = self.app.get('/v2/hymn/h/')
        assert rv.status_code == 404

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

    # test new song 487 (single-verse song)
    def test_h_487(self):
        self.assert_mock_get_hymn('h', '487', stored_content_path = 'stored/classic/487.html')
        self.assert_get_hymn('h', '487', stored_content_path = 'stored/classic/487.html')

    # test new song 68 (as a weird grave "e" character)
    def test_h_68(self):
        self.assert_mock_get_hymn('h', '68', stored_content_path = 'stored/classic/68.html')
        self.assert_get_hymn('h', '68', stored_content_path = 'stored/classic/68.html')

    # test classical hymn 17 (goes to external website)
    def test_h_17(self):
        # need to hard code url to external site
        self.assert_mock_get_hymn('h', '17', stored_content_path = 'stored/classic/17.html')
        self.assert_get_hymn('h', '17', stored_content_path = 'stored/classic/17.html')

    # test classical hymn 10 (goes to external website)
    def test_h_10(self):
        # need to hard code url to external site
        self.assert_mock_get_hymn('h', '10', stored_content_path = 'stored/classic/10.html')
        self.assert_get_hymn('h', '10', stored_content_path = 'stored/classic/10.html')

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

    def assert_mock_get_hymn(self, hymn_type, hymn_number, stored_content_path = None, query_params = tuple()):
        stubbed_path = GetSong.HYMN_PATH_FORMAT % (hymn_type, hymn_number)

        # url to stub out
        url = GetSong.GET_SONG_URL_FORMAT % stubbed_path
        stubbed_url = Utils.add_query_to_url(url, query_params)
        
        # mock out hymnal.net response
        # https://docs.python.org/3/library/unittest.mock.html
        mock_response = Mock()
        mock_data_format = Utils.add_query_to_url('test_data/get_song_html_{}_{}', query_params)
        mock_data_format += '.txt'
        
        with open(mock_data_format.format(hymn_type, hymn_number), 'r') as m:
            mock_response.text = m.read()

        # key order doesn't matter for dict equality, so compare query parameter dicts
        def get_url(url):
            parsed_url = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qsl(parsed_url.query)
            assert_equal(dict(query_params), dict(params))
            return mock_response

        # http://stackoverflow.com/questions/15753390/python-mock-requests-and-the-response
        with patch('requests.get', Mock(side_effect=get_url)) as n:
            self.assert_get_hymn(hymn_type, hymn_number, query_params, stored_content_path)

    def assert_get_hymn(self, hymn_type, hymn_number, query_params = tuple(), stored_content_path = None):
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
                else:
                    assert_false('transliteration' in actual[i])

        # open saved test data
        expected_result_path = Utils.add_query_to_url('test_data/get_song_{}_{}'.format(hymn_type,hymn_number), query_params)
        expected_result_path += '.txt'
        with open(expected_result_path, 'r') as e:
            expected_result = json.loads(e.read())
        # make request to get hymn
        path = 'v2/hymn/{}/{}'.format(hymn_type, hymn_number)
        path = Utils.add_query_to_url(path, query_params)

        # store original open method, so we can call it later
        original_open_method = open

        # this method will be called by the app code when it calls the open(...) method
        def mocked_open_method(path, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
            if (path == stored_content_path):
                # if the path is the same as the stored_content_path, then we open it
                return original_open_method('../' + path, mode)
            else:
                # otherwise we just call the original method
                return original_open_method(path, mode)

        if (stored_content_path):
            with patch('builtins.open', Mock(side_effect=mocked_open_method)):
                rv = self.app.get(path)
        else:
            rv = self.app.get(path)
        
        actual_result = json.loads(rv.get_data(as_text=True))
        # assert that components are equal
        assert_equal(expected_result['title'], actual_result['title'])
        check_meta_data(expected_result['meta_data'], actual_result['meta_data'])
        check_lyrics(expected_result['lyrics'], actual_result['lyrics'])

if __name__ == '__main__':
    unittest.main()
