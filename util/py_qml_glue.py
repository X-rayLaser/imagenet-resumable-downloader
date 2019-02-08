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
from PyQt5 import QtCore
import os
import json
from urllib.parse import urlparse

from util.download_manager import DownloadManager
from util.average import RunningAverage
from config import config


class StateManager(QtCore.QObject):
    stateChanged = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._state = 'initial'
        self._errors = []
        #self._download_strategy = download_strategy

    @QtCore.pyqtSlot()
    def start_download(self):
        if self._state == 'ready':
            self._state = 'running'
            self.stateChanged.emit()

    @QtCore.pyqtSlot(str, int, int)
    def configure(self, destination, number_of_images,
                  images_per_category):
        if self._state not in ['initial', 'ready']:
            return

        self._errors[:] = []
        self._state = 'ready'

        if not destination.strip():
            self._state = 'initial'
            self._errors.append('Destination folder for ImageNet was not specified')
        else:
            path = self._parse_url(destination)
            if not os.path.exists(path):
                self._state = 'initial'
                self._errors.append('Path "{}" does not exist'.format(path))

        if number_of_images <= 0:
            self._state = 'initial'
            self._errors.append('Number of images must be greater than 0')

        if images_per_category <= 0:
            self._state = 'initial'
            self._errors.append('Images per category must be greater than 0')

        self.stateChanged.emit()

    def _parse_url(self, file_uri):
        p = urlparse(file_uri)
        return os.path.abspath(os.path.join(p.netloc, p.path))

    @QtCore.pyqtSlot()
    def pause(self):
        if self._state == 'running':
            self._state = 'pausing'
            self.stateChanged.emit()

    @QtCore.pyqtSlot()
    def resume(self):
        if self._state == 'paused':
            self._state = 'running'
            self.stateChanged.emit()

    @QtCore.pyqtSlot()
    def reset(self):
        if self._state not in ['running', 'pausing']:
            self._state = 'initial'
            self.stateChanged.emit()

    @QtCore.pyqtProperty(str)
    def download_state(self):
        return self._state

    @QtCore.pyqtProperty(str)
    def state_data_json(self):
        d = {
            'errors': self._errors
        }
        return json.dumps(d)

        d = {
            'downloadPath': self._download_path,
            'numberOfImages': self._number_of_images,
            'imagesPerCategory': self._images_per_category,

            'timeLeft': self.time_remaining,
            'imagesLoaded': self._images,
            'failures': self._failures,
            'failedUrls': self._failed_urls,
            'progress': self._calculate_progress()
        }

        return json.dumps(d)


class Worker(QtCore.QObject):

    stateChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._download_path = ''
        self._number_of_images = 100
        self._images_per_category = 90
        self._failures = 0
        self._failed_urls = []
        self._images = 0

        self.thread = DownloadManager()
        self._running_avg = RunningAverage()

        self._connect_signals()

        self._started = False
        self._complete = self.thread.stateful_downloader.finished
        if self._complete:
            self._state = 'finished'
        else:
            self._state = 'initial'

    def _connect_signals(self):
        def handle_loaded(urls):
            amount = len(urls)
            self._images += amount

            if self._images >= self._number_of_images or self.thread.stateful_downloader.finished:
                self._complete = True
                self._state = 'finished'

            self._running_avg.update(amount)
            self.stateChanged.emit()

        def handle_failed(urls):
            amount = len(urls)
            self.stateChanged.emit()

        self.thread.imagesLoaded.connect(handle_loaded)
        self.thread.downloadFailed.connect(handle_failed)

        self.thread.downloadPaused.connect(lambda: self.downloadPaused.emit())
        self.thread.downloadResumed.connect(lambda: self.downloadResumed.emit())

    @QtCore.pyqtSlot()
    def start_download(self):
        self._complete = False
        self._images = 0

        self._running_avg.reset()
        self.thread.start()
        self._started = True

    @QtCore.pyqtSlot(str, int, int)
    def configure(self, destination, number_of_images,
                       images_per_category):
        try:
            self._validate_input(destination, number_of_images,
                                 images_per_category)
        except Exception:
            pass
        else:
            self._number_of_images = number_of_images
            self._images_per_category = images_per_category

            self._complete = False
            self._images = 0

            self._download_path = self._parse_url(destination)

            self.thread.configure(destination=self._download_path,
                                  number_of_examples=number_of_images,
                                  images_per_category=images_per_category,
                                  batch_size=config.default_batch_size)
            self._state = 'ready'

    def _validate_input(self, destination, number_of_images,
                        images_per_category):
        if number_of_images <= 0 or images_per_category <= 0:
            raise Exception()

        path = self._parse_url(destination)
        if not os.path.exists(path):
            raise Exception()

    @QtCore.pyqtSlot()
    def pause(self):
        if self._started:
            self.thread.pause_download()
        else:
            raise Exception('Has not started yet!')

    @QtCore.pyqtSlot()
    def resume(self):
        if self._started:
            self.thread.resume_download()
        else:
            self.start_download()

    @QtCore.pyqtProperty(str)
    def download_state(self):
        return self._state

    @QtCore.pyqtProperty(str)
    def state_data_json(self):
        d = {
            'downloadPath': self._download_path,
            'numberOfImages': self._number_of_images,
            'imagesPerCategory': self._images_per_category,

            'timeLeft': self.time_remaining,
            'imagesLoaded': self._images,
            'failures': self._failures,
            'failedUrls': self._failed_urls,
            'progress': self._calculate_progress()
        }

        return json.dumps(d)

    @QtCore.pyqtProperty(int)
    def images_downloaded(self):
        return self._images

    @QtCore.pyqtProperty(bool)
    def complete(self):
        return self._complete

    @QtCore.pyqtProperty(str)
    def time_remaining(self):
        if self._running_avg.units_per_second == 0:
            return 'Eternity'

        images_left = self._number_of_images - self._images
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

    def _parse_url(self, file_url):
        p = urlparse(file_url)
        return os.path.abspath(os.path.join(p.netloc, p.path))

    def _calculate_progress(self):
        if self._number_of_images == 0:
            return 0
        return self._images / float(self._number_of_images)


# todo: create a class storing all the state of the app (configuration, internal state such as current interator position, etc.)

# todo: implement save and load methods on that class

# todo: add validation of arguments to Configuration class

# todo: implement a helper for creating default configuration

# todo: a method telling if state is default state (unchanged)

# todo: inject the state into StatefulDownloader

# todo: remove duplication related to state data management

# todo: move _calculate_progress method to the new class for app state

# todo: Extract a class from Worker responsible for all the pause, resume, etc logic

# todo: unit test Worker (transition through all states

# todo: add support for loading all images from ImageNet
