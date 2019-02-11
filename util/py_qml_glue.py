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
from util.app_state import AppState, DownloadConfiguration
from config import config


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
        self._log_path = config.log_path

        if self._app_state.progress_info.finished:
            self._state = 'finished'
        elif self._app_state.inprogress:
            self._state = 'paused'
        else:
            self._state = 'initial'
            self._reset_log()

        self._strategy = self.get_strategy()
        self._connect_signals()

    def _connect_signals(self):
        def handle_loaded(urls):
            self.stateChanged.emit()

        def handle_failed(urls):
            self._log_failures(self._log_path, urls)
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

    def _reset_log(self):
        if not os.path.exists(config.app_data_folder):
            os.mkdir(config.app_data_folder)

        if os.path.isfile(self._log_path):
            os.remove(self._log_path)

        with open(self._log_path, 'w') as f:
            f.write('')

    def _log_failures(self, log_path, urls):
        with open(log_path, 'a') as f:
            lines = '\n'.join(urls)
            f.write(lines)

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

        conf = DownloadConfiguration(number_of_images=number_of_images,
                                     images_per_category=images_per_category,
                                     download_destination=destination,
                                     batch_size=config.default_batch_size)
        if conf.is_valid:
            self._state = 'ready'
            path = self._parse_url(destination)
            conf.download_destination = path
            self._app_state.set_configuration(conf)
        else:
            self._state = 'initial'
            self._generate_error_messages(conf)

        self.stateChanged.emit()

    def _generate_error_messages(self, download_conf):
        for e in download_conf.errors:
            self._app_state.add_error(e)

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
            self._reset_log()
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


# todo: refactor backend once more

# todo: double check, update readme and upload
