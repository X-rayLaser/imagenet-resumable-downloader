import unittest
import os
import sys
import time

from PyQt5 import QtWidgets
from PyQt5.QtTest import QSignalSpy

sys.path.insert(0, './')

import iterators
import util
from config import config
import shutil
import downloader
from downloader import Url2FileName, StatefulDownloader, DownloadConfiguration
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


class Url2FileNameTests(unittest.TestCase):
    def test_conversion_of_first_urls(self):
        url2name = util.Url2FileName()
        first = url2name.convert('http://haha.com/hahahaha.jpg')
        second = url2name.convert('http://example.com/hahahaha.png')
        self.assertEqual(first, '1.jpg')
        self.assertEqual(second, '2.png')

    def test_that_urls_with_trailing_newline_are_forbidden(self):
        url2name = util.Url2FileName()

        def f1():
            url2name.convert('http://haha.com/hahahaha.jpg\n')

        def f2():
            url2name.convert('http://haha.com/hahahaha.jpg\n\r\n\r')

        self.assertRaises(util.MalformedUrlError, f1)

        self.assertRaises(util.MalformedUrlError, f2)

        first = url2name.convert('http://haha.com/hahahaha.jpg')
        self.assertEqual(first, '1.jpg')

    def test_that_urls_with_trailing_spaces_are_forbidden(self):
        url2name = util.Url2FileName()

        def f():
            url2name.convert('http://haha.com/hahahaha.jpg    \n')

        self.assertRaises(util.MalformedUrlError, f)

        first = url2name.convert('http://haha.com/hahahaha.jpg')
        self.assertEqual(first, '1.jpg')

    def test_that_conversion_accounts_for_duplicates(self):
        url2name = util.Url2FileName()
        first = url2name.convert('http://example.com/xyz.jpg')
        second = url2name.convert('http://example.com/xyz.jpg')
        self.assertEqual(first, '1.jpg')
        self.assertEqual(second, '2.jpg')

    def test_with_non_ascii_characters_in_url_file_path(self):
        url2name = util.Url2FileName()

        from urllib import parse
        path = parse.quote(' xyz~`!@#$%^&*()_+=-{}[];:\'"\|,.<>/?.jpg')
        first = url2name.convert(
            'http://example.com/' + path
        )

        self.assertEqual(first, '1.jpg')

    def test_starting_index(self):
        url2name = util.Url2FileName(starting_index=3)
        self.assertEqual(url2name.file_index, 3)

        third = url2name.convert('http://example.com/third.gif')
        fourth = url2name.convert('http://example.com/fourth.png')

        self.assertEqual(third, '3.gif')
        self.assertEqual(fourth, '4.png')

        self.assertEqual(url2name.file_index, 5)


class ImageNetUrlsTests(unittest.TestCase):
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


class ThreadingDownloaderTests(unittest.TestCase):
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


class BatchDownloadTests(unittest.TestCase):
    def setUp(self):
        self.dataset_location = os.path.join('temp', 'imagenet')
        if os.path.exists(self.dataset_location):
            shutil.rmtree(self.dataset_location)
        os.makedirs(self.dataset_location, exist_ok=True)

    def test_flush_creates_directories(self):
        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                return [], urls

        d = BatchDownloadMocked(self.dataset_location)

        for wn_id, url in [('wn1', 'url1'), ('wn2', 'url2'), ('wn2', 'x')]:
            d.add(wn_id, url)

        d.flush()

        dirs = []
        for dirname, dir_names, file_names in os.walk(self.dataset_location):
            dirs.extend(dir_names)

        self.assertEqual(dirs, ['wn1', 'wn2'])

    def test_flush_downloads_correctly(self):
        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = ['url1', 'url3']
                succeeded_urls = ['url2']
                return failed_urls, succeeded_urls
        d = BatchDownloadMocked(self.dataset_location)

        for wn_id, url in [('wn1', 'url1'), ('wn1', 'url2'), ('wn3', 'url3')]:
            d.add(wn_id, url)

        failed, downloaded = d.flush()

        self.assertEqual(failed, ['url1', 'url3'])
        self.assertEqual(downloaded, ['url2'])

    def test_flush_removes_elements_in_buffer(self):
        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = urls
                succeeded_urls = []
                return failed_urls, succeeded_urls

        d = BatchDownloadMocked(self.dataset_location, batch_size=2)

        d.add('wn1', 'url1')
        d.add('wn2', 'url2')
        d.add('wn3', 'url3')

        d.flush()
        failed, downloaded = d.flush()

        self.assertEqual(failed, [])
        self.assertEqual(downloaded, [])

    def test_batch_ready(self):
        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = [urls[0]]
                succeeded_urls = [urls[1]]
                return failed_urls, succeeded_urls
        d = BatchDownloadMocked(self.dataset_location, batch_size=2)

        d.add('wn1', 'url1')
        self.assertFalse(d.batch_ready)

        d.add('wn1', 'url2')
        self.assertTrue(d.batch_ready)

        failed, downloaded = d.flush()
        self.assertEqual(failed, ['url1'])
        self.assertEqual(downloaded, ['url2'])

    def test_batch_empty(self):
        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = [urls[0]]
                succeeded_urls = [urls[1]]
                return failed_urls, succeeded_urls
        d = BatchDownloadMocked(self.dataset_location, batch_size=3)

        self.assertTrue(d.is_empty)
        d.add('wn1', 'url1')
        self.assertFalse(d.is_empty)

        d.add('wn1', 'url1')
        d.flush()
        self.assertTrue(d.is_empty)

    def test_completed(self):
        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                failed_urls = [urls[0]]
                succeeded_urls = [urls[1]]
                return failed_urls, succeeded_urls
        d = BatchDownloadMocked(self.dataset_location, number_of_images=2, batch_size=2)

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
        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                return [], urls

        d = BatchDownloadMocked(self.dataset_location, number_of_images=3, batch_size=2)

        d.add('wn1', 'url1')
        d.add('wn2', 'url3')

        d.flush()
        self.assertFalse(d.complete)

        d.add('wn1', 'url42')
        d.add('wn5', 'url2')
        d.flush()
        self.assertTrue(d.complete)

    def test_that_images_per_category_parameter_works_correctly(self):
        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                return [], urls

        downloaded = []

        d = BatchDownloadMocked(self.dataset_location, images_per_category=2, batch_size=3)

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
        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                return [], urls

        d = BatchDownloadMocked(self.dataset_location, number_of_images=7,
                                images_per_category=2, batch_size=2)

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

        class BatchDownloadMocked(downloader.BatchDownload):
            def do_download(self, urls, destinations):
                paths.extend(destinations)
                return [], urls

        d = BatchDownloadMocked(self.dataset_location, batch_size=3)

        d.add('dogs', 'url1.jpg')
        d.add('cats', 'url2.png')
        d.add('dogs', 'url2.gif')
        d.flush()

        first = os.path.join(self.dataset_location, 'dogs', '1.jpg')
        second = os.path.join(self.dataset_location, 'cats', '2.png')
        third = os.path.join(self.dataset_location, 'dogs', '3.gif')
        self.assertEqual(paths, [first, second, third])


