import requests
import shutil
import os
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from iterators import WordNetIdList, Synset, ImageNetUrls
from util import ItemsRegistry, Url2FileName
from config import config


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
            f.write('x' * 100)
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
        return True


class ThreadingDownloader:
    pool = config.pool_executor

    def __init__(self, destination, url2file_name):
        self._destination = destination
        self._url2file_name = url2file_name

    def download(self, urls):
        args = [(url, self._url2file_name.convert(url)) for url in urls]
        pool = self.pool
        statuses = list(pool.map(self._download, args))
        successes = sum(statuses)
        return successes

    def _download(self, args):
        image_url, file_name = args
        file_path = os.path.join(self._destination, file_name)
        #downloader = FileDownloader(destination=file_path)
        downloader = DummyDownloader(destination=file_path)
        success = downloader.download(image_url)

        Validator = DummyValidator
        if success:
            if Validator.valid_image(file_path):
                return 1
            else:
                os.remove(file_path)
                return 0
        else:
            return 0


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
                 destination, on_loaded):
        self.number_of_examples = number_of_examples
        self.images_per_category = images_per_category
        self.downloaded = 0
        self._location = DownloadLocation(destination)
        self.training_set = []

        self._on_loaded = on_loaded
        self._timeout = 2
        self._wordnet_list = WordNetIdList(config.wn_ids_path)

    def download(self):
        file_name_registry = ItemsRegistry(config.registry_path)
        url2file_name = Url2FileName(file_name_registry)

        image_net_urls = ImageNetUrls(word_net_ids=self._wordnet_list,
                                      wnid2synset=self.wnid2synset)

        for wn_id, urls in image_net_urls:
            folder_path = self._location.category_path(wn_id)
            threading_downloader = ThreadingDownloader(
                destination=folder_path, url2file_name=url2file_name
            )

            #category_images = []
            #while
            batch = urls[:self.images_per_category]
            successes = threading_downloader.download(batch)
            self.downloaded += successes
            self._on_loaded(successes)

            if self.downloaded >= self.number_of_examples:
                break
