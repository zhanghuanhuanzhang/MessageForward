import unittest
import Worker
import logging

from src import MessageForward, MessageStoreFactory
from conf.config import allConf

class TestMessageForward(unittest.TestCase):
	def setUp(self):
		# self.fileStorePath = None
		logging.disable(logging.ERROR)

		self.service = MessageForward.MessageForward()
		self.service.publishService.Start()
		self.service.broadcastService.Start()

		# worker thread.
		self.worker = Worker.Worker()
		self.worker.start()

	def tearDown(self):
		self.worker.AppendTask(Worker.StopWorkerTask(self.worker))
		self.worker.join()

	def waitUntil(self, condition):
		loopTime = 10
		while loopTime > 0:
			loopTime -= 1
			self.service.loop(1)
			if condition():
				break
		else:
			self.assertTrue(False, "wait time out")

	# block client
	def test_PublishService(self):
		publisherConnect = self.service.publishService.CurrentPublisher()
		self.assertIsNone(publisherConnect)
		messageStore = MessageStoreFactory.MessageStoreFactory.MessageStoreInstance()
		self.assertIsNone(messageStore.GetMsg(0, 0))
		self.assertIsNone(messageStore.GetMsg(1, 0))

		## connect to publisher.
		address = (allConf.api.publishHost, int(allConf.api.publishPort))
		senderTask = Worker.PublisherMsgSenderTask(address)
		expectPublisherId = 0
		def publisherCondition():
			publisher = self.service.publishService.CurrentPublisher()
			return publisher != None and publisher.publisherId == expectPublisherId
		self.waitUntil(publisherCondition)

		## check publisher connect state
		publisherConnect = self.service.publishService.CurrentPublisher()
		self.assertEqual(publisherConnect.publisherId, 0)
		self.assertEqual(publisherConnect.receiveMsgLen, 0)
		self.assertIsNone(messageStore.GetMsg(0, 0))

		## sendMsg and wait receive all msg.
		msg = ','.join([str(num) for num in xrange(10)])
		senderTask.sendMsg(msg)
		self.worker.AppendTask(senderTask)

		def receiveCondition():
			publisher = self.service.publishService.CurrentPublisher()
			return publisher.receiveMsgLen == len(msg) and senderTask.Done()
		self.waitUntil(receiveCondition)

		self.assertEqual(messageStore.GetMsg(0, 0), msg)
		self.assertIsNone(messageStore.GetMsg(1, 0))

		## create new publisher.
		senderTask2 = Worker.PublisherMsgSenderTask(address)
		expectPublisherId = 1
		self.waitUntil(publisherCondition)

		# check senderTask was closed (server close)
		senderTask.sock.setblocking(True)
		recvMsg = senderTask.sock.recv(1024)
		self.assertEqual(recvMsg, '')

		# client close
		senderTask2.sock.close()
		def noPublisherCondition():
			return self.service.publishService.CurrentPublisher() == None
		self.waitUntil(noPublisherCondition)

		## close publisher and create another publisher
		senderTask3 = Worker.PublisherMsgSenderTask(address)
		expectPublisherId = 2
		self.waitUntil(publisherCondition)

		senderTask3.sendMsg(msg)
		self.worker.AppendTask(senderTask3)
		def receiveCondition():
			publisher = self.service.publishService.CurrentPublisher()
			return publisher.receiveMsgLen == len(msg) and senderTask3.Done()
		self.waitUntil(receiveCondition)

		publisherConnect = self.service.publishService.CurrentPublisher()
		self.assertEqual(publisherConnect.publisherId, 2)
		self.assertEqual(messageStore.GetMsg(0, 0), msg)
		self.assertIsNone(messageStore.GetMsg(1, 0))
		self.assertEqual(messageStore.GetMsg(2, 0), msg)
