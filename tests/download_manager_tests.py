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

from PyQt5 import QtWidgets
from PyQt5.QtTest import QSignalSpy

from registered_test_cases import Meta
from config import config
from util.download_manager import DownloadManager
from util.app_state import AppState, DownloadConfiguration


class DownloadManagerTests(unittest.TestCase, metaclass=Meta):
    def setUp(self):
        if os.path.exists(config.app_data_folder):
            shutil.rmtree(config.app_data_folder)

        image_net_home = os.path.join('temp', 'image_net_home')
        if os.path.exists(image_net_home):
            shutil.rmtree(image_net_home)
        os.makedirs(image_net_home)

        self.image_net_home = image_net_home
        self.app = QtWidgets.QApplication(sys.argv)

    def test_imagesLoaded_gets_emitted(self):
        self._assert_signal_emitted('imagesLoaded')

    def test_downloadFailed_gets_emitted(self):
        self._assert_signal_emitted('downloadFailed')

    def test_allDownloaded_gets_emitted(self):
        self._assert_signal_emitted('allDownloaded')

    def _assert_signal_emitted(self, signal):
        app_state = AppState()
        manager = DownloadManager(app_state)

        conf = DownloadConfiguration(number_of_images=5,
                                     images_per_category=10,
                                     download_destination=self.image_net_home)
        app_state.set_configuration(conf)
        signal = getattr(manager, signal)
        spy = QSignalSpy(signal)
        manager.start()
        received = spy.wait(timeout=500)
        self.assertTrue(received)

        self.stop_the_thread(manager)

    def test_folders_are_created(self):
        app_state = AppState()
        manager = DownloadManager(app_state)
        conf = DownloadConfiguration(number_of_images=5,
                                     images_per_category=10,
                                     download_destination=self.image_net_home)

        app_state.set_configuration(conf)

        self.wait_for_completion(manager)
        self._assert_expected_directories_exist()
        self.stop_the_thread(manager)

    def test_files_are_downloaded(self):
        app_state = AppState()
        manager = DownloadManager(app_state)

        conf = DownloadConfiguration(number_of_images=5,
                                     images_per_category=10,
                                     download_destination=self.image_net_home)

        app_state.set_configuration(conf)

        self.wait_for_completion(manager)
        self._assert_files_are_correct()
        self.stop_the_thread(manager)

    def test_case_when_requested_number_of_images_is_greater_than_total(self):
        app_state = AppState()
        manager = DownloadManager(app_state)

        conf = DownloadConfiguration(number_of_images=50,
                                     images_per_category=100,
                                     download_destination=self.image_net_home)

        app_state.set_configuration(conf)

        self.wait_for_completion(manager)
        self._assert_files_are_correct()
        self.stop_the_thread(manager)

    def test_images_per_category_argument(self):
        app_state = AppState()
        manager = DownloadManager(app_state)

        conf = DownloadConfiguration(number_of_images=5,
                                     images_per_category=1,
                                     download_destination=self.image_net_home,
                                     batch_size=1)

        app_state.set_configuration(conf)

        self.wait_for_completion(manager)

        files_count = 0
        for dirname, dirs, file_names in os.walk(self.image_net_home):
            files_count += len(file_names)
        self.assertEqual(files_count, 2)

        self.stop_the_thread(manager)

    def test_start_pause_and_resume(self):
        app_state = AppState()

        manager = DownloadManager(app_state)

        conf = DownloadConfiguration(number_of_images=5,
                                     images_per_category=1,
                                     download_destination=self.image_net_home)

        app_state.set_configuration(conf)

        paused_spy = QSignalSpy(manager.downloadPaused)
        resumed_spy = QSignalSpy(manager.downloadResumed)
        finished_spy = QSignalSpy(manager.allDownloaded)

        manager.start()
        manager.pause_download()
        received = paused_spy.wait(timeout=500)
        self.assertTrue(received)

        time.sleep(0.5)

        manager.resume_download()

        received = finished_spy.wait(timeout=500)
        self.assertTrue(received)

        self._assert_expected_directories_exist()
        self._assert_files_are_correct()

        self.stop_the_thread(manager)

    def _assert_expected_directories_exist(self):
        word_net_directories = []
        for dirname, dirs, file_names in os.walk(self.image_net_home):
            word_net_directories.extend(dirs)

        self.assertEqual(word_net_directories, ['n38203', 'n392093'])

    def _assert_files_are_correct(self):
        file_paths = []
        for dirname, dirs, file_names in os.walk(self.image_net_home):
            paths = [os.path.join(dirname, fname)
                     for fname in file_names]
            file_paths.extend(paths)

        for path in file_paths:
            with open(path, 'r') as f:
                s = f.read()
                self.assertEqual(s, 'Dummy downloader written file')

    def wait_for_completion(self, manager):
        spy = QSignalSpy(manager.allDownloaded)
        self.assertTrue(spy.isValid())
        manager.start()

        received = spy.wait(timeout=500)
        self.assertTrue(received)

    def stop_the_thread(self, manager):
        try:
            manager.terminate()
            manager.wait()
        except:
            pass
