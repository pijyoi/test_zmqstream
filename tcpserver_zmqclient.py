from __future__ import print_function

import socket
import struct

import zmq

port = 12345

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('127.0.0.1', port))
server.listen(1)

zctx = zmq.Context.instance()
zsock = zctx.socket(zmq.STREAM)
zsock.connect('tcp://127.0.0.1:{}'.format(port))

sock, addr = server.accept()
server.close()

accum_buffer = bytearray()

for msgsize in [8000, 8192, 8193, 8194, 9000]:
    msg = bytearray(msgsize)
    struct.pack_into('>I', msg, 0, 0xdeadbeef)
    sock.sendall(msg)

    while len(accum_buffer) < msgsize:
        peerid, payload = zsock.recv_multipart()
        print('got payload size {}'.format(len(payload)))
        accum_buffer.extend(payload)
        
    tag = bytes(accum_buffer[0:4])
    print('size: {}, tag: {}'.format(msgsize, tag))

    accum_buffer = accum_buffer[msgsize:]

sock.close()

