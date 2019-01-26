from PyQt5 import QtCore
from PyQt5.QtCore import QThread, QMutex, QWaitCondition
import os
import time
from urllib.parse import urlparse
import downloader


class DownloadManager(QThread):
    imagesLoaded = QtCore.pyqtSignal(list)
    downloadFailed = QtCore.pyqtSignal(list)

    allDownloaded = QtCore.pyqtSignal()

    downloadPaused = QtCore.pyqtSignal()

    downloadResumed = QtCore.pyqtSignal()

    def __init__(self, destination, number_of_examples, images_per_category):
        super().__init__()
        self.destination = destination
        self.number_of_examples = number_of_examples
        self.images_per_category = images_per_category
        self.mutex = QMutex()
        self.download_paused = False
        self.wait_condition = QWaitCondition()

        self.downloaded = 0

    def run(self):
        self.downloaded = 0

        stateful_downloader = downloader.StatefulDownloader()

        conf = downloader.DownloadConfiguration(
            number_of_images=self.number_of_examples,
            images_per_category=self.images_per_category,
            download_destination=self.destination,
            batch_size=100
        )
        stateful_downloader.configure(conf)

        for result in stateful_downloader:
            self.imagesLoaded.emit(result.succeeded_urls)
            self.downloadFailed.emit(result.failed_urls)
            self.downloaded += len(result.succeeded_urls)

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
        self.mutex.lock()
        self.download_paused = False
        self.mutex.unlock()
        self.wait_condition.wakeAll()
        self.downloadResumed.emit()

    def _log_failures(self, log_path, urls):
        with open(log_path, 'a') as f:
            lines = '\n'.join(urls)
            f.write(lines)


class RunningAverage:
    def __init__(self, points=5):
        self._points = points
        self._update_times = []
        self._update_units = []
        self._initial_time = time.time()

    def reset(self):
        self._update_times = []
        self._update_units = []
        self._initial_time = time.time()

    def update(self, units=1):
        t = time.time()

        if len(self._update_times) >= self._points:
            self._initial_time = self._update_times[-1]
            self._update_times[:] = []
            self._update_units[:] = []

        self._update_times.append(t)
        self._update_units.append(units)

    @property
    def units_per_second(self):
        if not self._update_times:
            return 0

        seconds = self._update_times[-1] - self._initial_time
        units = sum(self._update_units)

        return float(units) / seconds


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

        self.thread = DownloadManager(destination=path,
                                      number_of_examples=nimages,
                                      images_per_category=per_category)

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
