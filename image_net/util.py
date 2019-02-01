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
from urllib.parse import urlparse


class Url2FileName:
    def __init__(self, starting_index=1):
        self._index = starting_index

    def convert(self, url):
        if url.rstrip() != url:
            raise MalformedUrlError('Trailing new line character')

        fname = self._url_to_file_name(url)
        base_name, extension = os.path.splitext(fname)

        converted_name = str(self._index) + extension

        self._index += 1
        return converted_name

    def _url_to_file_name(self, url):
        return os.path.basename(urlparse(url).path)

    @property
    def file_index(self):
        return self._index


class MalformedUrlError(Exception):
    pass
