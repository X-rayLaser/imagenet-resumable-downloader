import requests
import shutil
import os
import json
from urllib.parse import urlparse
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from time import time

app_data_folder = 'imagenet_data'


# todo: ImagenetDataDirectory
# todo: Lazy creation of directories when accessing them


class LinesIterator:
    def file_path(self):
        raise NotImplementedError

    def __iter__(self):
        file_path = self.file_path()
        with open(file_path) as f:
            for line in f:
                yield line.rstrip()


class WordNetIdList(LinesIterator):
    synsets_url = 'http://www.image-net.org/api/text/imagenet.synset.obtain_synset_list'
    timeout = 120

    def __init__(self, wn_ids_path):
        self.wn_ids_path = wn_ids_path
        self._download_list()

    def file_path(self):
        return self.wn_ids_path

    def _download_list(self):
        if not os.path.isfile(self.wn_ids_path):
            print('No file is found. Downloading the list')
            r = requests.get(self.synsets_url, stream=True, timeout=self.timeout)
            with open(self.wn_ids_path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)


class Synset(LinesIterator):
    timeout = 120

    def __init__(self, wn_id):
        file_name = 'synset_urls_{}.txt'.format(wn_id)
        self.synset_urls_path = os.path.join(app_data_folder, file_name)
        self._download_list(wn_id)

        self._lines = []
        with open(self.synset_urls_path) as f:
            self._lines = [line for line in f]

        self._lines_iterator = self._lines.__iter__()

    def file_path(self):
        return self.synset_urls_path

    def _download_list(self, wn_id):
        url = 'http://www.image-net.org/api/text/imagenet.synset.geturls?' \
              'wnid={}'.format(wn_id)

        if not os.path.isfile(self.synset_urls_path):
            print('No sysnset urls file is found. Downloading the list from {}'.format(url))

            r = requests.get(url, stream=True, timeout=self.timeout)
            code = r.status_code
            if code != requests.codes.ok:
                raise Exception(code)

            with open(self.synset_urls_path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)


class ImageNetUrls:
    def __init__(self, word_net_ids, wnid2synset, batch_size=1000):
        if batch_size <= 0:
            raise InvalidBatchError()

        self._word_net_ids = word_net_ids
        self._wnid2synset = wnid2synset
        self._batch_size = batch_size

    def __iter__(self):
        for wn_id in self._word_net_ids:
            synset = self._wnid2synset(wn_id)

            batch = []
            for url in synset:
                if not self._valid_url(url):
                    continue

                batch.append(url)
                if len(batch) >= self._batch_size:
                    yield (wn_id, batch)
                    batch = []
            if batch:
                yield (wn_id, batch)

    def _valid_url(self, url):
        return url.rstrip() != '' and url.lstrip() != ''


def url_to_file_path(destination_dir, url):
    file_name = os.path.basename(urlparse(url).path)
    return os.path.join(destination_dir, file_name)


class FileDownloader:
    def __init__(self, destination, timeout=1):
        self.destination = destination
        self._timeout = timeout

    def download(self, url):
        file_path = self.destination
        try:
            r = requests.get(url, stream=True, timeout=self._timeout)
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
    def __init__(self, destination, timeout=2):
        self.destination = destination
        self._timeout = timeout

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
        import random
        return random.random() > 0.5


class ItemsRegistry:
    def __init__(self, registry_path):
        self._registry_path = registry_path
        self._registry = set()

        if os.path.isfile(registry_path):
            with open(registry_path, 'r') as f:
                json_str = f.read()

            self._registry = set(json.loads(json_str))

    def add(self, name):
        self._registry.add(name)
        self._save()

    def remove(self, name):
        if name in self._registry:
            self._registry.remove(name)
            self._save()

    def __len__(self):
        return len(self._registry)

    def __contains__(self, name):
        return name in self._registry

    def _save(self):
        to_be_saved = json.dumps(list(self._registry))

        with open(self._registry_path, 'w') as f:
            f.writelines(to_be_saved)


class Url2FileName:
    def __init__(self, file_name_registry):
        self._registry = file_name_registry
        self._index = len(self._registry) + 1

    def convert(self, url):
        if url.rstrip() != url:
            raise MalformedUrlError('Trailing new line character')

        # todo check url has no trailing new line
        fname = self._url_to_file_name(url)
        base_name, extension = os.path.splitext(fname)

        converted_name = str(self._index) + extension
        assert converted_name not in self._registry

        self._registry.add(converted_name)
        self._index += 1
        return converted_name

    def _url_to_file_name(self, url):
        return os.path.basename(urlparse(url).path)


class ThreadingDownloader:
    max_workers = 1000
    pool = ThreadPoolExecutor(max_workers=max_workers)

    def __init__(self, destination, url2file_name):
        self.destination = destination
        self._url2file_name = url2file_name

    def download(self, urls):
        args = [(url, self._url2file_name.convert(url)) for url in urls]
        pool = self.pool
        statuses = list(pool.map(self._download, args))
        successes = sum(statuses)
        return successes

    def _download(self, args):
        image_url, file_name = args
        file_path = os.path.join(self.destination, file_name)
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


class ImageNet:
    wn_ids_path = os.path.join(app_data_folder, 'word_net_ids.txt')
    registry_path = os.path.join(app_data_folder, 'file-name-registry.json')

    @staticmethod
    def wnid2synset(wn_id):
        return Synset(wn_id=wn_id)

    def __init__(self, number_of_examples, destination, on_loaded):
        self.number_of_examples = number_of_examples
        self.downloaded = 0
        self.destination = destination
        self.training_set = []

        self._on_loaded = on_loaded
        self._timeout = 2
        self._wordnet_list = WordNetIdList(self.wn_ids_path)

    def download(self):
        #self._create_folders() # too many folders at once, hard to navigate them later
        self._download()

    def _create_folders(self):
        for wn_id in self._wordnet_list:
            folder_path = os.path.join(self.destination, str(wn_id))
            self._create_if_not_exist(folder_path)

    def _download(self):
        file_name_registry = ItemsRegistry(self.registry_path)
        url2file_name = Url2FileName(file_name_registry)

        image_net_urls = ImageNetUrls(word_net_ids=self._wordnet_list,
                                      wnid2synset=self.wnid2synset)

        for wn_id, urls in image_net_urls:
            folder_path = os.path.join(self.destination, str(wn_id))
            self._create_if_not_exist(folder_path)
            threading_downloader = ThreadingDownloader(
                destination=folder_path, url2file_name=url2file_name
            )

            successes = threading_downloader.download(urls)
            self.downloaded += successes
            self._on_loaded(successes)

            if self.downloaded >= self.number_of_examples:
                break

    def _create_if_not_exist(self, dir_path):
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)


class MalformedUrlError(Exception):
    pass


class InvalidBatchError(Exception):
    pass
