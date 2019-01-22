import requests
import shutil
import os
from PIL import Image
from iterators import WordNetIdList, Synset, ImageNetUrls
from util import ItemsRegistry, Url2FileName
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
    @staticmethod
    def valid_image(path):
        try:
            Image.open(path)
            return True
        except IOError:
            return False


class DummyValidator:
    @staticmethod
    def valid_image(path):
        import random
        return random.random() > 0.5


class ThreadingDownloader:
    pool = config.pool_executor

    def __init__(self, destination, url2file_name):
        self._destination = destination
        self._url2file_name = url2file_name

        self.downloaded_urls = []
        self.failed_urls = []

    def download(self, urls):
        self.downloaded_urls = []
        self.failed_urls = []

        args = [(url, self._url2file_name.convert(url)) for url in urls]
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

        Validator = self.get_validator()
        if success:
            if Validator.valid_image(file_path):
                return True
            else:
                os.remove(file_path)
                return False
        else:
            return False

    def get_file_downloader(self, destination):
        return FileDownloader(destination=destination)

    def get_validator(self):
        return ImageValidator


class TestThreadingDownloader(ThreadingDownloader):
    def get_file_downloader(self, destination):
        return DummyDownloader(destination=destination)

    def get_validator(self):
        return DummyValidator


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
    @staticmethod
    def wnid2synset(wn_id):
        return Synset(wn_id=wn_id)

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
        self._wordnet_list = WordNetIdList(config.wn_ids_path)

    def download(self):
        file_name_registry = ItemsRegistry(config.registry_path)
        url2file_name = Url2FileName(file_name_registry)

        image_net_urls = ImageNetUrls(word_net_ids=self._wordnet_list,
                                      wnid2synset=self.wnid2synset)

        factory = get_factory()

        for wn_id, urls in image_net_urls:
            folder_path = self._location.category_path(wn_id)
            threading_downloader = factory.new_threading_downloader(
                destination=folder_path, url2file_name=url2file_name
            )

            batch = urls[:self.images_per_category]
            threading_downloader.download(batch)

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


class UltimateDownloader:
    def load_next_batch(self):
        return [], []

    def save(self, fname):
        pass

    def load(self, fname):
        pass


from PyQt5.QtCore import QThread, pyqtSignal


# todo: fix DownloadManager, make it thread-safe
# todo: test DownloadManger with fake urls (and fake wn_id list)
# todo: use ImageNet class in DownloadManger
# todo: ImageNetUrls iterator must return only one url at a time


class StoppableDownloader(QThread):
    paused = pyqtSignal()
    resumed = pyqtSignal()

    imageLoaded = pyqtSignal(list)
    downloadFailed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._running = False
        self._downloader = UltimateDownloader()
        self._counter = Counter()

    def run(self):
        self._running = True

        while True:
            self._wait_until_resumed()
            failed_urls, succeeded_urls = self._downloader.load_next_batch()
            self.downloadFailed.emit(failed_urls)
            self.imageLoaded.emit(succeeded_urls)

            successes = len(succeeded_urls)
            self._counter.update(successes)
            if self._counter.is_complete():
                # save state, etc.
                return

    def _wait_until_resumed(self):
        if not self._running:
            self.paused.emit()

        import time
        while True:
            time.sleep(0.5)
            if self._running:
                self.resumed.emit()
                break

    def pause(self):
        self._running = False

    def resume(self):
        self._running = True


class ProductionFactory:
    def new_threading_downloader(self, destination, url2file_name):
        raise Exception('oopse')
        return ThreadingDownloader(destination, url2file_name)


class TestFactory:
    def new_threading_downloader(self, destination, url2file_name):
        return TestThreadingDownloader(destination, url2file_name)


def get_factory():
    if os.getenv('TEST_ENV'):
        return TestFactory()
    else:
        return ProductionFactory()
