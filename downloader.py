import requests
import shutil
import os
from urllib.parse import urlparse


class ImageNet:
    synsets_url = 'http://www.image-net.org/api/text/imagenet.synset.obtain_synset_list'

    def __init__(self, number_of_examples, destination):
        self.number_of_examples = number_of_examples
        self.downloaded = 0
        self.destination = destination
        self.training_set = []

    def download(self):
        synsets_url = self.synsets_url
        r = requests.get(synsets_url)

        wn_ids = r.text.splitlines()
        for wn_id in wn_ids:
            url = 'http://www.image-net.org/api/text/imagenet.synset.geturls?' \
                  'wnid={}'.format(wn_id)

            r = requests.get(url)
            image_urls = r.text.splitlines()

            print('wn_id', wn_id)
            print('urls',image_urls)

            for image_url in image_urls:
                if self.downloaded >= self.number_of_examples:
                    return

                self.downloaded += self._download_image(image_url)
                print(self.downloaded, image_url)

    def _download_image(self, image_url):
        print('loading image', image_url)
        file_path = self._file_path(image_url)
        try:
            r = requests.get(image_url, stream=True, timeout=5)
            code = r.status_code
            if code == requests.codes.ok:
                with open(file_path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
                return 1
            else:
                print('Bad code {}. Url {}'.format(code, image_url))
                return 0
        except Exception as e:
            import traceback
            traceback.print_exc()
            return 0

    def _file_path(self, image_url):
        file_name = os.path.basename(urlparse(image_url).path)
        return os.path.join(self.destination, file_name)
