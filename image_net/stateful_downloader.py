# <imagenet-resumable-downloader - a GUI based utility for getting ImageNet images>
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
import json
import os

from image_net import iterators
from config import config
from image_net.batch_download import BatchDownload


class StatefulDownloader:
    def __init__(self):
        self._set_defaults()

        try:
            self._restore_from_file()
        except json.decoder.JSONDecodeError:
            pass
        except KeyError:
            pass

    def _set_defaults(self):
        self.destination = None
        self.number_of_images = 0
        self.images_per_category = 0
        self.batch_size = 100
        self.total_downloaded = 0
        self.total_failed = 0

        self._configured = False
        self.finished = False
        self._last_result = None
        self._last_position = iterators.Position.null_position()
        self._category_counts = {}

        self._file_index = 1

    def _restore_from_file(self):
        path = config.download_state_path
        if os.path.isfile(path):
            with open(path, 'r') as f:
                s = f.read()
                d = json.loads(s)
            self.destination = d['destination']
            self.number_of_images = d['number_of_images']
            self.images_per_category = d['images_per_category']
            self.batch_size = d['batch_size']
            self.total_downloaded = d['total_downloaded']
            self.total_failed = d['total_failed']
            self._configured = d['configured']
            self.finished = d['finished']

            failed_urls = d['failed_urls']
            succeeded_urls = d['succeeded_urls']

            self._last_position = iterators.Position.from_json(d['position'])
            self._last_result = Result(failed_urls, succeeded_urls)

            self._category_counts = d['category_counts']

            self._file_index = d['file_index']

    def __iter__(self):
        if not self._configured:
            raise NotConfiguredError()

        images_left = self.number_of_images - self.total_downloaded

        batch_download = BatchDownload(dataset_root=self.destination,
                                       number_of_images=images_left,
                                       images_per_category=self.images_per_category,
                                       batch_size=self.batch_size,
                                       starting_index=self._file_index)

        batch_download.set_counts(self._category_counts)

        image_net_urls = iterators.create_image_net_urls(
            start_after_position=self._last_position
        )

        for wn_id, url, position in image_net_urls:
            batch_download.add(wn_id, url)

            if batch_download.batch_ready:
                failed_urls, succeeded_urls = batch_download.flush()
                self._update_and_save_progress(failed_urls, succeeded_urls,
                                               batch_download)

                if batch_download.complete:
                    self.finished = True
                yield self._last_result
                if batch_download.complete:
                    self.finished = True
                    break

            self._last_position = position
            self._category_counts = batch_download.category_counts

        self.finished = True
        if not batch_download.is_empty:
            self._finish_download(batch_download)
            yield self._last_result

    def _finish_download(self, batch_download):
        failed_urls, succeeded_urls = batch_download.flush()
        self._update_and_save_progress(failed_urls, succeeded_urls,
                                       batch_download)

    def _update_and_save_progress(self, failed_urls, succeeded_urls,
                                  batch_download):
        self.total_failed += len(failed_urls)
        self.total_downloaded += len(succeeded_urls)
        self._file_index = batch_download.file_index
        self._category_counts = batch_download.category_counts

        self._last_result = Result(
            failed_urls=failed_urls,
            succeeded_urls=succeeded_urls
        )

        self.save()

    def save(self):
        failed_urls = self.last_result.failed_urls
        succeeded_urls = self.last_result.succeeded_urls

        d = {
            'destination': self.destination,
            'number_of_images': self.number_of_images,
            'images_per_category': self.images_per_category,
            'batch_size': self.batch_size,
            'total_downloaded': self.total_downloaded,
            'total_failed': self.total_failed,
            'configured': self._configured,
            'finished': self.finished,
            'failed_urls': failed_urls,
            'succeeded_urls': succeeded_urls,
            'position': self._last_position.to_json(),
            'category_counts': self._category_counts,
            'file_index': self._file_index
        }

        path = config.download_state_path
        with open(path, 'w') as f:
            f.write(json.dumps(d))

    def configure(self, conf):
        self._set_defaults()

        self.destination = conf.download_destination
        self.number_of_images = conf.number_of_images
        self.images_per_category = conf.images_per_category
        self.batch_size = conf.batch_size
        self._configured = True

    @property
    def configuration(self):
        return DownloadConfiguration(
            number_of_images=self.number_of_images,
            images_per_category=self.images_per_category,
            download_destination=self.destination,
            batch_size=self.batch_size
        )

    @property
    def last_result(self):
        return self._last_result


class Result:
    def __init__(self, failed_urls, succeeded_urls):
        self.failed_urls = failed_urls
        self.succeeded_urls = succeeded_urls

    @property
    def failures_count(self):
        return len(self.failed_urls)

    @property
    def successes_count(self):
        return len(self.succeeded_urls)


class DownloadConfiguration:
    def __init__(self, number_of_images,
                 images_per_category,
                 download_destination,
                 batch_size=100):
        self.number_of_images = number_of_images
        self.images_per_category = images_per_category
        self.download_destination = download_destination
        self.batch_size = batch_size


class NotConfiguredError(Exception):
    pass
