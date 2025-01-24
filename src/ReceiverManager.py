import time
import logging

from UserDict import UserDict
from MessageStoreFactory import MessageStoreFactory
from conf.config import allConf

class AllReceivers(UserDict):
	instance=None
	def __init__(self):
		UserDict.__init__(self)

	@classmethod
	def Instance(cls):
		cls.instance = cls.instance if cls.instance is not None else cls()
		return cls.instance

	def AppendReceiver(self, receiverId, connection):
		if receiverId not in self:
			self[receiverId] = Receiver(receiverId)
		
		self[receiverId].SetConnection(connection)

	def BroadcastMsg(self):
		for receiver in self.itervalues():
			receiver.SendMsg()

class Receiver(object):
	SEND_INTERVAL=float(allConf.common.sendInterval)
	TRAFFIC_LIMIT=int(allConf.common.trafficLimit)

	def __init__(self, receiverId):
		self.receiverId = receiverId
		self.connection = None
		self.messageStore = MessageStoreFactory.MessageStoreInstance()
		self.lastSendTs = time.time()
		self.trafficRestrict = False
		
		# msgIdx
		self.publisherId = 0
		self.msgIdx = 0

	def SetConnection(self, connection):
		if self.connection and connection:
			logging.warning("The old client hasn't disconnected yet! receiverId: {0}".format(self.receiverId))
			self.connection.server.CloseConnection(self.connection.addr)

		self.connection = connection

	def SendMsg(self):
		# todo flow control && write buffer check.
		currentPublisherId = self.messageStore.PublisherId()
		if not self.connection or currentPublisherId < 0:
			return

		now = time.time()
		if self.trafficRestrict and now - self.lastSendTs < self.SEND_INTERVAL:
			return
		self.lastSendTs = now

		if currentPublisherId == self.publisherId:
			self.SendCurrentPublisherMsg()
		elif currentPublisherId > self.publisherId:
			self.SendCurrentPublisherMsg()
			# check write buffer and close connection.
			if not self.connection.out_buffer:
				self.connection.server.CloseConnection(self.connection.addr)
				# modify next publisher info.
				self.publisherId += 1
				self.msgIdx = 0
				# self.connection = None
		else:
			logging.warning("ReceiverId: {0} greater than publisherId: {1}".format(self.publisherId, currentPublisherId))

	def SendCurrentPublisherMsg(self):
		remainLen = self.TRAFFIC_LIMIT - len(self.connection.out_buffer)
		while remainLen > 0:
			msg = self.messageStore.GetMsg(self.publisherId, self.msgIdx)
			if not msg:
				self.trafficRestrict = False
				break

			msg = msg[:remainLen]
			self.connection.Send(msg)
			msgLen = len(msg)
			self.msgIdx += msgLen
			remainLen -= msgLen
		else:
			self.trafficRestrict = True
