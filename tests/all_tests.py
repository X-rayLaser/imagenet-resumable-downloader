import unittest
import os
import sys
import registered_test_cases, batch_download_tests, download_manager_tests
import iterator_tests, stateful_downloader_tests, threading_downloader_tests
import util_tests

suite = unittest.TestSuite()


for test_case in registered_test_cases.registry:
    suite.addTest(unittest.makeSuite(test_case))


if __name__ == '__main__':
    os.environ['TEST_ENV'] = 'test environment'
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())
