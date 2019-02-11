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
from util.app_state import AppState, DownloadConfiguration, ProgressInfo, Result, InternalState
from image_net.iterators import Position


class AppStateTests(unittest.TestCase, metaclass=Meta):
    def setUp(self):
        if os.path.exists(config.app_data_folder):
            shutil.rmtree(config.app_data_folder)

    def test_initial_state(self):
        app_state = AppState()
        conf = app_state.download_configuration
        self.assertEqual(conf.download_destination, '')
        self.assertEqual(conf.number_of_images, 100)
        self.assertEqual(conf.images_per_category, 90)

        progress_info = app_state.progress_info
        self.assertEqual(progress_info.total_downloaded, 0)
        self.assertEqual(progress_info.total_failed, 0)
        self.assertEqual(progress_info.finished, False)
        self.assertEqual(progress_info.last_result.failed_urls, [])
        self.assertEqual(progress_info.last_result.succeeded_urls, [])

        internal = app_state.internal_state
        self.assertEqual(internal.iterator_position, Position.null_position())
        self.assertEqual(internal.iterator_position.word_id_offset,
                         Position.null_position().word_id_offset)
        self.assertEqual(internal.iterator_position.url_offset,
                         Position.null_position().url_offset)

        self.assertEqual(internal.category_counts, {})
        self.assertEqual(internal.file_index, 1)

    def test_data_persistence(self):
        app_state = AppState()

        new_conf = DownloadConfiguration(number_of_images=9309,
                                         images_per_category=83,
                                         download_destination='481516')

        last_result = Result(failed_urls=['1', 'one'], succeeded_urls=['x'])
        progress_info = ProgressInfo(total_downloaded=192,
                                     total_failed=38,
                                     finished=False,
                                     last_result=last_result)

        position = Position(3, 1)
        counts = {'wnid1': 29, 'wnid10': 3}
        internal = InternalState(iterator_position=position,
                                 category_counts=counts,
                                 file_index=322)

        app_state.set_configuration(new_conf)
        app_state.set_progress_info(progress_info)
        app_state.set_internal_state(internal)
        app_state.save()

        app_state = AppState()

        conf = app_state.download_configuration
        self.assertEqual(conf.download_destination, '481516')
        self.assertEqual(conf.number_of_images, 9309)
        self.assertEqual(conf.images_per_category, 83)

        progress_info = app_state.progress_info
        self.assertEqual(progress_info.total_downloaded, 192)
        self.assertEqual(progress_info.total_failed, 38)
        self.assertEqual(progress_info.finished, False)
        self.assertEqual(progress_info.last_result.failed_urls, ['1', 'one'])

        self.assertEqual(progress_info.last_result.succeeded_urls, ['x'])

        internal = app_state.internal_state
        self.assertEqual(internal.iterator_position.word_id_offset, 3)
        self.assertEqual(internal.iterator_position.url_offset, 1)
        self.assertEqual(internal.category_counts, counts)
        self.assertEqual(internal.file_index, 322)

    def test_with_corrupted_json_file(self):
        os.makedirs(config.app_data_folder)
        path = config.app_state_path
        with open(path, 'w') as f:
            f.write('[238jf0[{9f0923j]jf{{{')

        app_state = AppState()
        conf = app_state.download_configuration
        self.assertEqual(conf.download_destination, '')
        self.assertEqual(conf.number_of_images, 100)
        self.assertEqual(conf.images_per_category, 90)

    def test_with_missing_fields_in_json_file(self):
        os.makedirs(config.app_data_folder)
        path = config.app_state_path
        with open(path, 'w') as f:
            f.write('{}')

        app_state = AppState()
        conf = app_state.download_configuration
        self.assertEqual(conf.download_destination, '')
        self.assertEqual(conf.number_of_images, 100)
        self.assertEqual(conf.images_per_category, 90)

    def test_progress(self):
        app_state = AppState()

        new_conf = DownloadConfiguration(number_of_images=10,
                                         images_per_category=83,
                                         download_destination='481516')

        last_result = Result(failed_urls=['1', 'one'], succeeded_urls=['x'])
        progress_info = ProgressInfo(total_downloaded=9,
                                     total_failed=38,
                                     finished=False,
                                     last_result=last_result)

        app_state.set_configuration(new_conf)
        app_state.set_progress_info(progress_info)

        self.assertAlmostEqual(app_state.calculate_progress(), 0.9)

    def test_progress_zero_by_zero(self):
        app_state = AppState()

        new_conf = DownloadConfiguration(number_of_images=0,
                                         images_per_category=83,
                                         download_destination='481516')


        app_state.set_configuration(new_conf)

        self.assertAlmostEqual(app_state.calculate_progress(), 0)

    def test_is_inprogress_initially(self):
        app_state = AppState()

        self.assertFalse(app_state.inprogress)

    def test_inprogress_after_updates(self):
        app_state = AppState()
        app_state.update_progress(result=Result([''], ['afef']))
        self.assertTrue(app_state.inprogress)
        app_state.save()

        app_state = AppState()
        self.assertTrue(app_state.inprogress)

    def test_inprogress_after_finishing(self):
        app_state = AppState()
        app_state.update_progress(result=Result([''], ['afef']))
        app_state.mark_finished()

        self.assertTrue(app_state.inprogress)
        app_state.save()

        app_state = AppState()
        self.assertTrue(app_state.inprogress)

    def test_inprogress_after_configuring(self):
        app_state = AppState()
        app_state.update_progress(result=Result([''], ['afef']))
        app_state.mark_finished()

        new_conf = DownloadConfiguration(number_of_images=0,
                                         images_per_category=83,
                                         download_destination='481516')

        app_state.set_configuration(new_conf)
        self.assertFalse(app_state.inprogress)

    def test_add_error(self):
        app_state = AppState()

        app_state.add_error('abc')
        app_state.add_error('def')


        app_state.errors[:] = []
        self.assertEqual(app_state.errors, ['abc', 'def'])

    def test_errors_after_new_configuration(self):
        app_state = AppState()

        new_conf = DownloadConfiguration(number_of_images=0,
                                         images_per_category=83,
                                         download_destination='481516')

        app_state.add_error('abc')

        app_state.set_configuration(new_conf)
        self.assertEqual(app_state.errors, [])

    def test_errors_persist(self):
        app_state = AppState()
        app_state.add_error('abc')
        app_state.add_error('def')

        app_state.save()

        app_state = AppState()
        self.assertEqual(app_state.errors, ['abc', 'def'])

    def test_to_json(self):
        app_state = AppState()

        new_conf = DownloadConfiguration(number_of_images=9309,
                                         images_per_category=83,
                                         download_destination='481516')

        last_result = Result(failed_urls=['1', 'one'], succeeded_urls=['x'])
        progress_info = ProgressInfo(total_downloaded=192,
                                     total_failed=38,
                                     finished=False,
                                     last_result=last_result)

        position = Position(3, 1)
        counts = {'wnid1': 29, 'wnid10': 3}
        internal = InternalState(iterator_position=position,
                                 category_counts=counts,
                                 file_index=322)

        app_state.set_configuration(new_conf)
        app_state.set_progress_info(progress_info)
        app_state.set_internal_state(internal)

        app_state.add_error('Some error')

        state_data = json.loads(app_state.to_json())

        self.assertEqual(state_data['downloadPath'], '481516')
        self.assertEqual(state_data['numberOfImages'], 9309)
        self.assertEqual(state_data['imagesPerCategory'], 83)
        self.assertNotEqual(state_data['timeLeft'], '')
        self.assertEqual(state_data['imagesLoaded'], 192)
        self.assertEqual(state_data['failures'], 38)
        self.assertEqual(state_data['failedUrls'], ['1', 'one'])
        self.assertEqual(state_data['succeededUrls'], ['x'])

        self.assertEqual(state_data['errors'], ['Some error'])

        self.assertAlmostEqual(state_data['progress'], 192.0 / 9309)
