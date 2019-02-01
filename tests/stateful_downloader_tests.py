import os
import shutil
import unittest

from registered_test_cases import Meta
import downloader
from config import config
from downloader import StatefulDownloader, DownloadConfiguration


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


