import sys
# append src to path so it can find the source code
# http://stackoverflow.com/questions/4383571/importing-files-from-different-folder-in-python
sys.path.append('..')
sys.path.append('v1')
sys.path.append('v2')

import glob
import unittest

# Need to install nose to run tests: https://nose.readthedocs.org/en/latest/

test_file_strings = glob.glob('**/*Test.py', recursive=True)
# turns 'v1/UtilsTest.py' into 'UtilsTest'
module_strings = [str[3:len(str)-3] for str in test_file_strings]
suites = [unittest.defaultTestLoader.loadTestsFromName(str) for str
          in module_strings]
testSuite = unittest.TestSuite(suites)
text_runner = unittest.TextTestRunner().run(testSuite)
