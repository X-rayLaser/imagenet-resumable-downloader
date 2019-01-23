import requests
import shutil
import os
from config import config


def read_by_lines(file_path):
    with open(file_path) as f:
        for line in f:
            yield line.strip()


# todo: method def offset(wn_id, url)
# todo: DownloadManager class (start, pause, resume)
class ImageNetUrls:
    def __init__(self, batch_size=1000):
        if batch_size <= 0:
            raise InvalidBatchError()

        self._batch_size = batch_size

    def fetch_wordnet_ids(self):
        raise Exception('Should create instance of ImageNetUrlsMocked, not ImageNetUrls!')

        destination = config.wn_ids_path

        if self._file_is_missing(destination):
            self._download_list(config.synsets_url, destination,
                                config.word_net_ids_timeout)

    def fetch_url_list(self, word_net_id):
        raise Exception('Should create instance of ImageNetUrlsMocked, not ImageNetUrls!')

        destination = config.synset_urls_path(word_net_id)
        if self._file_is_missing(destination):
            url = config.synset_download_url(word_net_id=word_net_id)
            self._download_list(url, destination, config.synsets_timeout)

    def _file_is_missing(self, path):
        return not os.path.isfile(path)

    def _download_list(self, url, destination, timeout):
        print('No file is found. Downloading the list')
        r = requests.get(url, stream=True, timeout=timeout)
        code = r.status_code
        if code != requests.codes.ok:
            raise Exception(code)

        with open(destination, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

    def __iter__(self):
        self.fetch_wordnet_ids()

        word_net_ids = read_by_lines(config.wn_ids_path)
        for wn_id in word_net_ids:
            self.fetch_url_list(wn_id)
            path = config.synset_urls_path(wn_id)

            synset = read_by_lines(path)

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


class ImageNetUrlsMocked(ImageNetUrls):
    def fetch_wordnet_ids(self):
        os.makedirs(config.app_data_folder, exist_ok=True)
        destination = config.wn_ids_path
        fixture_path = os.path.join('fixtures', 'word_net_ids.txt')
        shutil.copyfile(fixture_path, destination)

    def fetch_url_list(self, word_net_id):
        os.makedirs(config.app_data_folder, exist_ok=True)
        destination = config.synset_urls_path(word_net_id)
        file_name = 'synset_urls_{}.txt'.format(word_net_id)
        fixture_path = os.path.join('fixtures', file_name)
        shutil.copyfile(fixture_path, destination)


def create_image_net_urls(batch_size=1000):
    if os.getenv('TEST_ENV'):
        return ImageNetUrlsMocked(batch_size)
    else:
        return ImageNetUrls(batch_size)


class InvalidBatchError(Exception):
    pass
