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
import time


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