# coding=utf-8 

import asyncore
import logging

from PublishService import PublishService
from BroadcastService import BroadcastService
from ReceiverManager import AllReceivers
from conf.config import allConf

class MessageForward(object):
	def __init__(self):
		self.publishService = PublishService(self)
		self.broadcastService = BroadcastService()

		commonConf = allConf.common
		self.loop = asyncore.poll2 if int(commonConf.usePoll) else asyncore.poll
		self.loopTime = float(commonConf.loopTime)

	def Run(self):
		self.publishService.Start()
		self.broadcastService.Start()

		logging.info('Run MessageForward.')
		while True:
			self.loop(self.loopTime)
			AllReceivers.Instance().BroadcastMsg()

			# 没有做timer,放到每次循环中检测超时未验证的连接.
			self.broadcastService.CloseTimeoutConnections()

# service = MessageForward()
