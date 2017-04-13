import hymnalnetapi, unittest, flask
from nose.tools import assert_equal

class FlaskrTestCase(unittest.TestCase):
    
    def setUp(self):
        hymnalnetapi.app.config['TESTING'] = True
        self.app = hymnalnetapi.app.test_client()

    def test_request_data(self):
        with hymnalnetapi.app.test_request_context('/'):
            assert_equal(flask.request.path, '/')
            # assert args is empty
            assert not flask.request.args

    def test_blank_call(self):
        # https://blog.safaribooksonline.com/2013/12/05/flask-with-mock-and-nose/
        rv = self.app.get('/')
        assert_equal(rv.status_code, 200)
        assert 'Welcome to my API' in rv.get_data(as_text=True)


if __name__ == '__main__':
    unittest.main()
