import unittest
import os
import sys

sys.path.insert(0, './')

import iterators
import util
from util import ItemsRegistry
from config import config
import shutil
import downloader
from downloader import Url2FileName
from py_qml_glue import DownloadManager


class ReadByLinesTests(unittest.TestCase):
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


class WithRegistryMixin(unittest.TestCase):
    def setUp(self):
        file_dir = 'imagenet_data'
        file_path = os.path.join(file_dir, 'test_registry.json')
        self.file_path = file_path

        if not os.path.exists(file_dir):
            os.mkdir(file_dir)

        if os.path.isfile(file_path):
            os.remove(file_path)
        self.registry = ItemsRegistry(file_path)


class FileNameRegistryTests(WithRegistryMixin):
    def test_adding_name_and_checking_it(self):
        registry = self.registry
        self.assertNotIn('Hello, world!', registry)
        registry.add('Hello, world!')
        self.assertIn('Hello, world!', registry)

    def test_items_persist(self):
        registry = self.registry
        registry.add('first')
        registry.add('second')
        registry.add('third')
        registry.remove('second')
        
        registry = ItemsRegistry(self.file_path)
        self.assertIn('first', registry)
        self.assertIn('third', registry)
        self.assertNotIn('second', registry)

    def test_numbers_persist(self):
        registry = self.registry
        registry.add(2)
        registry.add(9)
        registry.add(11)
        registry.remove(9)

        registry = ItemsRegistry(self.file_path)
        self.assertIn(2, registry)
        self.assertIn(11, registry)
        self.assertNotIn(9, registry)

    def test_add_after_loading_from_file(self):
        registry = self.registry
        registry.add(2)
        registry.add("Hello")

        registry = ItemsRegistry(self.file_path)
        registry.add('world')

        self.assertIn(2, registry)
        self.assertIn('Hello', registry)
        self.assertIn('world', registry)

    def test_remove_after_loading_from_file(self):
        registry = self.registry
        registry.add(2)
        registry.add("Hello")

        registry = ItemsRegistry(self.file_path)
        registry.remove("Hello")
        self.assertIn(2, registry)
        self.assertNotIn("hello", registry)

    def test_adding_2_items(self):
        registry = self.registry
        registry.add('First')
        registry.add('Second')
        self.assertIn('First', registry)
        self.assertIn('Second', registry)

    def test_item_removal(self):
        registry = self.registry
        registry.add('First')
        registry.remove('First')
        self.assertNotIn('First', registry)

    def test_removal_of_missing_item_has_no_effect(self):
        registry = self.registry
        registry.add('First')
        registry.remove('Second')

        self.assertIn('First', registry)
        self.assertNotIn('Second', registry)


class Url2FileNameTests(WithRegistryMixin):
    def test_conversion_of_first_urls(self):
        url2name = util.Url2FileName(self.registry)
        first = url2name.convert('http://haha.com/hahahaha.jpg')
        second = url2name.convert('http://example.com/hahahaha.png')
        self.assertEqual(first, '1.jpg')
        self.assertEqual(second, '2.png')

    def test_that_urls_with_trailing_newline_are_forbidden(self):
        url2name = util.Url2FileName(self.registry)

        def f1():
            url2name.convert('http://haha.com/hahahaha.jpg\n')

        def f2():
            url2name.convert('http://haha.com/hahahaha.jpg\n\r\n\r')

        self.assertRaises(util.MalformedUrlError, f1)

        self.assertRaises(util.MalformedUrlError, f2)

        first = url2name.convert('http://haha.com/hahahaha.jpg')
        self.assertEqual(first, '1.jpg')

    def test_that_urls_with_trailing_spaces_are_forbidden(self):
        url2name = util.Url2FileName(self.registry)

        def f():
            url2name.convert('http://haha.com/hahahaha.jpg    \n')

        self.assertRaises(util.MalformedUrlError, f)

        first = url2name.convert('http://haha.com/hahahaha.jpg')
        self.assertEqual(first, '1.jpg')

    def test_that_conversion_accounts_for_duplicates(self):
        url2name = util.Url2FileName(self.registry)
        first = url2name.convert('http://example.com/xyz.jpg')
        second = url2name.convert('http://example.com/xyz.jpg')
        self.assertEqual(first, '1.jpg')
        self.assertEqual(second, '2.jpg')

    def test_with_non_ascii_characters_in_url_file_path(self):
        url2name = util.Url2FileName(self.registry)

        from urllib import parse
        path = parse.quote(' xyz~`!@#$%^&*()_+=-{}[];:\'"\|,.<>/?.jpg')
        first = url2name.convert(
            'http://example.com/' + path
        )

        self.assertEqual(first, '1.jpg')

    def test_persistence(self):
        url2name = util.Url2FileName(self.registry)
        first = url2name.convert('http://example.com/xyz.jpg')
        second = url2name.convert('http://example.com/xyz.jpg')

        registry = util.ItemsRegistry(self.file_path)
        url2name = util.Url2FileName(registry)

        third = url2name.convert('http://example.com/third.gif')
        self.assertEqual(third, '3.gif')


