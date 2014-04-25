import struct

import zmq
from zmq.eventloop import ioloop

class TcpSubscriber:
	hdrfmt = struct.Struct('>I')

	def __init__(self, endpoint):
		self.connect(endpoint)
		self.reset()

	def connect(self, endpoint):
		zctx = zmq.Context.instance()
		zsock = zctx.socket(zmq.STREAM)
		zsock.connect(endpoint)
		myid = zsock.getsockopt(zmq.IDENTITY)

		io_loop = ioloop.IOLoop.instance()
		io_loop.add_handler(zsock, self.handle_read, io_loop.READ)

	def reset(self):
		self.wait_hdr = True
		self.packet_size = self.hdrfmt.size
		self.accum_buffer = bytearray()

	def handle_read(self, zsock, events):
		msgid = zsock.recv()
		payload = zsock.recv()
		if payload:
			self.accum_buffer.extend(payload)			
		else:		
			print "empty message!"
			self.reset()

		while len(self.accum_buffer) >= self.packet_size:
			pkt = buffer(self.accum_buffer, 0, self.packet_size)
			self.accum_buffer = bytearray(self.accum_buffer[self.packet_size:])
			if self.wait_hdr:
				self.wait_hdr = False
				self.packet_size = self.hdrfmt.unpack(pkt)[0]
			else:
				self.wait_hdr = True
				self.packet_size = self.hdrfmt.size
				self.handle_msg(pkt)

	def handle_msg(self, msg):
		print 'msgsize: {0}'.format(len(msg))

class MySubscriber(TcpSubscriber):
	def handle_msg(self, msg):
		idx = struct.unpack('I', msg[:4])[0]
		print '{0}: {1}'.format(idx, len(msg))

MySubscriber("tcp://127.0.0.1:10000")
io_loop = ioloop.IOLoop.instance()
io_loop.start()

