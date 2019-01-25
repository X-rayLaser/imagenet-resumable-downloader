import requests
import shutil
import os
import json
from config import config


def read_by_lines(file_path):
    with open(file_path) as f:
        for line in f:
            yield line.strip()


class Position:
    def __init__(self, word_id_offset, url_offset):
        self.word_id_offset = word_id_offset
        self.url_offset = url_offset

    def next_id(self):
        self.word_id_offset += 1
        self.url_offset = 0

    def next_url(self):
        self.url_offset += 1

    def to_json(self):
        d = {
            'word_id_offset': self.word_id_offset,
            'url_offset': self.url_offset
        }
        return json.dumps(d)

    @staticmethod
    def from_json(s):
        d = json.loads(s)
        return Position(**d)

    def __lt__(self, other):
        if self.word_id_offset < other.word_id_offset:
            return True

        if self.word_id_offset > other.word_id_offset:
            return False

        return self.url_offset < other.url_offset

    def __eq__(self, other):
        return self.word_id_offset == other.word_id_offset and \
               self.url_offset == other.url_offset

    def __le__(self, other):
        return self < other or self == other


class ImageNetUrls:
    def __init__(self, start_after_position=None):
        if start_after_position is None:
            self._start_after_position = Position(-1, -1)
        else:
            self._start_after_position = start_after_position

    def fetch_wordnet_ids(self):
        destination = config.wn_ids_path

        if self._file_is_missing(destination):
            self._download_list(config.synsets_url, destination,
                                config.word_net_ids_timeout)

    def fetch_url_list(self, word_net_id):
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

    def _create_storage_directory(self):
        os.makedirs(config.app_data_folder, exist_ok=True)

    def __iter__(self):
        self._create_storage_directory()
        self.fetch_wordnet_ids()

        word_net_ids = read_by_lines(config.wn_ids_path)

        position = Position(0, 0)
        for wn_id in word_net_ids:
            if position.word_id_offset < self._start_after_position.word_id_offset:
                position.next_id()
                continue

            self.fetch_url_list(wn_id)
            path = config.synset_urls_path(wn_id)

            synset = read_by_lines(path)

            for url in synset:
                if self._valid_url(url):
                    if position <= self._start_after_position:
                        position.next_url()
                        continue

                    yield (wn_id, url, position)
                    position.next_url()

            position.next_id()

    def _valid_url(self, url):
        return url.rstrip() != '' and url.lstrip() != ''


class ImageNetUrlsMocked(ImageNetUrls):
    def fetch_wordnet_ids(self):
        destination = config.wn_ids_path
        fixture_path = os.path.join('fixtures', 'word_net_ids.txt')
        shutil.copyfile(fixture_path, destination)

    def fetch_url_list(self, word_net_id):
        destination = config.synset_urls_path(word_net_id)
        file_name = 'synset_urls_{}.txt'.format(word_net_id)
        fixture_path = os.path.join('fixtures', file_name)
        shutil.copyfile(fixture_path, destination)


def create_image_net_urls(start_after_position=None):
    if os.getenv('TEST_ENV'):
        return ImageNetUrlsMocked(start_after_position)
    else:
        return ImageNetUrls(start_after_position=None)


class InvalidBatchError(Exception):
    pass
