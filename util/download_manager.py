from PyQt5 import QtCore
from PyQt5.QtCore import QThread, QMutex, QWaitCondition

from image_net.stateful_downloader import StatefulDownloader, DownloadConfiguration


class DownloadManager(QThread):
    imagesLoaded = QtCore.pyqtSignal(list)
    downloadFailed = QtCore.pyqtSignal(list)

    allDownloaded = QtCore.pyqtSignal()

    downloadPaused = QtCore.pyqtSignal()

    downloadResumed = QtCore.pyqtSignal()

    def __init__(self, destination, number_of_examples, images_per_category,
                 batch_size=100):
        super().__init__()
        self.destination = destination
        self.number_of_examples = number_of_examples
        self.images_per_category = images_per_category
        self.batch_size = batch_size
        self.mutex = QMutex()
        self.download_paused = False
        self.wait_condition = QWaitCondition()

        self.downloaded = 0

    def run(self):
        self.downloaded = 0

        stateful_downloader = StatefulDownloader()

        conf = DownloadConfiguration(
            number_of_images=self.number_of_examples,
            images_per_category=self.images_per_category,
            download_destination=self.destination,
            batch_size=self.batch_size
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