class DownloadManagerTests(unittest.TestCase):
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
        manager = DownloadManager(destination=self.image_net_home,
                                  number_of_examples=5,
                                  images_per_category=10)
        signal = getattr(manager, signal)
        spy = QSignalSpy(signal)
        manager.start()
        received = spy.wait(timeout=500)
        self.assertTrue(received)

        self.stop_the_thread(manager)

    def test_folders_are_created(self):
        manager = DownloadManager(destination=self.image_net_home,
                                  number_of_examples=5,
                                  images_per_category=10)

        self.wait_for_completion(manager)
        self._assert_expected_directories_exist()
        self.stop_the_thread(manager)

    def test_files_are_downloaded(self):
        manager = DownloadManager(destination=self.image_net_home,
                                  number_of_examples=5,
                                  images_per_category=10)

        self.wait_for_completion(manager)
        self._assert_files_are_correct()
        self.stop_the_thread(manager)

    def test_case_when_requested_number_of_images_is_greater_than_total(self):
        manager = DownloadManager(destination=self.image_net_home,
                                  number_of_examples=50,
                                  images_per_category=100)

        self.wait_for_completion(manager)
        self._assert_files_are_correct()
        self.stop_the_thread(manager)

    def test_images_per_category_argument(self):
        manager = DownloadManager(destination=self.image_net_home,
                                  number_of_examples=5,
                                  images_per_category=1,
                                  batch_size=1)

        self.wait_for_completion(manager)

        files_count = 0
        for dirname, dirs, file_names in os.walk(self.image_net_home):
            files_count += len(file_names)
        self.assertEqual(files_count, 2)

        self.stop_the_thread(manager)

    def test_start_pause_and_resume(self):
        manager = DownloadManager(destination=self.image_net_home,
                                  number_of_examples=5,
                                  images_per_category=1)
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


