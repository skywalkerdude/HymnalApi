import unittest, pdb, Utils, mock
from bs4 import BeautifulSoup
from mock import PropertyMock
from mock import patch
from mock import create_autospec

import os, requests, re, simplejson as json

def method_under_test():
    r = Beauti
    
    print r.ok # prints "<MagicMock name='post().ok' id='11111111'>"
    
    if r.ok:
        return "YEAH!"
    else:
        raise Exception()

class MethodUnderTestTest(unittest.TestCase):
    
    def test_method_under_test(self):
        with patch('requests.post') as patched_post:
            patched_post.return_value.ok = True
            
            result = method_under_test()
            
            print 'result: %s' % result

if __name__ == '__main__':
    unittest.main()