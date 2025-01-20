from conf.config import allConf

class MessageStoreFactory(object):
	instance=None
	allMessageStore={}
	messageStoreName = allConf.messageStore.storeName

	@classmethod
	def MessageStoreInstance(cls):
		import FileStore, MessageStore
		if cls.messageStoreName not in cls.allMessageStore:
			raise Exception('not find {0} message store'.format(cls.messageStoreName))

		cls.instance = cls.instance if cls.instance else cls.allMessageStore[cls.messageStoreName]()
		return cls.instance

	def __call__(self, messageStoreCls):
		MessageStoreFactory.allMessageStore[messageStoreCls.__name__] = messageStoreCls
		return messageStoreCls
