import socket
import select
import struct
import time
import random

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('127.0.0.1', 10000))
server.listen(1)
clients = []

idx = 0
while 1:
    r, w, e = select.select([server], [], [], 0.2)
    if r:
        sock, addr = server.accept()
        clients.append(sock)

    payload_size = random.randint(4, 10000)
    fullmsg = bytearray(4 + payload_size)
    struct.pack_into('>I', fullmsg, 0, payload_size)    # 4-byte header
    struct.pack_into('I', fullmsg, 4, idx)

    idx += 1

    remove_list = []
    for sock in clients:
        do_close = False
        hiccup = random.randint(1, 20)==1       # 1 in 20 chance

        msg = memoryview(fullmsg)
        if hiccup:
            # simulate send of partial message before disconnection
            partial_size = random.randint(1, len(msg))
            msg = msg[:partial_size]
            do_close = True

        try:
            sock.sendall(msg)
        except socket.error:
            do_close = True

        if do_close:
            sock.close()
            remove_list.append(sock)

    for sock in remove_list:
        clients.remove(sock)


