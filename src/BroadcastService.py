import logging

from TcpServer import TcpServer
from TcpConnect import TcpConnect
from conf.config import allConf

class BroadcastService(TcpServer):
	def __init__(self):
		apiConf = allConf.api
		super(BroadcastService, self).__init__(apiConf.broadcastHost, int(apiConf.broadcastPort))
	
	def onNewConnection(self, sock, addr):
		logging.info('BroadcastService accept new connection on [{0}]'.format(addr))
		return BroadcastConnect(self, sock, addr)

	def BroadCastMsg(self, msg):
		for conn in self.allConnection.itervalues():
			conn.Send(msg)

class BroadcastConnect(TcpConnect):
	pass

