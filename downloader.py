import requests
import shutil
import os
from PIL import Image
import iterators
from util import Url2FileName
from config import config
import json


#todo: Implement session for storing the state of the app


class Session:
    def __init__(self):
        self.number_of_images = 0
        self.images_per_category = 0
        self.failed_urls = 0
        self.downloaded_urls = {}


class FileDownloader:
    timeout = config.file_download_timeout

    def __init__(self, destination):
        self.destination = destination

    def download(self, url):
        file_path = self.destination
        try:
            r = requests.get(url, stream=True, timeout=self.timeout)
            code = r.status_code
            if code == requests.codes.ok:
                with open(file_path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)

                return True
            else:
                print('Bad code {}. Url {}'.format(code, url))
                return False
        except Exception as e:
            print('Failed downloaing {}'.format(url))
            return False


class DummyDownloader:
    def __init__(self, destination):
        self.destination = destination

    def download(self, url):
        file_path = self.destination
        with open(file_path, 'w') as f:
            f.write('Dummy downloader written file')
        return True


class ImageValidator:
    def valid_image(self, path):
        try:
            Image.open(path)
            return True
        except IOError:
            return False


class DummyValidator:
    def __init__(self):
        self._count = 0

    def valid_image(self, path):
        self._count += 1
        return self._count % 2


class ThreadingDownloader:
    pool = config.pool_executor

    def __init__(self):
        self.downloaded_urls = []
        self.failed_urls = []

    def download(self, urls, destinations):
        self.downloaded_urls = []
        self.failed_urls = []

        args = zip(urls, destinations)
        pool = self.pool
        results = list(pool.map(self._download, args))

        for url, success in zip(urls, results):
            if success:
                self.downloaded_urls.append(url)
            else:
                self.failed_urls.append(url)

    def _download(self, args):
        image_url, file_path = args
        downloader = self.get_file_downloader(destination=file_path)
        success = downloader.download(image_url)

        validator = self.get_validator()
        if success:
            if validator.valid_image(file_path):
                return True
            else:
                os.remove(file_path)
                return False
        else:
            return False

    def get_file_downloader(self, destination):
        return FileDownloader(destination=destination)

    def get_validator(self):
        return ImageValidator()


class TestThreadingDownloader(ThreadingDownloader):
    def get_file_downloader(self, destination):
        return DummyDownloader(destination=destination)

    def get_validator(self):
        return DummyValidator()


class DownloadLocation:
    def __init__(self, destination_path):
        self._destination = destination_path

    def category_path(self, word_net_id):
        folder_path = os.path.join(self._destination, str(word_net_id))
        self._create_if_not_exist(folder_path)
        return folder_path

    def _create_if_not_exist(self, dir_path):
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)


class DownloadConfiguration:
    def __init__(self, number_of_images,
                 images_per_category,
                 download_destination,
                 batch_size=100):
        self.number_of_images = number_of_images
        self.images_per_category = images_per_category
        self.download_destination = download_destination
        self.batch_size = batch_size


class Result:
    def __init__(self, failed_urls, succeeded_urls):
        self.failed_urls = failed_urls
        self.succeeded_urls = succeeded_urls

    @property
    def failures_count(self):
        return len(self.failed_urls)

    @property
    def successes_count(self):
        return len(self.succeeded_urls)


class BatchDownload:
    def __init__(self, dataset_root, number_of_images=100,
                 images_per_category=100, batch_size=100, starting_index=1):
        self.on_fetched = lambda failed, succeeded : None
        self.on_complete = lambda: None

        self._location = DownloadLocation(dataset_root)
        self._pending = []
        self._batch_size = batch_size
        self._max_images = number_of_images
        self._images_per_category = images_per_category
        self._total_downloaded = 0

        self._url2file_name = Url2FileName(starting_index=starting_index)

        self._category_counts = {}

        self._threading_downloader = get_factory().new_threading_downloader()

    def set_counts(self, counts):
        self._category_counts = dict(counts)

    @property
    def category_counts(self):
        return dict(self._category_counts)

    @property
    def file_index(self):
        return self._url2file_name.file_index

    @property
    def batch_ready(self):
        return len(self._pending) >= self._batch_size

    @property
    def complete(self):
        return self._total_downloaded >= self._max_images

    @property
    def is_empty(self):
        return len(self._pending) == 0

    def flush(self):
        paths = self._file_paths()
        urls = self._url_batch()

        failed_urls, succeeded_urls = self.do_download(urls, paths)

        self._total_downloaded += len(succeeded_urls)
        if self._total_downloaded >= self._max_images:
            self.on_complete()

        self._update_category_counts(succeeded_urls)

        self.on_fetched(failed_urls, succeeded_urls)
        self._clear_buffer()

        return failed_urls, succeeded_urls

    def _update_category_counts(self, succeeded_urls):
        url_to_wn_id = {}
        for wn_id, url in self._pending:
            if wn_id not in url_to_wn_id:
                if url not in url_to_wn_id:
                    url_to_wn_id[url] = []
                url_to_wn_id[url].append(wn_id)

        for url in succeeded_urls:
            wn_ids = url_to_wn_id[url]
            for wn_id in wn_ids:
                self._category_counts[wn_id] += 1

    def _file_paths(self):
        paths = []

        for wn_id, url in self._pending:
            folder_path = self._location.category_path(wn_id)
            file_name = self._url2file_name.convert(url)

            path = os.path.join(folder_path, file_name)
            paths.append(path)
        return paths

    def _url_batch(self):
        return [url for _, url in self._pending]

    def _clear_buffer(self):
        self._pending[:] = []

    def do_download(self, urls, destinations):
        self._threading_downloader.download(urls, destinations)
        failed_urls = self._threading_downloader.failed_urls
        succeeded_urls = self._threading_downloader.downloaded_urls
        return failed_urls, succeeded_urls

    def add(self, wn_id, url):
        if wn_id not in self._category_counts:
            self._category_counts[wn_id] = 0

        if self._category_counts[wn_id] < self._images_per_category:
            self._pending.append((wn_id, url))


