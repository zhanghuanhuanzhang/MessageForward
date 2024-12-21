import asyncore
import logging

from PublishService import PublishService
from BroadcastService import BroadcastService
from conf.config import allConf

class MessageForward(object):
	def __init__(self):
		self.publishService = PublishService(self, None)
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

# service = MessageForward()
