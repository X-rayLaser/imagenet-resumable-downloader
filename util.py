import os
import json
from urllib.parse import urlparse


def url_to_file_path(destination_dir, url):
    file_name = os.path.basename(urlparse(url).path)
    return os.path.join(destination_dir, file_name)


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

        fname = self._url_to_file_name(url)
        base_name, extension = os.path.splitext(fname)

        converted_name = str(self._index) + extension
        assert converted_name not in self._registry

        self._registry.add(converted_name)
        self._index += 1
        return converted_name

    def _url_to_file_name(self, url):
        return os.path.basename(urlparse(url).path)


class MalformedUrlError(Exception):
    pass
