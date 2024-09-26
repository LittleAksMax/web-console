from threading import Lock


class ThreadSafeEmittingStream:
    def __init__(self, buffer: bytearray, buffer_lock: Lock):
        self.buf = buffer
        self.buf_lock = buffer_lock

    def write(self, data: str):
        with self.buf_lock:
            self.buf.extend(data.encode('utf-8'))

    def flush(self):
        with self.buf_lock:
            data = bytes(self.buf)
            self.buf.clear()
        return data
