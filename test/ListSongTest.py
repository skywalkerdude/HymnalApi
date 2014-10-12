import hymnalnetapi, unittest, ListSong, flask, json
from mock import create_autospec
from nose.tools import assert_equal

class FlaskrTestCase(unittest.TestCase):
    
    def setUp(self):
        hymnalnetapi.app.config['TESTING'] = True
        self.app = hymnalnetapi.app.test_client()
    
    def test_request_data(self):
        with hymnalnetapi.app.test_request_context('/list?song_type=lb&letter=g&page_num=4&testament=ot'):
            assert_equal(flask.request.path, '/list')
            assert_equal(flask.request.args['song_type'], 'lb')
            assert_equal(flask.request.args['letter'], 'g')
            assert_equal(flask.request.args['page_num'], '4')
            assert_equal(flask.request.args['testament'], 'ot')
    
    # test the negative cases that return Bad request
    def test_list_song_negative(self):
        rv = self.app.get('/list')
        assert rv.status_code == 400
        assert 'Request is missing argument: song_type' in rv.data
        rv = self.app.get('/list?song_type=h')
        assert rv.status_code == 400
        assert 'Request is missing argument: letter' in rv.data
        rv = self.app.get('/list?song_type=h&letter=g')
        assert rv.status_code == 400
        assert 'Request is missing argument: page_num' in rv.data
        rv = self.app.get('/list?song_type=scripture&letter=g&page_num=3')
        assert rv.status_code == 400
        assert 'Request is missing argument: testament' in rv.data

    # test listing classical hymns
    def test_list_h(self):
        self.assert_classical_hymn('g', 3)

    # test listing new songs
    def test_list_ns(self):
        self.assert_new_song('g', 2)
        self.assert_new_song('g', 3)

    # test listing new tunes
    def test_list_nt(self):
        self.assert_new_tune(4)
        self.assert_new_tune(5)
        self.assert_new_tune(6)
    
    # test listing scripture songs
    def test_list_scripture(self):
        self.assert_scripture_song('ot')
        self.assert_scripture_song('nt')

    def assert_classical_hymn(self, letter, page_num):
        self.assert_list_results(song_type='h', letter=letter, page_num=page_num)
    
    def assert_new_song(self, letter, page_num):
        self.assert_list_results(song_type='ns', letter=letter, page_num=page_num)

    def assert_new_tune(self, page_num):
        self.assert_list_results(song_type='nt', page_num=page_num)
    
    def assert_scripture_song(self, testament):
        self.assert_list_results(song_type='scripture', testament=testament)

    def assert_list_results(self, song_type, letter = None, page_num=None, testament = None):
        if song_type == 'h' or song_type == 'ns':
            # make request to get hymn from hymnal.net
            rv = self.app.get('list?song_type={}&letter={}&page_num={}'.format(song_type, letter, page_num))
            actual_result = json.loads(rv.data)
            # open saved test data
            expected_result = json.loads(open('test_data/list_song_{}_{}_{}.txt'.format(song_type, letter, page_num), 'r').read())

        elif song_type == 'nt':
            # make request to get hymn from hymnal.net
            rv = self.app.get('list?song_type={}&page_num={}'.format(song_type, page_num))
            actual_result = json.loads(rv.data)
            # open saved test data
            expected_result = json.loads(open('test_data/list_song_{}_{}.txt'.format(song_type, page_num), 'r').read())

        elif song_type == 'scripture':
            # make request to get hymn from hymnal.net
            rv = self.app.get('list?song_type={}&testament={}'.format(song_type, testament))
            actual_result = json.loads(rv.data)
            # open saved test data
            expected_result = json.loads(open('test_data/list_song_{}_{}.txt'.format(song_type, testament), 'r').read())

        assert_equal(actual_result, expected_result)

if __name__ == '__main__':
    unittest.main()