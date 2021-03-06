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


import os
import json
from urllib.parse import urlparse

from image_net.iterators import Position
from config import config
from util.average import RunningAverage


class AppState:
    def __init__(self):
        self._running_avg = RunningAverage()

        self.reset()

        try:
            self.load()
        except:
            pass

    def reset(self):
        self._running_avg.reset()

        self.download_configuration = DownloadConfiguration(
            number_of_images=100,
            images_per_category=90,
            download_destination='',
            batch_size=100
        )

        last_result = Result(failed_urls=[], succeeded_urls=[])

        self.progress_info = ProgressInfo(
            total_downloaded=0,
            total_failed=0,
            finished=False,
            last_result=last_result
        )

        self.internal_state = InternalState(
            iterator_position=Position.null_position(),
            category_counts={},
            file_index=1
        )

        self.configured = False
        self._errors = []

    def add_error(self, message):
        self._errors.append(message)

    @property
    def errors(self):
        return list(self._errors)

    def update_progress(self, result):
        self.progress_info.total_failed += len(result.failed_urls)
        self.progress_info.total_downloaded += len(result.succeeded_urls)
        self.progress_info.last_result = result
        self._running_avg.update(len(result.succeeded_urls))

    def mark_finished(self):
        self.progress_info.finished = True

    def set_configuration(self, conf):
        self.reset()
        self.download_configuration = conf
        self.configured = True

    def set_progress_info(self, progress_info):
        self.progress_info = progress_info

    def set_internal_state(self, internal_state):
        self.internal_state = internal_state

    def save(self):
        if not os.path.exists(config.app_data_folder):
            os.mkdir(config.app_data_folder)

        conf_dict = self.download_configuration.as_dict()

        progress_info = self.progress_info.as_dict()

        internal_state = self.internal_state.as_dict()

        d = {
            'download_configuration': conf_dict,
            'progress_info': progress_info,
            'internal_state': internal_state,
            'configured': self.configured,
            'errors': self._errors
        }

        path = config.app_state_path
        with open(path, 'w') as f:
            f.write(json.dumps(d))

    def to_json(self):
        download_conf = self.download_configuration

        d = dict(downloadPath=download_conf.download_destination,
                 numberOfImages=download_conf.number_of_images,
                 imagesPerCategory=download_conf.images_per_category,
                 timeLeft=self.time_remaining,
                 imagesLoaded=self.progress_info.total_downloaded,
                 failures=self.progress_info.total_failed,
                 failedUrls=self.progress_info.last_result.failed_urls,
                 succeededUrls=self.progress_info.last_result.succeeded_urls,
                 errors=self._errors,
                 progress=self.calculate_progress())

        return json.dumps(d)

    def load(self):
        if not os.path.exists(config.app_data_folder):
            os.mkdir(config.app_data_folder)

        with open(config.app_state_path, 'r') as f:
            s = f.read()
            d = json.loads(s)
            conf_dict = d['download_configuration']

            self.download_configuration = DownloadConfiguration.from_dict(
                conf_dict
            )

            progress_info_dict = d['progress_info']

            self.progress_info = ProgressInfo.from_dict(progress_info_dict)

            internal_state = d['internal_state']
            self.internal_state = InternalState.from_dict(internal_state)

            self.configured = d['configured']
            self._errors = d['errors']

    @property
    def inprogress(self):
        return self.progress_info.total_failed > 0 or \
               self.progress_info.total_downloaded > 0

    def calculate_progress(self):
        images_total = self.download_configuration.number_of_images
        downloaded = self.progress_info.total_downloaded
        if images_total == 0:
            return 0
        return downloaded/ float(images_total)

    @property
    def time_remaining(self):
        if self._running_avg.units_per_second == 0:
            return 'Eternity'

        images_left = self.download_configuration.number_of_images - \
                      self.progress_info.total_downloaded

        if images_left <= 0:
            return self._format_time(0)

        time_left = round(
            images_left / float(self._running_avg.units_per_second)
        )
        return self._format_time(time_left)

    def _format_time(self, seconds):
        if seconds < 60:
            return '{} seconds'.format(seconds)
        elif seconds < 3600:
            return '{} minutes'.format(round(seconds / 60.0))
        elif seconds < 3600 * 24:
            return '{} hours'.format(round(seconds / 3600.0))
        else:
            days = float(seconds) / (3600 * 24)
            return '{} days'.format(round(days))

    def _calculate_progress(self):
        num_of_images = self.download_configuration.number_of_images
        if num_of_images == 0:
            return 0
        return self.progress_info.total_downloaded / float(num_of_images)