class StatefulDownloaderTests(unittest.TestCase):
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
        downloader = StatefulDownloader()

        dconf = DownloadConfiguration(number_of_images=10,
                                      images_per_category=10,
                                      download_destination=self.image_net_home)
        downloader.configure(dconf)

        results = []
        failed_urls = []
        successful_urls = []
        for result in downloader:
            results.append(result)
            failed_urls.extend(result.failed_urls)
            successful_urls.extend(result.succeeded_urls)

        self.assertEqual(failed_urls, [])
        self.assertEqual(successful_urls, ['url1', 'url2', 'url3', 'url4', 'url5'])

        self.assertEqual(downloader.total_downloaded, 5)
        self.assertEqual(downloader.total_failed, 0)

        self.assertTrue(downloader.finished)

    def test_without_configuring(self):
        def f():
            d = StatefulDownloader()

            for result in d:
                pass

        self.assertRaises(downloader.NotConfiguredError, f)

    def test_data_persistence(self):
        downloader = StatefulDownloader()

        dconf = DownloadConfiguration(number_of_images=10,
                                      images_per_category=12,
                                      download_destination=self.image_net_home,
                                      batch_size=3)
        downloader.configure(dconf)

        res = None
        for result in downloader:
            res = result
            break

        downloader = StatefulDownloader()

        self.assertEqual(downloader.configuration.number_of_images, 10)
        self.assertEqual(downloader.configuration.images_per_category, 12)
        self.assertEqual(downloader.configuration.batch_size, 3)
        self.assertEqual(downloader.configuration.download_destination,
                         self.image_net_home)

        self.assertEqual(downloader.last_result.failed_urls,
                         res.failed_urls)
        self.assertEqual(downloader.last_result.succeeded_urls,
                         res.succeeded_urls)

        self.assertEqual(downloader.total_failed, 0)
        self.assertEqual(downloader.total_downloaded, 3)
        self.assertFalse(downloader.finished)

        for result in downloader:
            pass

        downloader = StatefulDownloader()
        self.assertTrue(downloader.finished)

    def test_with_corrupted_json_file(self):
        path = config.download_state_path
        with open(path, 'w') as f:
            f.write('[238jf0[{9f0923j]jf{{{')
        d = StatefulDownloader()
        self.assertFalse(d.finished)

        def f():
            for res in d:
                pass

        self.assertRaises(downloader.NotConfiguredError, f)

    def test_with_missing_fields_in_json_file(self):
        path = config.download_state_path
        import json
        with open(path, 'w') as f:
            f.write(json.dumps({'number_of_images': 15}))
        d = StatefulDownloader()
        self.assertFalse(d.finished)

        def f():
            for res in d:
                pass

        self.assertRaises(downloader.NotConfiguredError, f)

    def test_stopping_and_resuming_with_new_instance(self):
        downloader = StatefulDownloader()

        dconf = DownloadConfiguration(number_of_images=10,
                                      images_per_category=12,
                                      batch_size=3,
                                      download_destination=self.image_net_home)
        downloader.configure(dconf)

        for result in downloader:
            break

        downloader = StatefulDownloader()

        failed_urls = []
        successful_urls = []
        for result in downloader:
            failed_urls.extend(result.failed_urls)
            successful_urls.extend(result.succeeded_urls)
            break

        self.assertEqual(failed_urls, [])
        self.assertEqual(successful_urls, ['url4', 'url5'])

        self.assertEqual(downloader.total_downloaded, 5)
        self.assertEqual(downloader.total_failed, 0)

        self.assertTrue(downloader.finished)

    def test_creates_files_as_expected(self):
        downloader = StatefulDownloader()

        dconf = DownloadConfiguration(number_of_images=4,
                                      images_per_category=1,
                                      batch_size=2,
                                      download_destination=self.image_net_home)
        downloader.configure(dconf)

        for result in downloader:
            break

        downloader = StatefulDownloader()
        for result in downloader:
            pass

        fnames = []
        for dirname, dirs, file_names in os.walk(self.image_net_home):
            fnames.extend(file_names)

        expected_names = ['1', '2', '3', '4']

        self.assertEqual(set(fnames), set(expected_names))

    def test_remembers_number_of_images_downloaded_for_each_category(self):
        downloader = StatefulDownloader()

        dconf = DownloadConfiguration(number_of_images=4,
                                      images_per_category=1,
                                      batch_size=2,
                                      download_destination=self.image_net_home)
        downloader.configure(dconf)

        for result in downloader:
            break

        downloader = StatefulDownloader()

        failed_urls = []
        successful_urls = []
        for result in downloader:
            failed_urls.extend(result.failed_urls)
            successful_urls.extend(result.succeeded_urls)
            break

        self.assertEqual(failed_urls, [])
        self.assertEqual(successful_urls, ['url4', 'url5'])

        self.assertEqual(downloader.total_downloaded, 4)
        self.assertEqual(downloader.total_failed, 0)

        self.assertTrue(downloader.finished)

    def test_reconfiguration(self):
        downloader = StatefulDownloader()

        dconf = DownloadConfiguration(number_of_images=4,
                                      images_per_category=1,
                                      batch_size=2,
                                      download_destination=self.image_net_home)
        downloader.configure(dconf)

        for result in downloader:
            break

        shutil.rmtree(self.image_net_home)
        os.makedirs(self.image_net_home)

        downloader = StatefulDownloader()
        dconf = DownloadConfiguration(number_of_images=2,
                                      images_per_category=2,
                                      batch_size=2,
                                      download_destination=self.image_net_home)
        downloader.configure(dconf)

        failed_urls = []
        successful_urls = []
        for result in downloader:
            failed_urls.extend(result.failed_urls)
            successful_urls.extend(result.succeeded_urls)
            break

        self.assertEqual(successful_urls, ['url1', 'url2'])

        self.assertEqual(downloader.total_downloaded, 2)
        self.assertEqual(downloader.total_failed, 0)

        fnames = []
        for dirname, dirs, file_names in os.walk(self.image_net_home):
            fnames.extend(file_names)

        expected_names = ['1', '2']

        self.assertEqual(set(fnames), set(expected_names))


if __name__ == '__main__':
    os.environ['TEST_ENV'] = 'test environment'
    unittest.main()
