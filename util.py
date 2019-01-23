import os
import json
from urllib.parse import urlparse


def url_to_file_path(destination_dir, url):
    file_name = os.path.basename(urlparse(url).path)
    return os.path.join(destination_dir, file_name)


class Url2FileName:
    def __init__(self, starting_index=1):
        self._index = starting_index

    def convert(self, url):
        if url.rstrip() != url:
            raise MalformedUrlError('Trailing new line character')

        fname = self._url_to_file_name(url)
        base_name, extension = os.path.splitext(fname)

        converted_name = str(self._index) + extension

        self._index += 1
        return converted_name

    def _url_to_file_name(self, url):
        return os.path.basename(urlparse(url).path)


class MalformedUrlError(Exception):
    pass
