# coding=utf-8 

import time
import struct
import logging

from TcpServer import TcpServer
from TcpConnect import TcpConnect
from conf.config import allConf
from ReceiverManager import AllReceivers

class BroadcastService(TcpServer):
	VERIFY_TIME = int(allConf.common.verifyTime)
	def __init__(self):
		apiConf = allConf.api
		super(BroadcastService, self).__init__(apiConf.broadcastHost, int(apiConf.broadcastPort))
	
	def onNewConnection(self, sock, addr):
		logging.info('BroadcastService accept new connection on [{0}]'.format(addr))
		return BroadcastConnect(self, sock, addr)

	# def BroadCastMsg(self, msg):
	# 	for conn in self.allConnection.itervalues():
	# 		conn.Send(msg)

	def ReceiverNum(self):
		return len(self.allConnection)

	def CloseTimeoutConnections(self):
		now = time.time()
		closeAddrs = [c.addr for c in self.allConnection.values() if c.VerifyTimeout(now)]
		for addr in closeAddrs:
			logging.warning('connection {0} verify timeout, close it!'.format(addr))
			self.CloseConnection(addr)

class BroadcastConnect(TcpConnect):
	NONE_STATE = 0
	VERIFIED_STATE = 1
	CLOSED_STATE = 2

	def __init__(self, broadcastService, sock, addr):
		super(BroadcastConnect, self).__init__(broadcastService, sock, addr)
		self.state = self.NONE_STATE
		self.receiverId = None
		self.readBuffer = ''
		self.createTimestamp = time.time()

	def VerifyTimeout(self, now):
		return self.state == self.NONE_STATE and now - self.createTimestamp > self.server.VERIFY_TIME

	def onRead(self, msg):
		if self.state != self.NONE_STATE:
			return

		self.readBuffer += msg
		endIdx = self.readBuffer.find('\0')
		if endIdx > 0:
			self.receiverId = self.readBuffer[:endIdx]
			AllReceivers.Instance().AppendReceiver(self.receiverId, self)
			self.state = self.VERIFIED_STATE

	def onClose(self):
		super(BroadcastConnect, self).onClose()
		if self.state == self.VERIFIED_STATE:
			receivers = AllReceivers.Instance()
			if self.receiverId not in receivers:
				logging.warning('not find receivers {0}'.format(self.receiverId))
			else:
				receivers[self.receiverId].SetConnection(None)

		self.state = self.CLOSED_STATE
