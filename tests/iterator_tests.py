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

sys.path.insert(0, './')

from registered_test_cases import Meta

from image_net import iterators
from config import config
import shutil


class ReadByLinesTests(unittest.TestCase, metaclass=Meta):
    def test_url_has_no_trailing_newline_character(self):
        path = os.path.join('fixtures', 'dummy_synset.txt')
        for url in iterators.read_by_lines(path):
            self.assertFalse('\n' in url, 'Contains "\n" character')

    def test_that_iterator_outputs_expected_urls(self):
        path = os.path.join('fixtures', 'dummy_synset.txt')
        urls = [url for url in iterators.read_by_lines(path)]
        self.assertEqual(urls[0], 'http://some_domain.com/something')
        self.assertEqual(urls[1], 'http://another-domain.com/1234%329jflija')
        self.assertEqual(urls[2], 'http://another-domain.com/x/y/z')


class ImageNetUrlsTests(unittest.TestCase, metaclass=Meta):
    def tearDown(self):
        if os.path.exists(config.app_data_folder):
            shutil.rmtree(config.app_data_folder)

    def test_getting_all_urls(self):
        it = iterators.create_image_net_urls()
        results = []
        positions = []
        for wn_id, url, pos in it:
            results.append((wn_id, url))
            positions.append(pos.to_json())

        expected_pairs = [
            ('n392093', 'url1'), ('n392093', 'url2'),
            ('n392093', 'url3'),
            ('n38203', 'url4'), ('n38203', 'url5')
        ]
        self.assertEqual(results, expected_pairs)

        expected_positions = [
            iterators.Position(0, 0).to_json(),
            iterators.Position(0, 1).to_json(),
            iterators.Position(0, 2).to_json(),
            iterators.Position(1, 0).to_json(),
            iterators.Position(1, 1).to_json()
        ]

        self.assertEqual(positions, expected_positions)

    def test_iterate_from_initial_index(self):
        position = iterators.Position(0, 1)
        it = iterators.create_image_net_urls(start_after_position=position)

        results = []
        positions = []
        for wn_id, url, pos in it:
            results.append((wn_id, url))
            positions.append(pos.to_json())

        expected_pairs = [
            ('n392093', 'url3'),
            ('n38203', 'url4'), ('n38203', 'url5')
        ]
        self.assertEqual(results, expected_pairs)

        expected_positions = [
            iterators.Position(0, 2).to_json(),
            iterators.Position(1, 0).to_json(),
            iterators.Position(1, 1).to_json()
        ]

        self.assertEqual(positions, expected_positions)
