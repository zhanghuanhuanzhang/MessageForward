import socket
import asyncore
import logging

from Log import Logger
from conf.config import allConf
from errno import EWOULDBLOCK, EAGAIN

class TcpConnect(Logger, asyncore.dispatcher_with_send):
	READ_BUFFER_SIZE = int(allConf.common.readBufferSize)

	def __init__(self, server, sock, addr):
		asyncore.dispatcher_with_send.__init__(self, sock)
		self.server = server
		self.addr = addr

	# def initiate_send(self):
	# 	pass

	# def send(self, data)
	Send=asyncore.dispatcher_with_send.send
	
	def onRead(self, msg):
		pass

	def onClose(self):
		self.close()

	def handle_read(self):
		while True:
			try:
				data = self.recv(self.READ_BUFFER_SIZE)
				if not data:
					break
				self.onRead(data)
			except socket.error as why:
				if why.args[0] in (EWOULDBLOCK, EAGAIN):
					break
				else:
					raise

	def handle_close(self):
		self.server.CloseConnection(self.addr)

	def __repr__(self):
		return '[{0}->{1}]'.format(str(self.addr), self.server.name)

	__str__ = __repr__