class DownloadConfiguration:
    def __init__(self, number_of_images,
                 images_per_category,
                 download_destination,
                 batch_size=100):
        self.number_of_images = number_of_images
        self.images_per_category = images_per_category
        self.download_destination = download_destination
        self.batch_size = batch_size

    def as_dict(self):
        return {
            'number_of_images': self.number_of_images,
            'images_per_category': self.images_per_category,
            'download_destination': self.download_destination,
            'batch_size': self.batch_size
        }

    @staticmethod
    def from_dict(conf_dict):
        return DownloadConfiguration(
            number_of_images=conf_dict['number_of_images'],
            images_per_category=conf_dict['images_per_category'],
            download_destination=conf_dict['download_destination'],
            batch_size=conf_dict['batch_size']
        )

    @property
    def is_valid(self):
        if not self.download_destination.strip():
            return False

        path = self._parse_url(self.download_destination)

        return os.path.exists(path) and self.number_of_images > 0 \
                and self.images_per_category > 0

    @property
    def errors(self):
        errors_list = []

        path = self.download_destination.strip()

        if not self.download_destination.strip():
            errors_list.append(
                'Destination folder for ImageNet was not specified'
            )
        else:
            path = self._parse_url(self.download_destination)
            if not os.path.exists(path):
                errors_list.append(
                    'Path "{}" does not exist'.format(path)
                )

        if self.number_of_images <= 0:
            errors_list.append(
                'Number of images must be greater than 0'
            )

        if self.images_per_category <= 0:
            errors_list.append(
                'Images per category must be greater than 0'
            )

        return errors_list

    def _parse_url(self, file_uri):
        p = urlparse(file_uri)
        return os.path.abspath(os.path.join(p.netloc, p.path))


class ProgressInfo:
    def __init__(self, total_downloaded, total_failed, finished,
                 last_result):
        self.total_downloaded = total_downloaded
        self.total_failed = total_failed
        self.finished = finished
        self.last_result = last_result

    def as_dict(self):
        return {
            'total_downloaded': self.total_downloaded,
            'total_failed': self.total_failed,
            'finished': self.finished,
            'failed_urls': self.last_result.failed_urls,
            'succeeded_urls': self.last_result.succeeded_urls
        }

    @staticmethod
    def from_dict(progress_dict):
        last_result = Result(failed_urls=progress_dict['failed_urls'],
                             succeeded_urls=progress_dict['succeeded_urls'])

        return ProgressInfo(
            total_downloaded=progress_dict['total_downloaded'],
            total_failed=progress_dict['total_failed'],
            finished=progress_dict['finished'],
            last_result=last_result
        )


class InternalState:
    def __init__(self, iterator_position, category_counts, file_index):
        self.iterator_position = iterator_position
        self.category_counts = category_counts
        self.file_index = file_index

    def as_dict(self):
        return {
            'iterator_position_json': self.iterator_position.to_json(),
            'category_counts': self.category_counts,
            'file_index': self.file_index
        }

    @staticmethod
    def from_dict(state_dict):

        position = Position.from_json(state_dict['iterator_position_json'])
        counts = state_dict['category_counts']
        file_index = state_dict['file_index']
        return InternalState(iterator_position=position,
                             category_counts=counts,
                             file_index=file_index)


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


class DirectoryNotFoundError(Exception): pass
