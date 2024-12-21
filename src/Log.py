import logging
from conf.config import allConf

class Logger(object):
	LOGGER_FORMAT = '%(pathname)s:%(lineno)d - %(message)s'

	@classmethod
	def InitLogFormat(cls):
		loggingConf = allConf.logging
		level=getattr(logging, loggingConf.level) or logging.DEBUG

		logging.basicConfig(level=level,
			filename=loggingConf.fileName,
			filemode=loggingConf.fileMode,
			format=cls.LOGGER_FORMAT)

	def log_info(self, message, type='info'):
		logFunc = getattr(logging, type)
		if logFunc:
			logFunc('%s: %s' % (type, message))
		else:
			logging.error("not find log type {0}".format(type))

Logger.InitLogFormat()
