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
import shutil

sys.path.insert(0, './')

from image_net import batch_download
from util.app_state import DownloadConfiguration

from registered_test_cases import Meta


class BatchDownloadTests(unittest.TestCase, metaclass=Meta):
    def setUp(self):
        self.dataset_location = os.path.join('temp', 'imagenet')
        if os.path.exists(self.dataset_location):
            shutil.rmtree(self.dataset_location)
        os.makedirs(self.dataset_location, exist_ok=True)

    def test_flush_creates_directories(self):
        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                return [], urls

        conf = DownloadConfiguration(number_of_images=100,
                                     images_per_category=100,
                                     download_destination=self.dataset_location,
                                     batch_size=100)
        d = BatchDownloadMocked(conf)

        for wn_id, url in [('wn1', 'url1'), ('wn2', 'url2'), ('wn2', 'x')]:
            d.add(wn_id, url)

        d.flush()

        dirs = []
        for dirname, dir_names, file_names in os.walk(self.dataset_location):
            dirs.extend(dir_names)

        self.assertEqual(dirs, ['wn1', 'wn2'])

    def test_flush_downloads_correctly(self):
        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = ['url1', 'url3']
                succeeded_urls = ['url2']
                return failed_urls, succeeded_urls

        conf = DownloadConfiguration(number_of_images=100,
                                     images_per_category=100,
                                     download_destination=self.dataset_location,
                                     batch_size=100)
        d = BatchDownloadMocked(conf)

        for wn_id, url in [('wn1', 'url1'), ('wn1', 'url2'), ('wn3', 'url3')]:
            d.add(wn_id, url)

        failed, downloaded = d.flush()

        self.assertEqual(failed, ['url1', 'url3'])
        self.assertEqual(downloaded, ['url2'])

    def test_flush_removes_elements_in_buffer(self):
        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = urls
                succeeded_urls = []
                return failed_urls, succeeded_urls

        conf = DownloadConfiguration(number_of_images=100,
                                     images_per_category=100,
                                     download_destination=self.dataset_location,
                                     batch_size=2)
        d = BatchDownloadMocked(conf)

        d.add('wn1', 'url1')
        d.add('wn2', 'url2')
        d.add('wn3', 'url3')

        d.flush()
        failed, downloaded = d.flush()

        self.assertEqual(failed, [])
        self.assertEqual(downloaded, [])

    def test_batch_ready(self):
        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = [urls[0]]
                succeeded_urls = [urls[1]]
                return failed_urls, succeeded_urls

        conf = DownloadConfiguration(number_of_images=100,
                                     images_per_category=100,
                                     download_destination=self.dataset_location,
                                     batch_size=2)
        d = BatchDownloadMocked(conf)

        d.add('wn1', 'url1')
        self.assertFalse(d.batch_ready)

        d.add('wn1', 'url2')
        self.assertTrue(d.batch_ready)

        failed, downloaded = d.flush()
        self.assertEqual(failed, ['url1'])
        self.assertEqual(downloaded, ['url2'])

    def test_batch_empty(self):
        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = [urls[0]]
                succeeded_urls = [urls[1]]
                return failed_urls, succeeded_urls

        conf = DownloadConfiguration(number_of_images=100,
                                     images_per_category=100,
                                     download_destination=self.dataset_location,
                                     batch_size=3)
        d = BatchDownloadMocked(conf)

        self.assertTrue(d.is_empty)
        d.add('wn1', 'url1')
        self.assertFalse(d.is_empty)

        d.add('wn1', 'url1')
        d.flush()
        self.assertTrue(d.is_empty)

    def test_completed(self):
        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = [urls[0]]
                succeeded_urls = [urls[1]]
                return failed_urls, succeeded_urls

        conf = DownloadConfiguration(number_of_images=2,
                                     images_per_category=100,
                                     download_destination=self.dataset_location,
                                     batch_size=2)
        d = BatchDownloadMocked(conf)

        self.assertFalse(d.complete)

        d.add('wn1', 'url1')
        d.add('wn2', 'url3')
        d.flush()

        self.assertFalse(d.complete)

        d.add('wn1', 'url42')
        d.add('wn5', 'url2')
        self.assertFalse(d.complete)

        d.flush()
        self.assertTrue(d.complete)

    def test_complete_after_getting_more_images_than_was_requested(self):
        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                return [], urls

        conf = DownloadConfiguration(number_of_images=3,
                                     images_per_category=100,
                                     download_destination=self.dataset_location,
                                     batch_size=2)
        d = BatchDownloadMocked(conf)

        d.add('wn1', 'url1')
        d.add('wn2', 'url3')

        d.flush()
        self.assertFalse(d.complete)

        d.add('wn1', 'url42')
        d.add('wn5', 'url2')
        d.flush()
        self.assertTrue(d.complete)

    def test_that_images_per_category_parameter_works_correctly(self):
        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                return [], urls

        downloaded = []

        conf = DownloadConfiguration(number_of_images=100,
                                     images_per_category=2,
                                     download_destination=self.dataset_location,
                                     batch_size=3)
        d = BatchDownloadMocked(conf)

        d.add('n123', 'url1')
        d.add('n999', 'url2')
        d.add('n123', 'url3')
        failed, downloaded_urls = d.flush()
        downloaded.extend(downloaded_urls)

        d.add('n123', 'url4')
        d.add('n999', 'url5')
        d.add('n555', 'url6')
        d.add('n555', 'url7')

        failed, downloaded_urls = d.flush()
        downloaded.extend(downloaded_urls)

        self.assertEqual(downloaded, ['url1', 'url2', 'url3', 'url5', 'url6', 'url7'])

    def test_with_both_limiting_parameters(self):
        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                return [], urls

        conf = DownloadConfiguration(number_of_images=7,
                                     images_per_category=2,
                                     download_destination=self.dataset_location,
                                     batch_size=2)
        d = BatchDownloadMocked(conf)

        d.add('n1', 'url1')
        d.add('n1', 'url2')
        self.assertTrue(d.batch_ready)
        d.flush()

        d.add('n1', 'url3')
        d.add('n2', 'url4')
        self.assertFalse(d.batch_ready)

        d.add('n3', 'url5')
        self.assertTrue(d.batch_ready)
        d.flush()

        d.add('n3', 'url6')
        d.add('n3', 'url7')
        self.assertTrue(d.batch_ready)
        d.flush()

        d.add('n3', 'url8')
        d.add('n4', 'url9')
        self.assertFalse(d.batch_ready)

        self.assertFalse(d.complete)
        d.add('n5', 'url10')
        d.flush()

        self.assertTrue(d.complete)

    def test_destination_paths(self):
        paths = []

        class BatchDownloadMocked(batch_download.BatchDownload):
            def do_download(self, urls, destinations):
                paths.extend(destinations)
                return [], urls

        conf = DownloadConfiguration(number_of_images=100,
                                     images_per_category=100,
                                     download_destination=self.dataset_location,
                                     batch_size=3)
        d = BatchDownloadMocked(conf)

        d.add('dogs', 'url1.jpg')
        d.add('cats', 'url2.png')
        d.add('dogs', 'url2.gif')
        d.flush()

        first = os.path.join(self.dataset_location, 'dogs', '1.jpg')
        second = os.path.join(self.dataset_location, 'cats', '2.png')
        third = os.path.join(self.dataset_location, 'dogs', '3.gif')
        self.assertEqual(paths, [first, second, third])
