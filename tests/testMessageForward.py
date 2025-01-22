import unittest
import Worker
import logging

from src import MessageForward, MessageStoreFactory, ReceiverManager, BroadcastService
from conf.config import allConf

class TestMessageForward(unittest.TestCase):
	def setUp(self):
		# self.fileStorePath = None
		BroadcastService.BroadcastService.VERIFY_TIME = 2
		logging.disable(logging.ERROR)

		self.service = MessageForward.MessageForward()
		self.service.publishService.Start()
		self.service.broadcastService.Start()

		# reset message store.
		MessageStoreFactory.MessageStoreFactory.MessageStoreInstance().__init__()

		# worker thread.
		self.worker = Worker.Worker()
		self.worker.start()

	def tearDown(self):
		self.worker.AppendTask(Worker.StopWorkerTask(self.worker))
		self.worker.join()
		self.service.publishService.Close()
		self.service.broadcastService.Close()

	def waitUntil(self, condition):
		loopTime = 10
		while loopTime > 0:
			loopTime -= 1
			self.service.loop(1)
			ReceiverManager.AllReceivers.Instance().BroadcastMsg()
			self.service.broadcastService.CloseTimeoutConnections()
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
			return publisher and publisher.receiveMsgLen == len(msg) and senderTask3.Done()
		self.waitUntil(receiveCondition)

		publisherConnect = self.service.publishService.CurrentPublisher()
		self.assertEqual(publisherConnect.publisherId, 2)
		self.assertEqual(messageStore.GetMsg(0, 0), msg)
		self.assertIsNone(messageStore.GetMsg(1, 0))
		self.assertEqual(messageStore.GetMsg(2, 0), msg)

	# check broadcast service state.
	def test_BroadbastServiceState(self):
		receivers = ReceiverManager.AllReceivers.Instance()
		self.assertEqual(len(receivers), 0)
		BCS = self.service.broadcastService
		self.assertEqual(len(BCS.allConnection), 0)

		# connect to broadcast service.
		recieverId = 'client50001\0suffix'
		address = (allConf.api.broadcastHost, int(allConf.api.broadcastPort))
		receiverTask = Worker.BroadcastMsgReceiverTask(address, recieverId)

		connectionNum = 1
		def broadConnectCondition():
			return BCS.ReceiverNum() == connectionNum
		self.waitUntil(broadConnectCondition)

		# check broadcastConnection State.
		self.assertEqual(BCS.ReceiverNum(), 1)
		broadcastConnection = BCS.allConnection.values()[0]
		self.assertEqual(broadcastConnection.state, BroadcastService.BroadcastConnect.NONE_STATE)
		self.assertIsNone(broadcastConnection.receiverId)
		self.assertEqual(len(receivers), 0)

		# verify connection.
		receiverTask.verify()
		receiverNum = 1
		def receiverCondition():
			return len(receivers) == receiverNum
		self.waitUntil(receiverCondition)

		# check broadcastConnection after verified.
		recieverId='client50001'
		self.assertEqual(broadcastConnection.state, BroadcastService.BroadcastConnect.VERIFIED_STATE)
		self.assertEqual(broadcastConnection.receiverId, recieverId)
		
		self.assertIn(recieverId, receivers)
		receiver = receivers[recieverId]
		self.assertEqual(receiver.publisherId, 0)
		self.assertEqual(receiver.msgIdx, 0)

		## test verify timeout.
		recieverId = 'client50002\0'
		address = (allConf.api.broadcastHost, int(allConf.api.broadcastPort))
		receiverTask2 = Worker.BroadcastMsgReceiverTask(address, recieverId)

		connectionNum = 2
		self.waitUntil(broadConnectCondition)

		# wait until receiverTask socket was closed by server.
		connectionNum = 1
		self.waitUntil(broadConnectCondition)

		# check receiver sock was closed.
		receiverTask2.sock.setblocking(True)
		recvMsg = receiverTask2.sock.recv(1024)
		self.assertEqual(recvMsg, '')

	# check msg receive.
	def test_MsgReceive(self):
		receivers = ReceiverManager.AllReceivers.Instance()

		paddress = (allConf.api.publishHost, int(allConf.api.publishPort))
		senderTask1 = Worker.PublisherMsgSenderTask(paddress)

		receiverId = 'client50001\0'
		baddress = (allConf.api.broadcastHost, int(allConf.api.broadcastPort))
		receiverTask1 = Worker.BroadcastMsgReceiverTask(baddress, receiverId)
		receiverTask1.verify()

		publisherId = 0
		receiverNum = 1
		def PRcondition():
			publisher = self.service.publishService.CurrentPublisher()
			return publisher and publisher.publisherId == publisherId and \
				len(receivers) == receiverNum

		self.waitUntil(PRcondition)

		## check send and recv.
		msg = ','.join([str(num) for num in range(10)])
		senderTask1.sendMsg(msg)
		receiverTask1.setReadLen(len(msg))

		self.worker.AppendTask(senderTask1)
		self.worker.AppendTask(receiverTask1)

		def readConfition():
			return senderTask1.Done() and receiverTask1.Done()
		self.waitUntil(readConfition)

		self.assertEqual(msg, receiverTask1.receiverBuffer)
		receiverId = 'client50001'
		self.assertIn(receiverId, receivers)
		receiver = receivers[receiverId]
		self.assertEqual(receiver.publisherId, 0)
		self.assertEqual(receiver.msgIdx, len(msg))

		## receiver connects later than sender.
		receiverId2 = 'client50002\0'
		receiverTask2 = Worker.BroadcastMsgReceiverTask(baddress, receiverId2)
		receiverTask2.verify()
		receiverTask2.setReadLen(len(msg))

		self.worker.AppendTask(receiverTask2)
		self.waitUntil(receiverTask2.Done)
		
		self.assertEqual(msg, receiverTask2.receiverBuffer)
		receiverId2 = 'client50002'
		self.assertIn(receiverId2, receivers)
		receiver2 = receivers[receiverId2]
		self.assertEqual(receiver2.publisherId, 0)
		self.assertEqual(receiver2.msgIdx, len(msg))

		## broadCast to multi receiver.
		senderTask1.sendMsg(msg)
		receiverTask1.setReadLen(len(msg))
		receiverTask2.setReadLen(len(msg))

		self.worker.AppendTask(senderTask1)
		self.worker.AppendTask(receiverTask1)
		self.worker.AppendTask(receiverTask2)

		def readCondition2():
			return senderTask1.Done() and receiverTask1.Done() and receiverTask2.Done()
		self.waitUntil(readCondition2)

		self.assertEqual(msg, receiverTask1.receiverBuffer)
		self.assertEqual(msg, receiverTask2.receiverBuffer)

		## publisher reconnect.
		senderTask2 = Worker.PublisherMsgSenderTask(paddress)
		publisherId = 1
		def newPublisherCondition():
			publisher = self.service.publishService.CurrentPublisher()
			return publisher and publisher.publisherId == publisherId
		self.waitUntil(newPublisherCondition)

		senderTask3 = Worker.PublisherMsgSenderTask(paddress)
		senderTask3.sendMsg(msg)

		self.worker.AppendTask(senderTask3)
		def receiverCondition():
			publisher = self.service.publishService.CurrentPublisher()
			return publisher and publisher.receiveMsgLen == len(msg) and senderTask3.Done()
		self.waitUntil(receiverCondition)

		# receiverTask1 & receiverTask2 will be closed by server.
		receiverTask1.sock.setblocking(True)
		recvMsg = receiverTask1.sock.recv(1024)
		self.assertEqual(recvMsg, '')
		self.assertIsNone(receivers[receiverId].connection)
		self.assertEqual(receivers[receiverId].publisherId, 1)

		receiverTask2.sock.setblocking(True)
		recvMsg = receiverTask2.sock.recv(1024)
		self.assertEqual(recvMsg, '')
		self.assertIsNone(receivers[receiverId2].connection)
		self.assertEqual(receivers[receiverId2].publisherId, 1)

		## reconnect as 50001.
		receiverId = 'client50001\0'
		receiverTask3 = Worker.BroadcastMsgReceiverTask(baddress, receiverId)
		receiverTask3.verify()
		receiverTask3.setReadLen(100)

		self.worker.AppendTask(receiverTask3)
		def receiverCondition():
			receiver = receivers['client50001']
			return receiver and receiver.publisherId == 2 and receiverTask3.Done()
		self.waitUntil(receiverCondition)

		# recv nothing.
		self.assertEqual(receiverTask3.receiverBuffer, '')

		## reconnect as 50001 again.
		receiverTask4 = Worker.BroadcastMsgReceiverTask(baddress, receiverId)
		receiverTask4.verify()
		receiverTask4.setReadLen(len(msg))

		self.worker.AppendTask(receiverTask4)
		self.waitUntil(receiverTask4.Done)
		self.assertEqual(receiverTask4.receiverBuffer, msg)
