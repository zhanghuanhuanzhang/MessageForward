import os
import shutil
import unittest

from src import FileStore, MessageStore, MessageStoreFactory

class TestMessageStore(unittest.TestCase):
	def setUp(self):
		# modify conf.
		MessageStore.MessageStore.BUFF_SIZE = 32
		FileStore.FileMessageStore.BUFF_NUM = 2

		self.fileStorePath = None
		# fileStore = FileStore.FileMessageStore()
		# os.removedirs(fileStore.fileStorePath)

	def tearDown(self):
		# del file store.
		if self.fileStorePath:
			shutil.rmtree(self.fileStorePath)

	def test_messageStoreFactory(self):
		allMessageStore = MessageStoreFactory.MessageStoreFactory.allMessageStore
		self.assertEqual(len(allMessageStore), 3)
		self.assertIs(allMessageStore['MessageStore'], MessageStore.MessageStore)
		self.assertIs(allMessageStore['MemoryMessageStore'], MessageStore.MemoryMessageStore)
		self.assertIs(allMessageStore['FileMessageStore'], FileStore.FileMessageStore)

		msgStoreInstange1 = MessageStoreFactory.MessageStoreFactory.MessageStoreInstance()
		msgStoreInstange2 = MessageStoreFactory.MessageStoreFactory.MessageStoreInstance()

		self.assertIs(msgStoreInstange1, msgStoreInstange2)
		self.assertIsInstance(msgStoreInstange1, MessageStore.MemoryMessageStore)

	def GetAndAppendTest(self, msgStore, checkPublisherLen=None):
		msgStore.AppendMsg('*'*5)
		self.assertEqual(msgStore.currentPublisherMsg, ['*'*5])
		self.assertIs(msgStore.GetMsg(msgStore.publisherId, 0), msgStore.currentPublisherMsg[0])
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 3), '*'*2)

		msgStore.AppendMsg('+'*(32*2))
		if checkPublisherLen:
			self.assertTrue(checkPublisherLen(msgStore))
		else:
			self.assertEqual(len(msgStore.currentPublisherMsg), 3)
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 0), '*'*5+'+'*27)
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 31), '+')
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 32), '+'*32)
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 32*2), '+'*5)

		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 32*2+4), '+')
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 32*2+5), None)
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 32*2+6), None)

	def test_memoryMessageStore(self):
		msgStore = MessageStore.MemoryMessageStore()

		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 0), None)

		msgStore.NewPublisher()
		self.assertEqual(msgStore.publisherId, 0)
		self.assertEqual(len(msgStore.publisherMsgs), 1)
		self.assertEqual(msgStore.currentPublisherMsg, [''])
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 0), None)

		self.GetAndAppendTest(msgStore)

		msgStore.NewPublisher()
		msgStore.NewPublisher()
		self.assertEqual(msgStore.publisherId, 2)
		self.assertEqual(len(msgStore.publisherMsgs), 3)
		self.assertEqual(msgStore.currentPublisherMsg, [''])
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 0), None)

		self.GetAndAppendTest(msgStore)

	def test_fileMessageStore(self):
		msgStore = FileStore.FileMessageStore()
		self.fileStorePath = msgStore.fileStorePath
		self.assertTrue(os.path.exists(msgStore.bodyFilePath))
		self.assertTrue(os.path.exists(msgStore.ctrlFilePath))

		expectCtrlInfo = FileStore.CtrlInfo(0, 0)

		msgStore.NewPublisher()
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 0), None)
		self.assertEqual(len(msgStore.ctrlInfos), 0)
		self.assertEqual(msgStore.currentPublisherMsg, [''])
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 0), None)
		self.assertEqual(msgStore.currentPublisherMsgCtrl, expectCtrlInfo)
		
		publisherLenChecker = lambda ms: len(ms.currentPublisherMsg) == msgStore.BUFF_NUM
		self.GetAndAppendTest(msgStore, publisherLenChecker)
		msgStore.NewPublisher()
		msgStore.NewPublisher()
		self.assertEqual(msgStore.publisherId, 2)
		# self.assertEqual(len(msgStore.ctrlInfos), 2)
		self.assertEqual(msgStore.currentPublisherMsg, [''])
		self.assertEqual(msgStore.GetMsg(msgStore.publisherId, 0), None)
		self.GetAndAppendTest(msgStore, publisherLenChecker)

		# test reload from file.
		# del msgStore
		msgStore = None
		msgStore = FileStore.FileMessageStore()
		self.assertEqual(msgStore.GetMsg(0, 32), '+'*32)
		self.assertEqual(msgStore.GetMsg(1, 0), None)
		self.assertEqual(msgStore.GetMsg(2, 64), '+'*5)
		self.assertEqual(msgStore.GetMsg(3, 0), None)

		msgStore.NewPublisher()
		self.GetAndAppendTest(msgStore, publisherLenChecker)
		msgStore.NewPublisher()
		self.GetAndAppendTest(msgStore, publisherLenChecker)

		# reload again
		# del msgStore
		msgStore = None
		msgStore = FileStore.FileMessageStore()
		self.assertEqual(len(msgStore.ctrlInfos), 5)
		self.assertEqual(msgStore.GetMsg(0, 32), '+'*32)
		self.assertEqual(msgStore.GetMsg(1, 0), None)
		self.assertEqual(msgStore.GetMsg(2, 64), '+'*5)
		self.assertEqual(msgStore.GetMsg(3, 0), '*'*5+'+'*27)
		self.assertEqual(msgStore.GetMsg(4, 60), '+'*4)
		self.assertEqual(msgStore.GetMsg(5, 0), None)

if __name__ == '__main__':
	unittest.main()
