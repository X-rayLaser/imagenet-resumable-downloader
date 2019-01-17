import requests
import shutil
import os


from config import config


class LinesIterator:
    def file_path(self):
        raise NotImplementedError

    def __iter__(self):
        file_path = self.file_path()
        with open(file_path) as f:
            for line in f:
                yield line.rstrip()


class WordNetIdList(LinesIterator):
    synsets_url = config.synsets_url
    timeout = config.word_net_ids_timeout

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
    timeout = config.synsets_timeout

    def __init__(self, wn_id):
        self.synset_urls_path = config.synset_urls_path(wn_id)
        self._download_list(wn_id)

        self._lines = []
        with open(self.synset_urls_path) as f:
            self._lines = [line for line in f]

        self._lines_iterator = self._lines.__iter__()

    def file_path(self):
        return self.synset_urls_path

    def _download_list(self, wn_id):
        url = config.synset_download_url(wn_id)

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


class InvalidBatchError(Exception):
    pass