# todo: fix test for category_counts
class StatefulDownloader:
    def __init__(self):
        self._set_defaults()

        try:
            self._restore_from_file()
        except json.decoder.JSONDecodeError:
            pass
        except KeyError:
            pass

    def _set_defaults(self):
        self.destination = None
        self.number_of_images = 0
        self.images_per_category = 0
        self.batch_size = 100
        self.total_downloaded = 0
        self.total_failed = 0

        self._configured = False
        self.finished = False
        self._last_result = None
        self._last_position = iterators.Position.null_position()
        self._category_counts = {}

        self._file_index = 1

    def _restore_from_file(self):
        path = config.download_state_path
        if os.path.isfile(path):
            with open(path, 'r') as f:
                s = f.read()
                d = json.loads(s)
            self.destination = d['destination']
            self.number_of_images = d['number_of_images']
            self.images_per_category = d['images_per_category']
            self.batch_size = d['batch_size']
            self.total_downloaded = d['total_downloaded']
            self.total_failed = d['total_failed']
            self._configured = d['configured']
            self.finished = d['finished']

            failed_urls = d['failed_urls']
            succeeded_urls = d['succeeded_urls']

            self._last_position = iterators.Position.from_json(d['position'])
            self._last_result = Result(failed_urls, succeeded_urls)

            self._category_counts = d['category_counts']

            self._file_index = d['file_index']

    def __iter__(self):
        if not self._configured:
            raise NotConfiguredError()

        images_left = self.number_of_images - self.total_downloaded

        batch_download = BatchDownload(dataset_root=self.destination,
                                       number_of_images=images_left,
                                       images_per_category=self.images_per_category,
                                       batch_size=self.batch_size,
                                       starting_index=self._file_index)

        batch_download.set_counts(self._category_counts)

        image_net_urls = iterators.create_image_net_urls(
            start_after_position=self._last_position
        )

        for wn_id, url, position in image_net_urls:
            batch_download.add(wn_id, url)

            if batch_download.batch_ready:
                failed_urls, succeeded_urls = batch_download.flush()
                self._update_and_save_progress(failed_urls, succeeded_urls,
                                               batch_download)

                if batch_download.complete:
                    self.finished = True
                yield self._last_result
                if batch_download.complete:
                    self.finished = True
                    break

            self._last_position = position
            self._category_counts = batch_download.category_counts

        self.finished = True
        if not batch_download.is_empty:
            self._finish_download(batch_download)
            yield self._last_result

    def _finish_download(self, batch_download):
        failed_urls, succeeded_urls = batch_download.flush()
        self._update_and_save_progress(failed_urls, succeeded_urls,
                                       batch_download)

    def _update_and_save_progress(self, failed_urls, succeeded_urls,
                                  batch_download):
        self.total_failed += len(failed_urls)
        self.total_downloaded += len(succeeded_urls)
        self._file_index = batch_download.file_index
        self._category_counts = batch_download.category_counts

        self._last_result = Result(
            failed_urls=failed_urls,
            succeeded_urls=succeeded_urls
        )

        self.save()

    def save(self):
        failed_urls = self.last_result.failed_urls
        succeeded_urls = self.last_result.succeeded_urls

        d = {
            'destination': self.destination,
            'number_of_images': self.number_of_images,
            'images_per_category': self.images_per_category,
            'batch_size': self.batch_size,
            'total_downloaded': self.total_downloaded,
            'total_failed': self.total_failed,
            'configured': self._configured,
            'finished': self.finished,
            'failed_urls': failed_urls,
            'succeeded_urls': succeeded_urls,
            'position': self._last_position.to_json(),
            'category_counts': self._category_counts,
            'file_index': self._file_index
        }

        path = config.download_state_path
        with open(path, 'w') as f:
            f.write(json.dumps(d))

    def configure(self, conf):
        self._set_defaults()

        self.destination = conf.download_destination
        self.number_of_images = conf.number_of_images
        self.images_per_category = conf.images_per_category
        self.batch_size = conf.batch_size
        self._configured = True

    @property
    def configuration(self):
        return DownloadConfiguration(
            number_of_images=self.number_of_images,
            images_per_category=self.images_per_category,
            download_destination=self.destination,
            batch_size=self.batch_size
        )

    @property
    def last_result(self):
        return self._last_result


class ProductionFactory:
    def new_threading_downloader(self):
        return ThreadingDownloader()


class TestFactory:
    def new_threading_downloader(self):
        return TestThreadingDownloader()


def get_factory():
    if os.getenv('TEST_ENV'):
        return TestFactory()
    else:
        return ProductionFactory()


class NotConfiguredError(Exception):
    pass
