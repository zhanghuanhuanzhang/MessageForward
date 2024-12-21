import logging

from TcpServer import TcpServer
from TcpConnect import TcpConnect
from conf.config import allConf

class PublishService(TcpServer):
	def __init__(self, msgForward, messageStore):
		apiConf = allConf.api
		super(PublishService, self).__init__(apiConf.publishHost, int(apiConf.publishPort))
		self.messageStore = messageStore
		self.msgForward = msgForward

	def onNewConnection(self, sock, addr):
		logging.info('PublishService accept new connection on [{0}], current connection num: {1}'
			   .format(str(addr), len(self.allConnection)))
		if len(self.allConnection) > 0:
			# close all publish connection.
			self.CloseAllConnections()

		return PublishConnect(self, sock, addr)

class PublishConnect(TcpConnect):
	
	def onRead(self, msg):
		self.server.msgForward.broadcastService.BroadCastMsg(msg)
