from PyQt5 import QtCore
from PyQt5.QtCore import QThread
from downloader import ImageNet
import os
from urllib.parse import urlparse


class DownloaderThread(QThread):
    imageLoaded = QtCore.pyqtSignal()

    def __init__(self, destination, number_of_examples):
        super().__init__()
        self.destination = destination
        self.number_of_examples = number_of_examples

    def run(self):
        def on_image_downloaded():
            self.imageLoaded.emit()

        imagenet = ImageNet(number_of_examples=self.number_of_examples,
                            destination=self.destination,
                            on_loaded=on_image_downloaded)
        imagenet.download()


class Worker(QtCore.QObject):
    imageLoaded = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._complete = True
        self._images = 0

    @QtCore.pyqtSlot(str)
    def start_download(self, destination):
        self._complete = False
        self._images = 0

        path = self._parse_url(destination)
        path = '/home/eugene/mytemp/imagenet'

        self.thread = DownloaderThread(destination=path, number_of_examples=10)

        def handle_loaded():
            self._images += 1

            if self._images >= 10:
                self._complete = True

            self.imageLoaded.emit()

        self.thread.imageLoaded.connect(handle_loaded)
        self.thread.start()

    @QtCore.pyqtProperty(int)
    def images_downloaded(self):
        return self._images

    @QtCore.pyqtProperty(bool)
    def complete(self):
        return self._complete

    def _parse_url(self, file_url):
        p = urlparse(file_url)
        return os.path.abspath(os.path.join(p.netloc, p.path))
