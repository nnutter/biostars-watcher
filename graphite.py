import time
import socket
import pickle
import struct


class Graphite:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))
        self.queue = []

    def __del__(self):
        self.close()

    def now(self):
        return int(time.time())

    def enqueue(self, name, value, timestamp=None):
        if timestamp == None:
            timestamp = self.now()
        self.queue.append((name, (timestamp, value)))

    def send(self, name, value, timestamp=None):
        self.enqueue(name, value, timestamp)
        self.pop_send()

    def pack(self, items):
        data = pickle.dumps(items)
        header = struct.pack("!L", len(data))
        return header + data

    def send_queue(self):
        # Maybe this doesn't work because our carbon is old.
        # But the code looks the same and looks like this
        # should work but it doesn't.
        raise Exception("I haven't got this working yet.")
        self.socket.send(self.pack(self.queue))
        self.queue = []

    def pop_send(self):
        self.socket.send(self.pack([self.queue.pop()]))

    def close(self):
        if len(self.queue):
            self.send_queue()
        if self.socket:
            self.socket.close()
            self.socket = None
