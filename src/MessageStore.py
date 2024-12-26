# coding=utf-8 

from conf.config import allConf
from MessageStoreFactory import MessageStoreFactory

@MessageStoreFactory()
class MessageStore(object):
	BUFF_SIZE=int(allConf.messageStore.storeBuffSize)

	def __init__(self, publisherId):
		self.publisherId = publisherId

	def NewPublisher(self):
		self.publisherId += 1

	def AppendMsg(self, msg):
		raise NotImplementedError

	def GetMsg(self, publisherId, msgIdx):
		raise NotImplementedError

# 这里说一下,因为python中没有像C++ STL那种的容器,直接用单个str对象做接收缓冲区的时候又比较尴尬.
# 最开始想的处理方式是每一个publisher对应一个str对象,来消息了直接拼接到后面.
# 但是`currentPublishMsg`对象越长,后面每次拼接耗时也越久.况且也没办法预知要接收多少东西.
# 另一种方法是不做拼接,直接将每次从socket中读取到的数据按序存到一个list里面,
# 但是这种方法,会导致后面转发逻辑复杂,而且转发的时候也要重新拼接小对象,也不太合适.
# 所以取了一个折中方式,按照定长空间存储接收到的消息,一个publisher对应一个list,
# 每个list的elem是一个长度固定的str(可配置),收到消息的时候依次填充就好了.
@MessageStoreFactory()
class MemoryMessageStore(MessageStore):
	def __init__(self):
		super(MemoryMessageStore, self).__init__(-1)
		self.publisherMsgs = []
		self.currentPublisherMsg = ['']

	def NewPublisher(self):
		super(MemoryMessageStore, self).NewPublisher()
		self.currentPublisherMsg = ['']
		self.publisherMsgs.append(self.currentPublisherMsg)

	def _AppendMsgReal(self, msg):
		latestBufferSize=len(self.currentPublisherMsg[-1])
		if latestBufferSize + len(msg) <= self.BUFF_SIZE:
			self.currentPublisherMsg[-1] += msg
		else:
			bufferRemainLen=self.BUFF_SIZE-latestBufferSize
			self.currentPublisherMsg[-1] += msg[:bufferRemainLen]
			self.currentPublisherMsg.append('')
			self._AppendMsgReal(msg[bufferRemainLen:])

	def AppendMsg(self, msg):
		self._AppendMsgReal(msg)

	def GetMsg(self, publisherId, msgIdx):
		if 0 > publisherId or publisherId >= len(self.publisherMsgs):
			return None

		requirePublisherMsg = self.publisherMsgs[publisherId]
		bufferRowId, bufferOffset=int(msgIdx/self.BUFF_SIZE), msgIdx%self.BUFF_SIZE
		if bufferRowId >= len(requirePublisherMsg):
			return None
		elif bufferOffset >= len(requirePublisherMsg[bufferRowId]):
			return None
		else:
			return requirePublisherMsg[bufferRowId][bufferOffset:] if bufferOffset > 0 else requirePublisherMsg[bufferRowId]
