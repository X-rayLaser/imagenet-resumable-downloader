import requests
import shutil
import os
from urllib.parse import urlparse
from PIL import Image
from concurrent.futures import ThreadPoolExecutor


# todo: fix \n in the synset urls
# todo: transform file names (remove bad characters)


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
        self.synset_urls_path = 'synset_urls_{}.txt'.format(wn_id)
        self._download_list(wn_id)

        self._lines = []
        with open(self.synset_urls_path) as f:
            self._lines = [line for line in f]

        self._lines_iterator = self._lines.__iter__()

    def file_path(self):
        return self.synset_urls_path

    def next_batch(self, size):
        lines = []
        try:
            for i in range(size):
                lines.append(next(self._lines_iterator))
        except StopIteration:
            print('StopIteration')
            pass
        return lines

    def _download_list(self, wn_id):
        url = 'http://www.image-net.org/api/text/imagenet.synset.geturls?' \
              'wnid={}'.format(wn_id)

        if not os.path.isfile(self.synset_urls_path):
            print('No sysnset urls file is found. Downloading the list from {}'.format(url))

            r = requests.get(url, timeout=self.timeout)
            code = r.status_code
            if code != requests.codes.ok:
                raise Exception(code)

            with open(self.synset_urls_path, 'wb') as f:
                urls = r.text
                print(urls)
                f.write(urls)


def url_to_file_path(destination_dir, url):
    file_name = os.path.basename(urlparse(url).path)
    return os.path.join(destination_dir, file_name)


class FileDownloader:
    def __init__(self, destination, timeout=2):
        self.destination = destination
        self._timeout = timeout

    def download(self, url):
        file_path = url_to_file_path(self.destination, url)
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
            import traceback
            traceback.print_exc()
            return False


class DummyDownloader:
    def __init__(self, destination, timeout=2):
        self.destination = destination
        self._timeout = timeout

    def download(self, url):
        import time
        import random
        #time.sleep(2 * random.random())
        file_path = url_to_file_path(self.destination, url)
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
        import random
        return random.random() > 0.5


class ThreadingDownloader:
    def __init__(self, destination):
        self.destination = destination

    def download(self, urls):
        pool = ThreadPoolExecutor(max_workers=100)
        statuses = list(map(self._download, urls))
        successes = sum(statuses)
        return successes

    def _download(self, image_url):
        file_path = url_to_file_path(self.destination, image_url)
        #downloader = FileDownloader(destination=self.destination)
        downloader = DummyDownloader(destination=self.destination)
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
    wn_ids_path = 'word_net_ids.txt'

    def __init__(self, number_of_examples, destination, on_loaded):
        self.number_of_examples = number_of_examples
        self.downloaded = 0
        self.destination = destination
        self.training_set = []

        self._on_loaded = on_loaded
        self._timeout = 2

    def download(self):
        from time import time
        start = time()
        wordnet_list = WordNetIdList(self.wn_ids_path)

        for wn_id in wordnet_list:
            folder_path = os.path.join(self.destination, str(wn_id))
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)

            threading_downloader = ThreadingDownloader(destination=folder_path)

            synset = Synset(wn_id=wn_id)

            while True:
                urls = synset.next_batch(
                    size=self.number_of_examples - self.downloaded
                )

                successes = threading_downloader.download(urls)
                self.downloaded += successes
                self._on_loaded(successes)

                if self.downloaded >= self.number_of_examples:
                    end = time()
                    print('Took %.3f seconds' % (end - start))
                    return
