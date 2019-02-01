import os

from image_net.downloader import get_factory
from image_net.util import Url2FileName


class BatchDownload:
    def __init__(self, dataset_root, number_of_images=100,
                 images_per_category=100, batch_size=100, starting_index=1):
        self.on_fetched = lambda failed, succeeded : None
        self.on_complete = lambda: None

        self._location = DownloadLocation(dataset_root)
        self._pending = []
        self._batch_size = batch_size
        self._max_images = number_of_images
        self._images_per_category = images_per_category
        self._total_downloaded = 0

        self._url2file_name = Url2FileName(starting_index=starting_index)

        self._category_counts = {}

        self._threading_downloader = get_factory().new_threading_downloader()

    def set_counts(self, counts):
        self._category_counts = dict(counts)

    @property
    def category_counts(self):
        return dict(self._category_counts)

    @property
    def file_index(self):
        return self._url2file_name.file_index

    @property
    def batch_ready(self):
        return len(self._pending) >= self._batch_size

    @property
    def complete(self):
        return self._total_downloaded >= self._max_images

    @property
    def is_empty(self):
        return len(self._pending) == 0

    def flush(self):
        paths = self._file_paths()
        urls = self._url_batch()

        failed_urls, succeeded_urls = self.do_download(urls, paths)

        self._total_downloaded += len(succeeded_urls)
        if self._total_downloaded >= self._max_images:
            self.on_complete()

        self._update_category_counts(succeeded_urls)

        self.on_fetched(failed_urls, succeeded_urls)
        self._clear_buffer()

        return failed_urls, succeeded_urls

    def _update_category_counts(self, succeeded_urls):
        url_to_wn_id = {}
        for wn_id, url in self._pending:
            if wn_id not in url_to_wn_id:
                if url not in url_to_wn_id:
                    url_to_wn_id[url] = []
                url_to_wn_id[url].append(wn_id)

        for url in succeeded_urls:
            wn_ids = url_to_wn_id[url]
            for wn_id in wn_ids:
                self._category_counts[wn_id] += 1

    def _file_paths(self):
        paths = []

        for wn_id, url in self._pending:
            folder_path = self._location.category_path(wn_id)
            file_name = self._url2file_name.convert(url)

            path = os.path.join(folder_path, file_name)
            paths.append(path)
        return paths

    def _url_batch(self):
        return [url for _, url in self._pending]

    def _clear_buffer(self):
        self._pending[:] = []

    def do_download(self, urls, destinations):
        self._threading_downloader.download(urls, destinations)
        failed_urls = self._threading_downloader.failed_urls
        succeeded_urls = self._threading_downloader.downloaded_urls
        return failed_urls, succeeded_urls

    def add(self, wn_id, url):
        if wn_id not in self._category_counts:
            self._category_counts[wn_id] = 0

        if self._category_counts[wn_id] < self._images_per_category:
            self._pending.append((wn_id, url))


class DownloadLocation:
    def __init__(self, destination_path):
        self._destination = destination_path

    def category_path(self, word_net_id):
        folder_path = os.path.join(self._destination, str(word_net_id))
        self._create_if_not_exist(folder_path)
        return folder_path

    def _create_if_not_exist(self, dir_path):
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
