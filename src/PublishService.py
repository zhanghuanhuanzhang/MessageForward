import logging

from TcpServer import TcpServer
from TcpConnect import TcpConnect
from conf.config import allConf
from MessageStoreFactory import MessageStoreFactory

class PublishService(TcpServer):
	def __init__(self, msgForward):
		apiConf = allConf.api
		super(PublishService, self).__init__(apiConf.publishHost, int(apiConf.publishPort))
		self.messageStore = MessageStoreFactory.MessageStoreInstance()
		self.msgForward = msgForward
		self.publisher = None
		# self.publisherId = 1

	def onNewConnection(self, sock, addr):
		logging.info('PublishService accept new connection on [{0}], current connection num: {1}'
			   .format(str(addr), len(self.allConnection)))
		if len(self.allConnection) > 0:
			# close all publish connection.
			self.CloseAllConnections()

		self.publisher = PublishConnect(self, sock, addr)
		return self.publisher

	def CurrentPublisher(self):
		return self.publisher

	def ResetPublisher(self):
		self.publisher = None

class PublishConnect(TcpConnect):

	def __init__(self, publishService, sock, addr):
		super(PublishConnect, self).__init__(publishService, sock, addr)
		self.messageStore = MessageStoreFactory.MessageStoreInstance()
		self.messageStore.NewPublisher()
		self.publisherId = self.messageStore.PublisherId()
		self.receiveMsgLen = 0

	def onRead(self, msg):
		# self.server.msgForward.broadcastService.BroadCastMsg(msg)
		if not self.connected:
			logging.warning('receive publish message from disconnected connection: {1}'.format(self))
			return

		self.server.messageStore.AppendMsg(msg)
		self.receiveMsgLen += len(msg)

		## todo. notify all broadcast service.

	def onClose(self):
		super(PublishConnect, self).onClose()
		if self.server.CurrentPublisher() != self:
			logging.warning('{0} was closed, but is not current publisher!!'.format(self.publisherId))
		else:
			self.server.ResetPublisher()
