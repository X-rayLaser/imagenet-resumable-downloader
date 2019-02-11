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
from util.app_state import AppState


class DummyStrategy(QtCore.QObject):
    imagesLoaded = QtCore.pyqtSignal(list)
    downloadFailed = QtCore.pyqtSignal(list)

    allDownloaded = QtCore.pyqtSignal()

    downloadPaused = QtCore.pyqtSignal()

    downloadResumed = QtCore.pyqtSignal()

    def start(self):
        pass

    def pause_download(self):
        pass

    def resume_download(self):
        pass

    def configure(self, destination, number_of_examples,
                  images_per_category, batch_size=100):
        pass

    def quit(self):
        pass


class StateManager(QtCore.QObject):
    stateChanged = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._app_state = AppState()

        if self._app_state.progress_info.finished:
            self._state = 'finished'
        elif self._app_state.inprogress:
            self._state = 'paused'
        else:
            self._state = 'initial'

        self._strategy = self.get_strategy()
        self._connect_signals()

    def _connect_signals(self):
        def handle_loaded(urls):
            self.stateChanged.emit()

        def handle_failed(urls):
            self.stateChanged.emit()

        def handle_paused():
            self._state = 'paused'
            self.stateChanged.emit()

        def handle_allDownloaded():
            self._state = 'finished'
            self._app_state.mark_finished()
            self._app_state.save()
            self.stateChanged.emit()

        self._strategy.imagesLoaded.connect(handle_loaded)
        self._strategy.downloadFailed.connect(handle_failed)

        self._strategy.downloadPaused.connect(handle_paused)
        self._strategy.allDownloaded.connect(handle_allDownloaded)

    def get_strategy(self):
        return DummyStrategy()

    @QtCore.pyqtSlot()
    def start_download(self):
        if self._state == 'ready':
            self._state = 'running'
            self.stateChanged.emit()
            self._strategy.start()

    @QtCore.pyqtSlot(str, int, int)
    def configure(self, destination, number_of_images,
                  images_per_category):
        if self._state not in ['initial', 'ready']:
            return

        self._app_state.reset()
        if self._valid_config(destination, number_of_images,
                              images_per_category):
            self._state = 'ready'
            path = self._parse_url(destination)

            self._strategy.configure(destination=path,
                                     number_of_examples=number_of_images,
                                     images_per_category=images_per_category)
        else:
            self._state = 'initial'
            self._generate_error_messages(destination, number_of_images,
                                          images_per_category)

        self.stateChanged.emit()

    def _valid_config(self, destination, number_of_images,
                      images_per_category):
        if not destination.strip():
            return False

        path = self._parse_url(destination)
        return os.path.exists(path) and number_of_images > 0 \
                and images_per_category > 0

    def _generate_error_messages(self, destination, number_of_images,
                                 images_per_category):
        if not destination.strip():
            self._app_state.add_error(
                'Destination folder for ImageNet was not specified'
            )
        else:
            path = self._parse_url(destination)
            if not os.path.exists(path):
                self._app_state.add_error(
                    'Path "{}" does not exist'.format(path)
                )

        if number_of_images <= 0:
            self._app_state.add_error(
                'Number of images must be greater than 0'
            )

        if images_per_category <= 0:
            self._app_state.add_error(
                'Images per category must be greater than 0'
            )

    def _parse_url(self, file_uri):
        p = urlparse(file_uri)
        return os.path.abspath(os.path.join(p.netloc, p.path))

    @QtCore.pyqtSlot()
    def pause(self):
        if self._state == 'running':
            self._state = 'pausing'
            self.stateChanged.emit()
            self._strategy.pause_download()

    @QtCore.pyqtSlot()
    def resume(self):
        if self._state == 'paused':
            self._state = 'running'
            self._strategy.resume_download()
            self.stateChanged.emit()

    @QtCore.pyqtSlot()
    def reset(self):
        if self._state not in ['running', 'pausing']:
            self._state = 'initial'
            self._app_state.reset()
            self._strategy.quit()
            self._strategy = self.get_strategy()
            self._connect_signals()

            self._app_state.save()
            self.stateChanged.emit()

    @QtCore.pyqtProperty(str)
    def download_state(self):
        return self._state

    @QtCore.pyqtProperty(str)
    def state_data_json(self):
        return self._app_state.to_json()

    @QtCore.pyqtProperty(str)
    def time_remaining(self):
        return self._app_state.time_remaining


class Worker(StateManager):
    def get_strategy(self):
        return DownloadManager(self._app_state)


# todo: add validation of arguments to Configuration class

# todo: refactor backend once more

# todo: double check, update readme and upload
