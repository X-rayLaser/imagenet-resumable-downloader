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
import os
import shutil
import sys
import time
import unittest
import json

from PyQt5 import QtWidgets
from PyQt5.QtTest import QSignalSpy

from registered_test_cases import Meta
from config import config
from util.py_qml_glue import Worker


class WorkerTests(unittest.TestCase, metaclass=Meta):
    def setUp(self):
        if os.path.exists(config.app_data_folder):
            shutil.rmtree(config.app_data_folder)

    def test_initial_state(self):
        self.app = QtWidgets.QApplication(sys.argv)

        worker = Worker()
        state_data = json.loads(worker.state_data_json)

        self.assertEqual(worker.download_state, 'initial')

        self.assertEqual(state_data['downloadPath'], '')
        self.assertEqual(state_data['numberOfImages'], 100)
        self.assertEqual(state_data['imagesPerCategory'], 90)
        self.assertEqual(state_data['timeLeft'], 'Eternity')
        self.assertEqual(state_data['imagesLoaded'], 0)
        self.assertEqual(state_data['failures'], 0)
        self.assertEqual(state_data['failedUrls'], [])
        self.assertEqual(state_data['progress'], 0)
