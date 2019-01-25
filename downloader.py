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


class ImageNet:
    def __init__(self, number_of_examples, images_per_category,
                 destination, on_loaded, on_failed):
        self.number_of_examples = number_of_examples
        self.images_per_category = images_per_category
        self.downloaded = 0
        self._location = DownloadLocation(destination)
        self.training_set = []

        self._on_loaded = on_loaded
        self._on_failed = on_failed
        self._timeout = 2

    def download(self):
        url2file_name = Url2FileName()

        image_net_urls = iterators.create_image_net_urls()

        factory = get_factory()

        for wn_id, urls in image_net_urls:
            folder_path = self._location.category_path(wn_id)
            threading_downloader = factory.new_threading_downloader(
                destination=folder_path
            )

            batch = urls[:self.images_per_category]
            file_names = [url2file_name.convert(url) for url in batch]
            threading_downloader.download(batch, file_names)

            self._on_loaded(threading_downloader.downloaded_urls)
            self._on_failed(threading_downloader.failed_urls)

            self.downloaded += len(threading_downloader.downloaded_urls)

            if self.downloaded >= self.number_of_examples:
                break


class DownloadConfiguration:
    def __init__(self, number_of_images,
                 images_per_category,
                 download_destination):
        self.number_of_images = number_of_images
        self.images_per_category = images_per_category
        self.download_destination = download_destination


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


class PendingDownloadsBuffer:
    def __init__(self, batch_size):
        self._batch_size = batch_size

    def add(self):
        pass

    def prepare_batch(self):
        return [], []

    def is_full(self):
        return True


class CategoryCounter:
    def __init__(self, elememts_limit):
        self._elememts_limit = elememts_limit
        self._category_counts = {}

    def add(self, wn_id, url):
        if wn_id not in self._category_counts:
            self._category_counts[wn_id] = 0
        self._category_counts[wn_id] += 1

    def reached_limit(self, wn_id):
        if wn_id not in self._category_counts:
            return False
        return self._category_counts[wn_id] >= self._elememts_limit


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

    def flush(self):
        url_to_wn_id = {}

        paths = []
        for wn_id, url in self._pending:
            folder_path = self._location.category_path(wn_id)
            file_name = self._url2file_name.convert(url)

            path = os.path.join(folder_path, file_name)
            paths.append(path)

            if wn_id not in url_to_wn_id:
                if url not in url_to_wn_id:
                    url_to_wn_id[url] = []
                url_to_wn_id[url].append(wn_id)

        urls = [url for _, url in self._pending]

        failed_urls, succeeded_urls = self.do_download(urls, paths)

        self.on_fetched(failed_urls, succeeded_urls)

        self._clear_buffer()

        self._total_downloaded += len(succeeded_urls)
        if self._total_downloaded >= self._max_images:
            self.on_complete()

        for url in succeeded_urls:
            wn_ids = url_to_wn_id[url]
            for wn_id in wn_ids:
                self._category_counts[wn_id] += 1

    def _clear_buffer(self):
        self._pending[:] = []

    def do_download(self, urls, destinations):
        pass

    def add(self, wn_id, url):
        if wn_id not in self._category_counts:
            self._category_counts[wn_id] = 0

        if self._category_counts[wn_id] < self._images_per_category:
            self._pending.append((wn_id, url))
            if len(self._pending) >= self._batch_size:
                self.flush()


class StatefulDownloader:
    def __init__(self):
        self.destination = None
        self.number_of_images = 0
        self.images_per_category = 0
        self.total_downloaded = 0
        self.total_failed = 0

        self._configured = False
        self.finished = False
        self._last_result = None

        try:
            self._restore_from_file()
        except json.decoder.JSONDecodeError:
            pass
        except KeyError:
            pass

    def _restore_from_file(self):
        path = config.download_state_path
        if os.path.isfile(path):
            with open(path, 'r') as f:
                s = f.read()
                d = json.loads(s)
            self.destination = d['destination']
            self.number_of_images = d['number_of_images']
            self.images_per_category = d['images_per_category']
            self.total_downloaded = d['total_downloaded']
            self.total_failed = d['total_failed']
            self._configured = d['configured']
            self.finished = d['finished']

            failed_urls = d['failed_urls']
            succeeded_urls = d['succeeded_urls']
            self._last_result = Result(failed_urls, succeeded_urls)

    def __iter__(self):
        if not self._configured:
            raise NotConfiguredError()

        self._location = DownloadLocation(self.destination)

        url2file_name = Url2FileName()

        image_net_urls = iterators.create_image_net_urls()

        factory = get_factory()

        buffer = PendingDownloadsBuffer(batch_size=100)
        counter = CategoryCounter(self.images_per_category)

        threading_downloader = factory.new_threading_downloader()

        for wn_id, url, position in image_net_urls:
            if counter.reached_limit(wn_id):
                continue

            buffer.add()
            if buffer.is_full():
                batch = buffer.prepare_batch()

                url_to_wnid = {}
                for word_net_id, url in batch:
                    url_to_wnid[url] = word_net_id



                threading_downloader.download(urls, file_names)

                self.total_failed += len(threading_downloader.failed_urls)
                self.total_downloaded += len(threading_downloader.downloaded_urls)

                for url in threading_downloader.downloaded_urls:
                    counter.add(url_to_wnid[url], url)

                self._last_result = Result(
                    failed_urls=threading_downloader.failed_urls,
                    succeeded_urls=threading_downloader.downloaded_urls
                )

                self.save()
                yield self._last_result

            #folder_path = self._location.category_path(wn_id)

            #file_names = [url2file_name.convert(url) for url in batch]

        self.finished = True
        self.save()

    def save(self):
        failed_urls = self.last_result.failed_urls
        succeeded_urls = self.last_result.succeeded_urls

        d = {
            'destination': self.destination,
            'number_of_images': self.number_of_images,
            'images_per_category': self.images_per_category,
            'total_downloaded': self.total_downloaded,
            'total_failed': self.total_failed,
            'configured': self._configured,
            'finished': self.finished,
            'failed_urls': failed_urls,
            'succeeded_urls': succeeded_urls
        }

        path = config.download_state_path
        with open(path, 'w') as f:
            f.write(json.dumps(d))

    def configure(self, conf):
        self.destination = conf.download_destination
        self.number_of_images = conf.number_of_images
        self.images_per_category = conf.images_per_category
        self._configured = True

    @property
    def configuration(self):
        return DownloadConfiguration(
            number_of_images=self.number_of_images,
            images_per_category=self.images_per_category,
            download_destination=self.destination
        )

    @property
    def last_result(self):
        return self._last_result


class Counter:
    def update(self, count):
        pass

    def is_complete(self):
        pass


# todo: fix DownloadManager, make it thread-safe
# todo: test DownloadManger with fake urls (and fake wn_id list)
# todo: use ImageNet class in DownloadManger
# todo: ImageNetUrls iterator must return only one url at a time


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
