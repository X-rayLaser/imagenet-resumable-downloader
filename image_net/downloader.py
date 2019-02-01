# <pyqt-robot - a small Selenium-like API for testing GUI apps written with PyQt.>
# Copyright © 2019 Evgenii Dolotov. Contacts <supernovaprotocol@gmail.com>
# Author: Evgenii Dolotov
# License: https://www.gnu.org/licenses/gpl-3.0.txt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import requests
import shutil
import os
from PIL import Image
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
            f.write('Dummy downloader written file')
        return True


class ImageValidator:
    def valid_image(self, path):
        try:
            Image.open(path)
            return True
        except IOError:
            return False


class DummyValidator:
    def __init__(self):
        self._count = 0

    def valid_image(self, path):
        self._count += 1
        return self._count % 2


class ThreadingDownloader:
    pool = config.pool_executor

    def __init__(self):
        self.downloaded_urls = []
        self.failed_urls = []

    def download(self, urls, destinations):
        self.downloaded_urls = []
        self.failed_urls = []

        args = zip(urls, destinations)
        pool = self.pool
        results = list(pool.map(self._download, args))

        for url, success in zip(urls, results):
            if success:
                self.downloaded_urls.append(url)
            else:
                self.failed_urls.append(url)

    def _download(self, args):
        image_url, file_path = args
        downloader = self.get_file_downloader(destination=file_path)
        success = downloader.download(image_url)

        validator = self.get_validator()
        if success:
            if validator.valid_image(file_path):
                return True
            else:
                os.remove(file_path)
                return False
        else:
            return False

    def get_file_downloader(self, destination):
        return FileDownloader(destination=destination)

    def get_validator(self):
        return ImageValidator()


class TestThreadingDownloader(ThreadingDownloader):
    def get_file_downloader(self, destination):
        return DummyDownloader(destination=destination)

    def get_validator(self):
        return DummyValidator()


class ProductionFactory:
    def new_threading_downloader(self):
        return ThreadingDownloader()


class TestFactory:
    def new_threading_downloader(self):
        return TestThreadingDownloader()


def get_factory():
    if os.getenv('TEST_ENV'):
        return TestFactory()
    else:
        return ProductionFactory()
