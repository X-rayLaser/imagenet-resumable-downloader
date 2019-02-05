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

        self.app = QtWidgets.QApplication(sys.argv)

        image_net_home = os.path.join('temp', 'image_net_home')
        if os.path.exists(image_net_home):
            shutil.rmtree(image_net_home)
        os.makedirs(image_net_home)
        self.image_net_home = image_net_home

    def test_initial_state(self):
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

    def test_configure_changes_parameters(self):
        worker = Worker()
        worker.configure(destination=self.image_net_home,
                         number_of_images=10,
                         images_per_category=5)
        state_data = json.loads(worker.state_data_json)

        expected_path = os.path.abspath(self.image_net_home)
        self.assertEqual(state_data['downloadPath'], expected_path)
        self.assertEqual(state_data['numberOfImages'], 10)
        self.assertEqual(state_data['imagesPerCategory'], 5)
        self.assertEqual(state_data['timeLeft'], 'Eternity')
        self.assertEqual(state_data['imagesLoaded'], 0)
        self.assertEqual(state_data['failures'], 0)
        self.assertEqual(state_data['failedUrls'], [])
        self.assertEqual(state_data['progress'], 0)

        self.assertEqual(worker.download_state, 'ready')

    def test_destination_path_validation(self):
        worker = Worker()
        dest = os.path.join('hello', 'world', 'folder')
        worker.configure(destination=dest,
                         number_of_images=10,
                         images_per_category=5)

        state_data = json.loads(worker.state_data_json)
        self.assertEqual(state_data['downloadPath'], '')
        self.assertEqual(worker.download_state, 'initial')

    def test_number_of_images_validation(self):
        worker = Worker()
        worker.configure(destination=self.image_net_home,
                         number_of_images=-1,
                         images_per_category=5)

        state_data = json.loads(worker.state_data_json)
        self.assertEqual(state_data['numberOfImages'], 100)
        self.assertEqual(worker.download_state, 'initial')

        worker.configure(destination=self.image_net_home,
                         number_of_images=0,
                         images_per_category=5)

        self.assertEqual(state_data['numberOfImages'], 100)
        self.assertEqual(worker.download_state, 'initial')

    def test_images_per_category_validation(self):
        worker = Worker()
        worker.configure(destination=self.image_net_home,
                         number_of_images=10,
                         images_per_category=-1)

        state_data = json.loads(worker.state_data_json)
        self.assertEqual(state_data['imagesPerCategory'], 90)
        self.assertEqual(worker.download_state, 'initial')

        worker.configure(destination=self.image_net_home,
                         number_of_images=10,
                         images_per_category=0)

        self.assertEqual(state_data['imagesPerCategory'], 90)
        self.assertEqual(worker.download_state, 'initial')

    def test_wait_until_download_complete(self):
        worker = Worker()
        worker.configure(destination=self.image_net_home,
                         number_of_images=10,
                         images_per_category=5)

        change_spy = QSignalSpy(worker.stateChanged)
        worker.start_download()

        while not worker.complete:
            received = change_spy.wait(500)

        self.assertEqual(worker.download_state, 'finished')
        self.assertTrue(worker.complete)

    def test_finished_state(self):
        worker = Worker()
        worker.configure(destination=self.image_net_home,
                         number_of_images=5,
                         images_per_category=10)

        change_spy = QSignalSpy(worker.stateChanged)
        worker.start_download()

        while not worker.complete:
            received = change_spy.wait(500)

        worker = Worker()

        self.assertEqual(worker.download_state, 'finished')
        self.assertTrue(worker.complete)

        worker = Worker()
        expected_path = os.path.abspath(self.image_net_home)

        state_data = json.loads(worker.state_data_json)
        self.assertEqual(state_data['downloadPath'], expected_path)
        self.assertEqual(state_data['numberOfImages'], 5)
        self.assertEqual(state_data['imagesPerCategory'], 10)
        self.assertEqual(state_data['timeLeft'], '0 seconds')
        self.assertEqual(state_data['imagesLoaded'], 5)
        self.assertEqual(state_data['failures'], 0)
        self.assertEqual(state_data['failedUrls'], [])
        self.assertEqual(state_data['progress'], 1.0)
