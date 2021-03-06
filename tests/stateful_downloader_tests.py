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
import unittest

from registered_test_cases import Meta
from image_net import stateful_downloader
from config import config
from image_net.stateful_downloader import StatefulDownloader
from util.app_state import DownloadConfiguration, AppState


class StatefulDownloaderTests(unittest.TestCase, metaclass=Meta):
    def setUp(self):
        path = config.download_state_path
        if os.path.isfile(path):
            os.remove(path)

        if os.path.exists(config.app_data_folder):
            shutil.rmtree(config.app_data_folder)
        os.makedirs(config.app_data_folder)

        image_net_home = os.path.join('temp', 'image_net_home')
        if os.path.exists(image_net_home):
            shutil.rmtree(image_net_home)
        os.makedirs(image_net_home)
        self.image_net_home = image_net_home

    def test_complete_download_from_scratch(self):
        app_state = AppState()

        dconf = DownloadConfiguration(number_of_images=10,
                                      images_per_category=10,
                                      download_destination=self.image_net_home)
        app_state.set_configuration(dconf)
        downloader = StatefulDownloader(app_state)

        results = []
        failed_urls = []
        successful_urls = []
        for result in downloader:
            results.append(result)
            failed_urls.extend(result.failed_urls)
            successful_urls.extend(result.succeeded_urls)

        self.assertEqual(failed_urls, [])
        self.assertEqual(successful_urls, ['url1', 'url2', 'url3', 'url4', 'url5'])

        self.assertEqual(downloader.progress_info.total_downloaded, 5)
        self.assertEqual(downloader.progress_info.total_failed, 0)

        self.assertTrue(downloader.progress_info.finished)

    def test_without_configuring(self):
        def f():
            app_state = AppState()

            d = StatefulDownloader(app_state)

            for result in d:
                pass

        self.assertRaises(stateful_downloader.NotConfiguredError, f)

    def test_stopping_and_resuming_with_new_instance(self):
        app_state = AppState()

        dconf = DownloadConfiguration(number_of_images=10,
                                      images_per_category=12,
                                      batch_size=3,
                                      download_destination=self.image_net_home)
        app_state.set_configuration(dconf)
        downloader = StatefulDownloader(app_state)

        for result in downloader:
            break

        app_state = AppState()
        downloader = StatefulDownloader(app_state)

        failed_urls = []
        successful_urls = []
        for result in downloader:
            failed_urls.extend(result.failed_urls)
            successful_urls.extend(result.succeeded_urls)
            break

        self.assertEqual(failed_urls, [])
        self.assertEqual(successful_urls, ['url4', 'url5'])

        self.assertEqual(downloader.progress_info.total_downloaded, 5)
        self.assertEqual(downloader.progress_info.total_failed, 0)

        self.assertTrue(downloader.progress_info.finished)

    def test_creates_files_as_expected(self):
        app_state = AppState()

        dconf = DownloadConfiguration(number_of_images=4,
                                      images_per_category=1,
                                      batch_size=2,
                                      download_destination=self.image_net_home)
        app_state.set_configuration(dconf)
        downloader = StatefulDownloader(app_state)

        for result in downloader:
            break

        app_state = AppState()

        downloader = StatefulDownloader(app_state)
        for result in downloader:
            pass

        fnames = []
        for dirname, dirs, file_names in os.walk(self.image_net_home):
            fnames.extend(file_names)

        expected_names = ['1', '2', '3', '4']

        self.assertEqual(set(fnames), set(expected_names))

    def test_remembers_number_of_images_downloaded_for_each_category(self):
        app_state = AppState()

        dconf = DownloadConfiguration(number_of_images=4,
                                      images_per_category=1,
                                      batch_size=2,
                                      download_destination=self.image_net_home)

        app_state.set_configuration(dconf)
        downloader = StatefulDownloader(app_state)

        for result in downloader:
            break

        app_state = AppState()

        downloader = StatefulDownloader(app_state)

        failed_urls = []
        successful_urls = []
        for result in downloader:
            failed_urls.extend(result.failed_urls)
            successful_urls.extend(result.succeeded_urls)
            break

        self.assertEqual(failed_urls, [])
        self.assertEqual(successful_urls, ['url4', 'url5'])

        self.assertEqual(downloader.progress_info.total_downloaded, 4)
        self.assertEqual(downloader.progress_info.total_failed, 0)

        self.assertTrue(downloader.progress_info.finished)

    def test_reconfiguration(self):
        app_state = AppState()

        dconf = DownloadConfiguration(number_of_images=4,
                                      images_per_category=1,
                                      batch_size=2,
                                      download_destination=self.image_net_home)
        app_state.set_configuration(dconf)
        downloader = StatefulDownloader(app_state)

        for result in downloader:
            break

        shutil.rmtree(self.image_net_home)
        os.makedirs(self.image_net_home)

        app_state = AppState()

        downloader = StatefulDownloader(app_state)
        dconf = DownloadConfiguration(number_of_images=2,
                                      images_per_category=2,
                                      batch_size=2,
                                      download_destination=self.image_net_home)

        app_state.set_configuration(dconf)

        failed_urls = []
        successful_urls = []
        for result in downloader:
            failed_urls.extend(result.failed_urls)
            successful_urls.extend(result.succeeded_urls)
            break

        self.assertEqual(successful_urls, ['url1', 'url2'])

        self.assertEqual(downloader.progress_info.total_downloaded, 2)
        self.assertEqual(downloader.progress_info.total_failed, 0)

        fnames = []
        for dirname, dirs, file_names in os.walk(self.image_net_home):
            fnames.extend(file_names)

        expected_names = ['1', '2']

        self.assertEqual(set(fnames), set(expected_names))
