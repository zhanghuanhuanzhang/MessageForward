import configparser
from UserDict import UserDict

# conf = configparser.ConfigParser()
# conf.read('config.ini')

class Conf(object):
	def __init__(self, confName, confSection):
		self.__dict__['confName'] = confName
		self.__dict__['confSection'] = confSection

	def __getattr__(self, name):
		if name not in self.confSection:
			raise Exception("not find conf '{0}.{1}' in config.ini".format(self.confName, name))

		return self.confSection[name]

	def __setattr__(self, name, value):
		raise Exception("Disable configuration changes")

class AllConf(UserDict):
	def __init__(self, confPath):
		# super(AllConf, self).__init__()
		UserDict.__init__(self)
		self.conf = configparser.ConfigParser()
		self.conf.read(confPath)

		for confName, confVal in self.conf.iteritems():
			self[confName] = Conf(confName, confVal)

	def __getattr__(self, name):
		if name not in self:
			raise Exception("not find conf section '{0}' in config.ini".format(name))

		return self[name]


allConf = AllConf('conf/config.ini')
