# <imagenet-resumable-downloader - a GUI based utility for getting ImageNet images>
# Copyright © 2019 Evgenii Dolotov. Contacts <supernovaprotocol@gmail.com>
# Author: Evgenii Dolotov
# License: https://www.gnu.org/licenses/gpl-3.0.txt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
