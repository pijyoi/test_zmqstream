from __future__ import print_function

import struct

import zmq
from zmq.eventloop import ioloop

class TcpSubscriber:
    hdrfmt = struct.Struct('>I')

    def __init__(self, endpoint):
        self.reset()
        self.connected = False
        self.connect(endpoint)

    def connect(self, endpoint):
        zctx = zmq.Context.instance()
        zsock = zctx.socket(zmq.STREAM)
        zsock.connect(endpoint)
        peerid = zsock.getsockopt(zmq.IDENTITY)
        self.zsock = zsock

        io_loop = ioloop.IOLoop.instance()
        io_loop.add_handler(zsock, self.handle_read, io_loop.READ)

    def reset(self):
        self.wait_hdr = True
        self.packet_size = self.hdrfmt.size
        self.accum_buffer = bytearray()

    def handle_read(self, zsock, events):
        peerid, payload = zsock.recv_multipart()

        if not payload:
            if not self.connected:
                self.handle_connect(peerid)
                self.connected = True
            else:
                self.handle_disconnect(peerid)
                self.connected = False
            return

        self.accum_buffer.extend(payload)

        while len(self.accum_buffer) >= self.packet_size:
            pkt = memoryview(self.accum_buffer)[:self.packet_size]
            self.accum_buffer = self.accum_buffer[self.packet_size:]
            if self.wait_hdr:
                self.wait_hdr = False
                self.packet_size = self.hdrfmt.unpack(pkt)[0]
            else:
                self.wait_hdr = True
                self.packet_size = self.hdrfmt.size
                self.handle_msg(pkt)

    def handle_connect(self, peerid):
        print('connected to {0!r}'.format(peerid))

    def handle_disconnect(self, peerid):
        print('disconnected from {0!r}'.format(peerid))
        self.reset()

    def handle_msg(self, msg):
        print('msgsize: {0}'.format(len(msg)))

class MySubscriber(TcpSubscriber):
    def handle_msg(self, msg):
        idx = struct.unpack('I', msg[:4])[0]
        print('{0}: {1}'.format(idx, len(msg)))

MySubscriber("tcp://127.0.0.1:10000")
io_loop = ioloop.IOLoop.instance()
io_loop.start()

