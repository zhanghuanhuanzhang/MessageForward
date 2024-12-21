import socket
import asyncore
import logging

from Log import Logger
from TcpConnect import TcpConnect
from conf.config import allConf

class TcpServer(Logger, asyncore.dispatcher):

	def __init__(self, host, port):
		asyncore.dispatcher.__init__(self)
		self.host = host
		self.port = port
		self.name = self.__class__.__name__
		self.allConnection = {}

	def Start(self):
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind((self.host, self.port))
		self.listen(int(allConf.common.backlog))
		logging.info('start service {0} on [{1}:{2}]'.format(self.name, self.host, self.port))

	def Close(self):
		self.CloseAllConnections()
		self.close()
		logging.info('clost service {0}'.format(self.name))

	def handle_accept(self):
		newSock = self.accept()
		if newSock:
			sock, addr = newSock
			tcpConn = self.onNewConnection(sock, addr)
			self.allConnection[addr] = tcpConn

	def handle_close(self):
		self.Close()

	def onNewConnection(self, sock, addr):
		# return TcpConnect(self, sock, addr)
		raise Exception("{0} does not implement 'onNewConnection' interface".format(self.name))

	def CloseConnection(self, addr):
		if addr in self.allConnection:
			tcpConn = self.allConnection.pop(addr)
			tcpConn.onClose()
			logging.info('{0} disconnects to the {1}'.format(tcpConn, self.name))

	def CloseAllConnections(self):
		for tcpConn in self.allConnection.itervalues():
			tcpConn.onClose()
			logging.info('{0} disconnects to the {1}'.format(tcpConn, self.name))
		
		self.allConnection.clear()
