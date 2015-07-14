from __future__ import print_function

import struct
import random

import zmq
from zmq.eventloop import ioloop

zctx = zmq.Context.instance()
zsock = zctx.socket(zmq.STREAM)
zsock.bind('tcp://127.0.0.1:10000')

idx = 0
clients = []

def msg_handler(zsock, events):
    msg = zsock.recv_multipart()
    clientid, payload = msg

    if not payload:
        if clientid not in clients:
            print('connection from', repr(clientid))
            clients.append(clientid)
        else:
            print('disconnection from', repr(clientid))
            clients.remove(clientid)

def timer_data():
    global idx

    payload_size = random.randint(4, 10000)
    msg = bytearray(4 + payload_size)
    struct.pack_into('>I', msg, 0, payload_size)    # 4-byte header
    struct.pack_into('I', msg, 4, idx)

    idx += 1

    for clientid in clients:
        do_close = False
        hiccup = random.randint(1, 20)==1   # 1 in 20 chance

        if hiccup:
            # simulate send of partial message before disconnection
            partial_size = random.randint(1, len(msg))
            msg = buffer(msg, 0, partial_size)
            do_close = True

        zsock.send(clientid, zmq.SNDMORE)
        zsock.send(msg, zmq.SNDMORE)

        if do_close:
            zsock.send(clientid, zmq.SNDMORE)
            zsock.send('', zmq.SNDMORE)
            clients.remove(clientid)


io_loop = ioloop.IOLoop.instance()
io_loop.add_handler(zsock, msg_handler, io_loop.READ)
ioloop.PeriodicCallback(timer_data, 200, io_loop).start()
io_loop.start()

