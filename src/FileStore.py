# coding=utf-8 

import os
import logging

from MessageStore import MemoryMessageStore
from MessageStoreFactory import MessageStoreFactory
from conf.config import allConf

class CtrlInfo(object):
	def __init__(self, msgBeg, msgLen, saveRowNum=0, begRowNum=0):
		self.msgBeg=msgBeg # body文件中起始位置
		self.msgLen=msgLen
		self.saveRowNum=saveRowNum
		self.begRowNum=begRowNum

	def __eq__(self, other):
		return self.msgBeg == other.msgBeg and\
			self.msgLen == other.msgLen and\
			self.saveRowNum == other.saveRowNum and\
			self.begRowNum == other.begRowNum

	def __repr__(self):
		return 'CtrlInfo:{msgBeg=%d, msgLen=%d, saveRowNum=%d, begRowNum=%d}'%\
				(self.msgBeg, self.msgLen, self.saveRowNum, self.begRowNum)

@MessageStoreFactory()
class FileMessageStore(MemoryMessageStore):
	BUFF_NUM = int(allConf.messageStore.fileStoreBuffNum)

	def __init__(self):
		super(FileMessageStore, self).__init__()
		
		self.fileStorePath = allConf.messageStore.fileStorePath
		if not self.fileStorePath:
			runPath = os.path.abspath(os.curdir)
			self.fileStorePath = os.path.join(runPath, 'MessageStore')
		
		self.bodyFile = None
		self.bodyFilePath = os.path.join(self.fileStorePath, 'body')
		self.ctrlFile = None
		self.ctrlFilePath = os.path.join(self.fileStorePath, 'ctrl')
		self.ctrlInfos = []
		self.currentPublisherMsgCtrl = CtrlInfo(0, 0)
		self.hasPublisher = False

		self.OpenStoreFile()
		self.LoadMessage()
		# self.currentPublisherMsg = ['']

	def __del__(self):
		if self.bodyFile and self.ctrlFile:
			self.FlushCurrentPublisherMsg()

		if self.bodyFile:
			# self.bodyFile.flush()
			self.bodyFile.close()
		if self.ctrlFile:
			# self.ctrlFile.flush()
			self.ctrlFile.close()

	def OpenStoreFile(self):
		try:
			if not os.path.exists(self.fileStorePath):
				os.makedirs(self.fileStorePath)
			self.bodyFile = open(self.bodyFilePath, 'ab+')
			self.ctrlFile = open(self.ctrlFilePath, 'a+')
			self.ctrlFile.seek(os.SEEK_SET, 0)
		except Exception as e:
			logging.error('Open store file failed: {0}'.format(e))
			raise e

	# ctrl file line format: publishId msgBeg msgLen
	def LoadMessage(self):
		try:
			for line in self.ctrlFile.readlines():
				_, msgBeg, msgLen = line.split()
				self.ctrlInfos.append(CtrlInfo(int(msgBeg), int(msgLen), int(msgLen)))
			if len(self.ctrlInfos) > 1:
				latestCtrlInfo = self.ctrlInfos[-1]
				self.currentPublisherMsgCtrl.msgBeg = latestCtrlInfo.msgBeg + latestCtrlInfo.msgLen
			self.publisherId = len(self.ctrlInfos) - 1
		except:
			logging.warning('Load message from file fail')
			self.ClearFile(self.bodyFile)
			self.ClearFile(self.ctrlFile)

	def ClearFile(self, file):
		file.seek(0)
		file.truncate()

	def FlushCurrentPublisherMsg(self):
		if self.currentPublisherMsg[-1]:
			self.bodyFile.write(self.currentPublisherMsg[-1])
		
		currentMsgBeg, currentMsgLen = self.currentPublisherMsgCtrl.msgBeg, self.currentPublisherMsgCtrl.msgLen
		self.ctrlFile.write('{0} {1} {2}\n'.format(len(self.ctrlInfos), currentMsgBeg, currentMsgLen))
		return currentMsgBeg + currentMsgLen

	# flush current publisher msg to file
	def NewPublisher(self):
		if self.hasPublisher:
			newMsgBeg = self.FlushCurrentPublisherMsg()
			self.ctrlInfos.append(self.currentPublisherMsgCtrl)		
			self.currentPublisherMsgCtrl = CtrlInfo(newMsgBeg, 0)

		self.hasPublisher = True

		super(FileMessageStore, self).NewPublisher()
		self.publisherMsgs = []

	def AppendMsg(self, msg):
		super(FileMessageStore, self).AppendMsg(msg)
		msgCtrl = self.currentPublisherMsgCtrl
		msgCtrl.msgLen += len(msg)
		totalRowNum = int(msgCtrl.msgLen/self.BUFF_SIZE)
		for buffRowIdx in xrange(msgCtrl.saveRowNum, totalRowNum):
			buffRowIdx -= msgCtrl.begRowNum
			self.bodyFile.write(self.currentPublisherMsg[buffRowIdx])

		self.bodyFile.flush()
		msgCtrl.saveRowNum = totalRowNum

		if self.BUFF_NUM > 0 and len(self.currentPublisherMsg) > self.BUFF_NUM:
			msgCtrl.begRowNum = len(self.currentPublisherMsg) - self.BUFF_NUM
			self.currentPublisherMsg = self.currentPublisherMsg[-self.BUFF_NUM:]

	def GetMsg(self, publisherId, msgIdx):
		targetCtrlInfo = None
		if publisherId < 0 or publisherId > len(self.ctrlInfos):
			return None
		elif publisherId == len(self.ctrlInfos):
			msgCtrl = self.currentPublisherMsgCtrl
			bufferRowId, bufferOffset = int(msgIdx/self.BUFF_SIZE), msgIdx%self.BUFF_SIZE
			bufferRowId -= msgCtrl.begRowNum
			if bufferRowId < 0:
				targetCtrlInfo = self.currentPublisherMsgCtrl
			elif bufferRowId >= len(self.currentPublisherMsg):
				return None
			elif bufferOffset >= len(self.currentPublisherMsg[bufferRowId]):
				return None
			else:
				return self.currentPublisherMsg[bufferRowId][bufferOffset:] if bufferOffset > 0 else self.currentPublisherMsg[bufferRowId]
		else:
			targetCtrlInfo = self.ctrlInfos[publisherId]

		if not targetCtrlInfo:
			raise Exception('not find ctrlInfo')

		logging.info('cache misss ({0}, {1})'.format(publisherId, msgIdx))
		readLen = (int(msgIdx/self.BUFF_SIZE)+1)*self.BUFF_SIZE - msgIdx
		return self.ReadFromBody(targetCtrlInfo, msgIdx, readLen)

	def ReadFromBody(self, ctrlInfo, msgIdx, readLen):
		readLen = min(readLen, ctrlInfo.msgLen - msgIdx)
		if readLen == 0 or ctrlInfo.msgLen < readLen:
			return None

		with open(self.bodyFilePath, 'r+') as ctrlFile:
			ctrlFile.seek(ctrlInfo.msgBeg + msgIdx)
			return ctrlFile.read(readLen)

		logging.warning('read msg from body file failed!')
		return None
