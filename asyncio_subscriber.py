import struct
import asyncio

def handle_msg(msg):
    idx = struct.unpack('I', msg[:4])[0]
    print('{0}: {1}'.format(idx, len(msg)))

@asyncio.coroutine
def subscribe_stuff():
    reader, writer = yield from asyncio.open_connection('127.0.0.1', 10000)

    hdrfmt = struct.Struct('>I')
    wait_hdr = True
    packet_size = hdrfmt.size
    accum_buffer = bytearray()

    while True:
        payload = yield from reader.read(8192)
        if not payload:
            break

        accum_buffer.extend(payload)

        while len(accum_buffer) >= packet_size:
            pkt = memoryview(accum_buffer)[:packet_size]
            accum_buffer = accum_buffer[packet_size:]
            if wait_hdr:
                wait_hdr = False
                packet_size = hdrfmt.unpack(pkt)[0]
            else:
                wait_hdr = True
                packet_size = hdrfmt.size
                handle_msg(pkt)

loop = asyncio.get_event_loop()
loop.run_until_complete(subscribe_stuff())
#loop.run_forever()


