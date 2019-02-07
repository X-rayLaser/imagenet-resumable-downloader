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
from util.app_state import DownloadConfiguration, Result, ProgressInfo, InternalState, AppState


class StatefulDownloader:
    def __init__(self, app_state):
        self._app_state = app_state

    def __iter__(self):
        if not self._app_state.configured:
            raise NotConfiguredError()

        conf = self._app_state.download_configuration
        progress_info = self._app_state.progress_info
        internal = self._app_state.internal_state

        images_left = conf.number_of_images - progress_info.total_downloaded

        conf = DownloadConfiguration(download_destination=conf.download_destination,
                                     number_of_images=images_left,
                                     images_per_category=conf.images_per_category,
                                     batch_size=conf.batch_size)
        batch_download = BatchDownload(
            conf, starting_index=internal.file_index
        )

        batch_download.set_counts(internal.category_counts)

        image_net_urls = iterators.create_image_net_urls(
            start_after_position=internal.iterator_position
        )

        for wn_id, url, position in image_net_urls:
            batch_download.add(wn_id, url)

            if batch_download.batch_ready:
                failed_urls, succeeded_urls = batch_download.flush()
                self._update_and_save_progress(failed_urls, succeeded_urls,
                                               batch_download)

                if batch_download.complete:
                    progress_info.finished = True
                yield self._last_result
                if batch_download.complete:
                    progress_info.finished = True
                    break

            internal.iterator_position = position
            internal.category_counts = batch_download.category_counts

        progress_info.finished = True
        if not batch_download.is_empty:
            self._finish_download(batch_download)
            yield self._last_result

    def _finish_download(self, batch_download):
        failed_urls, succeeded_urls = batch_download.flush()
        self._update_and_save_progress(failed_urls, succeeded_urls,
                                       batch_download)

    def _update_and_save_progress(self, failed_urls, succeeded_urls,
                                  batch_download):
        self._app_state.progress_info.total_failed += len(failed_urls)
        self._app_state.progress_info.total_downloaded += len(succeeded_urls)
        self._app_state.progress_info.last_result = Result(
            failed_urls=failed_urls,
            succeeded_urls=succeeded_urls
        )

        self._app_state.internal_state.file_index = batch_download.file_index
        self._app_state.internal_state.category_counts = batch_download.category_counts

        self._last_result = self._app_state.progress_info.last_result
        self.save()

    def save(self):
        self._app_state.save()

    def configure(self, conf):
        self._app_state.reset()
        self._conf = conf
        self._app_state.set_configuration(conf)
        self._configured = True
        self._app_state.configured = True
        self.save()

    @property
    def configuration(self):
        return self._conf

    @property
    def progress_info(self):
        return self._app_state.progress_info

    @property
    def last_result(self):
        return self._last_result


class NotConfiguredError(Exception):
    pass
