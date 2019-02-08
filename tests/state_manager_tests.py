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
import pathlib
import unittest
import json

from PyQt5 import QtWidgets
from PyQt5.QtTest import QSignalSpy

from registered_test_cases import Meta
from config import config
from util.py_qml_glue import StateManager


class DownloadManagerTests(unittest.TestCase, metaclass=Meta):
    def setUp(self):
        self.image_net_home = os.path.join('temp', 'imageNetHome')
        os.makedirs(self.image_net_home, exist_ok=True)
        self.app = QtWidgets.QApplication(sys.argv)

        self.manager = StateManager()

        self.download_state = self.manager.download_state
        self.state_data = None

        def on_changed():
            self.download_state = self.manager.download_state
            self.state_data = json.loads(self.manager.state_data_json)

        self.manager.stateChanged.connect(on_changed)

    def test_starts_in_initial_state(self):
        self.assertEqual(self.manager.download_state, 'initial')

    def test_configure_without_destination(self):
        self.manager.configure('', 9, 30)

        self.assertEqual(self.download_state, 'initial')

        self.assertEqual(
            self.state_data['errors'],
            ['Destination folder for ImageNet was not specified']
        )

    def test_configure_with_non_existent_destination(self):
        abs_path = os.path.join('/non-existent','path')
        path = pathlib.Path(abs_path).as_uri()
        self.manager.configure(path, 0, 30)
        self.assertEqual(self.download_state, 'initial')

        self.assertEqual(
            self.state_data['errors'],
            ['Path "{}" does not exist'.format(abs_path),
             'Number of images must be greater than 0']
        )

    def test_configure_with_invalid_integer_parameters(self):
        self.manager.configure('', 0, 0)
        self.assertEqual(self.download_state, 'initial')

        self.assertEqual(
            self.state_data['errors'],
            ['Destination folder for ImageNet was not specified',
             'Number of images must be greater than 0',
             'Images per category must be greater than 0']
        )

    def test_with_bad_parameters_twice(self):
        self.manager.configure('', 0, 0)
        self.assertEqual(self.download_state, 'initial')

        self.manager.configure('', 0, 10)
        self.assertEqual(self.download_state, 'initial')

    def test_with_valid_configuration(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()

        self.manager.configure(path_uri, 10, 30)

        self.assertEqual(self.download_state, 'ready')

    def test_start_in_initial_state_does_nothing(self):
        self.manager.start_download()

        self.assertEqual(self.download_state, 'initial')

    def test_pause_in_initial_state(self):
        self.manager.pause()

        self.assertEqual(self.download_state, 'initial')

    def test_resume_in_initial_state(self):
        self.manager.resume()

        self.assertEqual(self.download_state, 'initial')

    def test_start_in_ready_state(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()
        self.manager.configure(path_uri, 10, 30)
        self.manager.start_download()

        self.assertEqual(self.download_state, 'running')

    def test_pause_in_ready_state(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()
        self.manager.configure(path_uri, 10, 30)
        self.manager.pause()
        self.assertEqual(self.download_state, 'ready')

    def test_resume_in_ready_state(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()
        self.manager.configure(path_uri, 10, 30)
        self.manager.pause()
        self.assertEqual(self.download_state, 'ready')

    def test_pause_in_running_state(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()
        self.manager.configure(path_uri, 10, 30)
        self.manager.start_download()
        self.manager.pause()
        self.assertEqual(self.download_state, 'pausing')

    def test_resume_in_running_state_does_nothing(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()
        self.manager.configure(path_uri, 10, 30)
        self.manager.start_download()
        self.manager.resume()
        self.assertEqual(self.download_state, 'running')

    def test_start_download_in_running_state_does_nothing(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()
        self.manager.configure(path_uri, 10, 30)
        self.manager.start_download()
        self.manager.start_download()
        self.assertEqual(self.download_state, 'running')

    def test_configure_in_running_state_does_nothing(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()
        self.manager.configure(path_uri, 10, 30)
        self.manager.start_download()
        self.manager.configure('', 10, 0)
        self.assertEqual(self.download_state, 'running')

    def test_reset_in_running_state_does_nothing(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()
        self.manager.configure(path_uri, 10, 30)
        self.manager.start_download()
        self.manager.reset()
        self.assertEqual(self.download_state, 'running')

    def test_no_action_can_be_made_during_pausing(self):
        path_uri = pathlib.Path(os.path.abspath(self.image_net_home)).as_uri()
        self.manager.configure(path_uri, 10, 30)
        self.manager.start_download()
        self.manager.pause()
        self.assertEqual(self.download_state, 'pausing')

        self.manager.configure(path_uri, 10, 30)
        self.assertEqual(self.download_state, 'pausing')

        self.manager.start_download()
        self.assertEqual(self.download_state, 'pausing')

        self.manager.pause()
        self.assertEqual(self.download_state, 'pausing')

        self.manager.resume()
        self.assertEqual(self.download_state, 'pausing')

        self.manager.reset()
        self.assertEqual(self.download_state, 'pausing')

    def test_resume_in_paused_state(self):
        self.manager._state = 'paused'
        self.manager.resume()
        self.assertEqual(self.download_state, 'running')

    def test_reset_while_paused(self):
        self.manager._state = 'paused'
        self.download_state = 'paused'
        self.manager.reset()
        self.assertEqual(self.download_state, 'initial')

    def test_configure_in_paused_state(self):
        self.manager._state = 'paused'
        self.download_state = 'paused'
        self.manager.configure('', 10,  -10)
        self.assertEqual(self.download_state, 'paused')

    def test_start_while_paused(self):
        self.manager._state = 'paused'
        self.download_state = 'paused'
        self.manager.start_download()
        self.assertEqual(self.download_state, 'paused')

    def test_pause_while_paused(self):
        self.manager._state = 'paused'
        self.download_state = 'paused'
        self.manager.pause()
        self.assertEqual(self.download_state, 'paused')

    def test_reset_after_finishing(self):
        self.manager._state = 'finished'
        self.download_state = 'finished'
        self.manager.reset()
        self.assertEqual(self.download_state, 'initial')
