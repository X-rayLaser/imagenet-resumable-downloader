import requests
import shutil
import os
from urllib.parse import urlparse
from PIL import Image


class WordNetIdList:
    synsets_url = 'http://www.image-net.org/api/text/imagenet.synset.obtain_synset_list'
    wn_ids_path = 'word_net_ids.txt'
    timeout = 120

    def __init__(self):
        self._download_list()

    def __iter__(self):
        with open(self.wn_ids_path) as f:
            for line in f:
                yield line

    def _download_list(self):
        if not os.path.isfile(self.wn_ids_path):
            print('No file is found. Downloading the list')
            r = requests.get(self.synsets_url, stream=True, timeout=self.timeout)
            with open(self.wn_ids_path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)


class Synset:
    timeout = 120

    def __init__(self, wn_id):
        self.synset_urls_path = 'synset_urls_{}.txt'.format(wn_id)
        self._download_list(wn_id)

    def __iter__(self):
        with open(self.synset_urls_path) as f:
            for line in f:
                yield line

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


class ImageNet:
    def __init__(self, number_of_examples, destination, on_loaded):
        self.number_of_examples = number_of_examples
        self.downloaded = 0
        self.destination = destination
        self.training_set = []

        self._on_loaded = on_loaded
        self._timeout = 2

    def download(self):
        wordnet_list = WordNetIdList()

        for wn_id in wordnet_list:
            synset = Synset(wn_id=wn_id)

            for image_url in synset:
                if self.downloaded >= self.number_of_examples:
                    return

                self.downloaded += self._download_image(image_url)
                print(self.downloaded, image_url)

    def _download_image(self, image_url):
        print('loading image', image_url)
        file_path = self._file_path(image_url)
        try:
            r = requests.get(image_url, stream=True, timeout=self._timeout)
            code = r.status_code
            if code == requests.codes.ok:
                with open(file_path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)

                if self._valid_image(file_path):
                    self._on_loaded()
                    return 1
                else:
                    os.remove(file_path)
                    return 0
            else:
                print('Bad code {}. Url {}'.format(code, image_url))
                return 0
        except Exception as e:
            import traceback
            traceback.print_exc()
            return 0

    def _valid_image(self, path):
        try:
            Image.open(path)
            return True
        except IOError:
            return False

    def _file_path(self, image_url):
        file_name = os.path.basename(urlparse(image_url).path)
        return os.path.join(self.destination, file_name)
