from PyQt5 import QtCore
from downloader import ImageNet
import os
from urllib.parse import urlparse


class Worker(QtCore.QObject):
    #imageLoaded = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @QtCore.pyqtSlot(str)
    def start_download(self, destination):
        path = self._parse_url(destination)
        path = '/home/eugene/mytemp/imagenet'
        imagenet = ImageNet(number_of_examples=10, destination=path)
        imagenet.download()

    def _parse_url(self, file_url):
        p = urlparse(file_url)
        return os.path.abspath(os.path.join(p.netloc, p.path))
