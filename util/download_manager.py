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
from PyQt5.QtCore import QThread, QMutex, QWaitCondition

from image_net.stateful_downloader import StatefulDownloader


class DownloadManager(QThread):
    imagesLoaded = QtCore.pyqtSignal(list)
    downloadFailed = QtCore.pyqtSignal(list)

    allDownloaded = QtCore.pyqtSignal()

    downloadPaused = QtCore.pyqtSignal()

    downloadResumed = QtCore.pyqtSignal()

    def __init__(self, app_state):
        super().__init__()
        self.mutex = QMutex()
        self.download_paused = False
        self.wait_condition = QWaitCondition()

        self.stateful_downloader = StatefulDownloader(app_state)

        self._has_started = False

    def run(self):
        self._has_started = True

        stateful_downloader = self.stateful_downloader

        for result in stateful_downloader:
            self.imagesLoaded.emit(result.succeeded_urls)
            self.downloadFailed.emit(result.failed_urls)

            if self.download_paused:
                self.downloadPaused.emit()
                self.mutex.lock()
                self.wait_condition.wait(self.mutex)
                self.mutex.unlock()

        self.allDownloaded.emit()

    def pause_download(self):
        self.mutex.lock()
        self.download_paused = True
        self.mutex.unlock()

    def resume_download(self):
        if not self._has_started:
            self.start()
            return

        self.mutex.lock()
        self.download_paused = False
        self.mutex.unlock()
        self.wait_condition.wakeAll()
        self.downloadResumed.emit()
