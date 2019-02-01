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