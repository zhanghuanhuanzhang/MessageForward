# import configparser
import ConfigParser
from UserDict import UserDict

# conf = configparser.ConfigParser()
# conf.read('config.ini')

class Conf(object):
	def __init__(self, sectionName, sectionInfoList):
		self.__dict__['sectionName'] = sectionName
		# self.__dict__['confSection'] = confSection
		for confName, confVal in sectionInfoList:
			self.__dict__[confName] = confVal

	def __getattr__(self, name):
		name = name.lower()
		if name not in self.__dict__:
			raise Exception("not find conf '{0}.{1}' in config.ini".format(self.sectionName, name))

		return self.__dict__[name]

	def __setattr__(self, name, value):
		raise Exception("Disable configuration changes")

class AllConf(UserDict):
	def __init__(self, confPath):
		# super(AllConf, self).__init__()
		UserDict.__init__(self)
		self.conf = ConfigParser.ConfigParser()
		self.conf.read(confPath)

		# for confName, confVal in self.conf.iteritems():
		# 	self[confName] = Conf(confName, confVal)
		for sectionName in self.conf.sections():
			self[sectionName] = Conf(sectionName, self.conf.items(sectionName))

	def __getattr__(self, name):
		if name not in self:
			raise Exception("not find conf section '{0}' in config.ini".format(name))

		return self[name]


allConf = AllConf('conf/config.ini')
