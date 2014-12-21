import hymnalnetapi, unittest, GetSong, flask, json
from mock import create_autospec, patch, Mock
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
        assert 'Request is missing argument: hymn_type' in rv.data
        rv = self.app.get('/hymn?hymn_type=h')
        assert rv.status_code == 400
        assert 'Request is missing argument: hymn_number' in rv.data

    # test classical hymn 1131
    def test_h_1131(self):
        self.assert_mock_get_hymn('h', '1331')
        self.assert_get_hymn('h', '1331')
    
    # test new song 157 (multiple scripture links)
    def test_ns_157(self):
        self.assert_mock_get_hymn('ns', '157')
        self.assert_get_hymn('ns', '157')

    # test classical hymn 17 (goes to external website)
    def test_h_17(self):
        # need to hard code url to external site
        self.assert_mock_get_hymn('h', '17', external_url = 'http://www.witness-lee-hymns.org/hymns/H0017.html', external_data = 'test_data/get_song_html_h_17_external.txt')
        self.assert_get_hymn('h', '17')

    # test classical hymn 1197 (multiple choruses)
    def test_h_1197(self):
        self.assert_mock_get_hymn('h', '1197')
        self.assert_get_hymn('h', '1197')
    
    def assert_mock_get_hymn(self, hymn_type, hymn_number, external_url = None, external_data = None):
        # url to stub out
        path = GetSong.HYMN_PATH_FORMAT % (hymn_type, int(hymn_number))
        url = GetSong.GET_SONG_URL_FORMAT % path
        # mock out hymnal.net response
        # https://docs.python.org/3/library/unittest.mock.html
        mock_response = Mock()
        mock_response.content = open('test_data/get_song_html_{}_{}.txt'.format(hymn_type, hymn_number), 'r').read()
        
        # http://stackoverflow.com/questions/15753390/python-mock-requests-and-the-response
        # http://mock.readthedocs.org/en/latest/patch.html
        if (external_url):
            external_mock = Mock()
            external_mock.content = open(external_data.format(hymn_type, hymn_number), 'r').read()
            patcher = patch('requests.get', Mock(side_effect = lambda k:{url: mock_response, external_url: external_mock}.get(k, 'unhandled request %s' % k)))
        else :
            patcher = patch('requests.get', Mock(side_effect = lambda k:{url: mock_response}.get(k, 'unhandled request %s' % k)))
        
        # start patcher, do assertions, then stop patcher
        patcher.start()
        self.assert_get_hymn(hymn_type, hymn_number)
        patcher.stop()

    def assert_get_hymn(self, hymn_type, hymn_number):
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

        # make request to get hymn
        rv = self.app.get('hymn?hymn_type={}&hymn_number={}'.format(hymn_type, hymn_number))
        actual_result = json.loads(rv.data)
        # open saved test data
        expected_result = json.loads(open('test_data/get_song_{}_{}.txt'.format(hymn_type, hymn_number), 'r').read())
        # assert that components are equal
        assert_equal(expected_result['title'], actual_result['title'])
        check_meta_data(expected_result['meta_data'], actual_result['meta_data'])
        check_lyrics(expected_result['lyrics'], actual_result['lyrics'])

if __name__ == '__main__':
    unittest.main()