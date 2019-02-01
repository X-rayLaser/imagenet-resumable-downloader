import unittest
import os
import sys

sys.path.insert(0, './')

from registered_test_cases import Meta
from config import config
import shutil
import downloader
from util import Url2FileName


class ThreadingDownloaderTests(unittest.TestCase, metaclass=Meta):
    def setUp(self):
        factory = downloader.get_factory()

        self.destination = os.path.join(config.app_data_folder,
                                        'image_net_home')

        if os.path.exists(self.destination):
            shutil.rmtree(self.destination)
        os.makedirs(self.destination)

        self.downloader = factory.new_threading_downloader()

    def test_with_multiple_urls(self):
        url2file_name = Url2FileName()

        urls = ['first url'] * 5

        file_names = [url2file_name.convert(url) for url in urls]
        destinations = [os.path.join(self.destination, fname)
                        for fname in file_names]
        self.downloader.download(urls, destinations)

        file_list = []
        for dirname, dirs, filenames in os.walk(self.destination):
            paths = [os.path.join(dirname, fname) for fname in filenames]
            file_list.extend(paths)

        expected_num_of_files = len(self.downloader.downloaded_urls)
        self.assertEqual(len(file_list), expected_num_of_files)

        for path in file_list:
            with open(path, 'r') as f:
                self.assertEqual(f.read(), 'Dummy downloader written file')
