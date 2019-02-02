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
from urllib.parse import urlparse

from util.download_manager import DownloadManager
from util.average import RunningAverage
from config import config


class Worker(QtCore.QObject):
    imageLoaded = QtCore.pyqtSignal()

    downloadFailed = QtCore.pyqtSignal(
        int, list, arguments=['failures', 'failed_urls']
    )

    downloadPaused = QtCore.pyqtSignal()

    downloadResumed = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._complete = True
        self._images = 0

        self._running_avg = RunningAverage()
        self._number_of_images = 0

    @QtCore.pyqtSlot(str, int, int)
    def start_download(self, destination, number_of_images,
                       images_per_category):
        nimages = int(number_of_images)
        per_category = int(images_per_category)

        self._number_of_images = nimages

        self._complete = False
        self._images = 0

        path = self._parse_url(destination)

        default_batch_size = config.default_batch_size

        self.thread = DownloadManager(destination=path,
                                      number_of_examples=nimages,
                                      images_per_category=per_category,
                                      batch_size=default_batch_size)

        def handle_loaded(urls):
            amount = len(urls)
            self._images += amount

            if self._images >= nimages:
                self._complete = True

            self._running_avg.update(amount)
            for i in range(amount):
                self.imageLoaded.emit()

        def handle_failed(urls):
            amount = len(urls)

            self.downloadFailed.emit(amount, urls)

        self.thread.imagesLoaded.connect(handle_loaded)
        self.thread.downloadFailed.connect(handle_failed)

        self.thread.downloadPaused.connect(lambda: self.downloadPaused.emit())
        self.thread.downloadResumed.connect(lambda: self.downloadResumed.emit())

        self._running_avg.reset()
        self.thread.start()

    @QtCore.pyqtSlot()
    def pause(self):
        self.thread.pause_download()

    @QtCore.pyqtSlot()
    def resume(self):
        self.thread.resume_download()

    @QtCore.pyqtProperty(int)
    def images_downloaded(self):
        return self._images

    @QtCore.pyqtProperty(bool)
    def complete(self):
        return self._complete

    @QtCore.pyqtProperty(str)
    def time_remaining(self):
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
