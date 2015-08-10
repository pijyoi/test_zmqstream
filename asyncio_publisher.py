import struct
import random
import asyncio

clients = {}

@asyncio.coroutine
def publish_stuff():
    yield from asyncio.start_server(client_connected, '127.0.0.1', 10000)

    idx = 0
    while True:
        payload_size = random.randint(4, 10000)
        fullmsg = bytearray(4 + payload_size)
        struct.pack_into('>I', fullmsg, 0, payload_size)    # 4-byte header
        struct.pack_into('I', fullmsg, 4, idx)

        remove_list = []

        for connid in clients.keys():
            reader, writer = clients[connid]

            do_close = False
            hiccup = random.randint(1, 20)==1       # 1 in 20 chance

            msg = memoryview(fullmsg)
            if hiccup:
                # simulate send of partial message before disconnection
                partial_size = random.randint(1, len(msg))
                msg = msg[:partial_size]
                do_close = True

            writer.write(msg)

            if do_close:
                writer.close()
                remove_list.append(connid)

        for connid in remove_list:
            del clients[connid]

        idx += 1
        yield from asyncio.sleep(0.2) 

@asyncio.coroutine
def client_connected(reader, writer):
    sock = writer.get_extra_info('socket')
    connid = sock.fileno()
    clients[connid] = (reader, writer)
    while True:
        data = yield from reader.read(1)
        if not data:
            break
    clients.pop(connid, None)
    writer.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(publish_stuff())
loop.run_forever()

