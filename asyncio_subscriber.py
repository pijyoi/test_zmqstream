import struct
import asyncio

class SubscriberProtocol(asyncio.Protocol):
    hdrfmt = struct.Struct('>I')

    def __init__(self, loop):
        self.loop = loop

    def connection_made(self, transport):
        print('connection_made')
        self.transport = transport
        self.reset()

    def connection_lost(self, exc):
        print('connection_lost')
        self.loop.stop()

    def data_received(self, data):
        self.accum_buffer.extend(data)

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

    def reset(self):
        self.wait_hdr = True
        self.packet_size = self.hdrfmt.size
        self.accum_buffer = bytearray()

    def handle_msg(self, msg):
        idx = struct.unpack('I', msg[:4])[0]
        print('{0}: {1}'.format(idx, len(msg)))

@asyncio.coroutine
def reconnect(loop):
    coro = loop.create_connection(lambda: SubscriberProtocol(loop), '127.0.0.1', 10000)
    transport, protocol = yield from coro

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
#coro = loop.create_connection(lambda: SubscriberProtocol(loop), '127.0.0.1', 10000)
#transport, protocol = loop.run_until_complete(coro)
asyncio.async(reconnect(loop))
loop.run_forever()
loop.close()

#loop.run_until_complete(subscribe_stuff())

