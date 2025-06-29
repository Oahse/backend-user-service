import time
import threading

class SnowflakeGenerator:
    def __init__(self, datacenter_id=0, worker_id=0):
        # Define bit lengths for each part
        self.datacenter_id_bits = 5
        self.worker_id_bits = 5
        self.sequence_bits = 12

        # Max values
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)  # 31
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)          # 31
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)            # 4095

        # Shift bits
        self.worker_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_shift = self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits

        # Custom epoch (e.g., Jan 1, 2020)
        self.epoch = 1577836800000

        # Instance IDs
        if datacenter_id > self.max_datacenter_id or datacenter_id < 0:
            raise ValueError("datacenter_id out of bounds")
        if worker_id > self.max_worker_id or worker_id < 0:
            raise ValueError("worker_id out of bounds")
        self.datacenter_id = datacenter_id
        self.worker_id = worker_id

        self.sequence = 0
        self.last_timestamp = -1

        self.lock = threading.Lock()

    def _time_gen(self):
        return int(time.time() * 1000)  # current time in milliseconds

    def _wait_next_millis(self, last_timestamp):
        timestamp = self._time_gen()
        while timestamp <= last_timestamp:
            timestamp = self._time_gen()
        return timestamp

    def get_id(self):
        with self.lock:
            timestamp = self._time_gen()

            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Refusing to generate id")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    # Sequence overflow, wait for next millisecond
                    timestamp = self._wait_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            id = ((timestamp - self.epoch) << self.timestamp_shift) | \
                 (self.datacenter_id << self.datacenter_id_shift) | \
                 (self.worker_id << self.worker_id_shift) | \
                 self.sequence

            return id

generator = SnowflakeGenerator(datacenter_id=1, worker_id=2)

