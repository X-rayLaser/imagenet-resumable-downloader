import requests
import shutil
import os
from PIL import Image
import iterators
from util import Url2FileName
from config import config


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

    def __init__(self, destination):
        self._destination = destination
        self.downloaded_urls = []
        self.failed_urls = []

    def download(self, urls, file_names):
        self.downloaded_urls = []
        self.failed_urls = []

        args = zip(urls, file_names)
        pool = self.pool
        results = list(pool.map(self._download, args))

        for url, success in zip(urls, results):
            if success:
                self.downloaded_urls.append(url)
            else:
                self.failed_urls.append(url)

    def _download(self, args):
        image_url, file_name = args
        file_path = os.path.join(self._destination, file_name)
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
    def new_threading_downloader(self, destination):
        raise Exception('oopse')
        return ThreadingDownloader(destination)


class TestFactory:
    def new_threading_downloader(self, destination):
        return TestThreadingDownloader(destination)


def get_factory():
    if os.getenv('TEST_ENV'):
        return TestFactory()
    else:
        return ProductionFactory()
