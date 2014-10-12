import sys
# append src to path so it can find the source code
sys.path.append('..')

import glob
import unittest

# Need to install nose to run tests: https://nose.readthedocs.org/en/latest/

test_file_strings = glob.glob('*Test.py')
module_strings = [str[0:len(str)-3] for str in test_file_strings]
suites = [unittest.defaultTestLoader.loadTestsFromName(str) for str
          in module_strings]
testSuite = unittest.TestSuite(suites)
text_runner = unittest.TextTestRunner().run(testSuite)