class ImageNetUrlsTests(unittest.TestCase):
    def tearDown(self):
        if os.path.exists(config.app_data_folder):
            shutil.rmtree(config.app_data_folder)

    def test_getting_all_urls(self):
        it = iterators.create_image_net_urls(batch_size=2)
        results = []
        for pair in it:
            results.append(pair)

        expected_pairs = [
            ('n392093', ['url1', 'url2']),
            ('n392093', ['url3']),
            ('n38203', ['url4', 'url5'])
        ]
        self.assertEqual(results, expected_pairs)

    def test_with_1_pair_batch(self):
        it = iterators.create_image_net_urls(batch_size=1)
        results = []
        for pair in it:
            results.append(pair)

        expected_pairs = [
            ('n392093', ['url1']),
            ('n392093', ['url2']),
            ('n392093', ['url3']),
            ('n38203', ['url4']),
            ('n38203', ['url5'])
        ]
        self.assertEqual(results, expected_pairs)

    def test_with_default_batch_size(self):
        it = iterators.create_image_net_urls()
        results = []
        for pair in it:
            results.append(pair)

        expected_pairs = [
            ('n392093', ['url1', 'url2', 'url3']),
            ('n38203', ['url4', 'url5'])
        ]
        self.assertEqual(results, expected_pairs)

    def test_with_zero_batch_size(self):
        def f():
            it = iterators.create_image_net_urls(batch_size=0)

        self.assertRaises(iterators.InvalidBatchError, f)

    def test_with_negative_batch_size(self):

        def f():
            it = iterators.create_image_net_urls(batch_size=-1)

        self.assertRaises(iterators.InvalidBatchError, f)


class ThreadingDownloaderTests(unittest.TestCase):
    def setUp(self):
        factory = downloader.get_factory()

        self.destination = os.path.join(config.app_data_folder,
                                        'image_net_home')

        if os.path.exists(self.destination):
            shutil.rmtree(self.destination)
        os.makedirs(self.destination)

        file_name_registry = ItemsRegistry(config.registry_path)
        url2file_name = Url2FileName(file_name_registry)

        self.downloader = factory.new_threading_downloader(
            destination=self.destination, url2file_name=url2file_name
        )

    def test_with_multiple_urls(self):
        urls = ['first url'] * 5
        self.downloader.download(urls)

        file_list = []
        for dirname, dirs, filenames in os.walk(self.destination):
            paths = [os.path.join(dirname, fname) for fname in filenames]
            file_list.extend(paths)

        expected_num_of_files = len(self.downloader.downloaded_urls)
        self.assertEqual(len(file_list), expected_num_of_files)

        for path in file_list:
            with open(path, 'r') as f:
                self.assertEqual(f.read(), 'Dummy downloader written file')


class DownloadManagerTests(unittest.TestCase):
    def test_imageLoaded_signal(self):
        DownloadManager


if __name__ == '__main__':
    os.environ['TEST_ENV'] = 'test environment'
    unittest.main()
