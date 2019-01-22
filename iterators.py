import requests
import shutil
import os


from config import config


class FileLinesIterator:
    def __iter__(self):
        self._download_list()
        file_path = self.file_path
        with open(file_path) as f:
            for line in f:
                yield line.rstrip()

    def _download_list(self):
        if not os.path.isfile(self.file_path):
            print('No file is found. Downloading the list')
            r = requests.get(self.url, stream=True, timeout=self.timeout)
            code = r.status_code
            if code != requests.codes.ok:
                raise Exception(code)

            with open(self.file_path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)


class WordNetIdList(FileLinesIterator):
    def __init__(self, wn_ids_path):
        self.file_path = wn_ids_path
        self.url = config.synsets_url
        self.timeout = config.word_net_ids_timeout


class Synset(FileLinesIterator):
    def __init__(self, wn_id):
        self.file_path = config.synset_urls_path(wn_id)
        self.url = config.synset_download_url(wn_id)
        self.timeout = config.synsets_timeout


# todo: method def offset(wn_id, url)
# todo: DownloadManager class (start, pause, resume)
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
