import struct
import asyncio

def handle_msg(msg):
    idx = struct.unpack('I', msg[:4])[0]
    print('{0}: {1}'.format(idx, len(msg)))

@asyncio.coroutine
def subscribe_stuff():
    reader, writer = yield from asyncio.open_connection('127.0.0.1', 10000)

    hdrfmt = struct.Struct('>I')

    while True:
        try:
            hdr = yield from reader.readexactly(hdrfmt.size)
            packet_size = hdrfmt.unpack(hdr)[0]
            payload = yield from reader.readexactly(packet_size)
        except asyncio.IncompleteReadError as e:
            print('partial read {} / {}'.format(len(e.partial), e.expected))
            break

        handle_msg(payload)

loop = asyncio.get_event_loop()
loop.run_until_complete(subscribe_stuff())
#loop.run_forever()


