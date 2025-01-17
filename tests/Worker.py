import Queue
import logging
import threading
import socket
import time

class Worker(threading.Thread):
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.queue = Queue.Queue()
		self.exitLoop = False

	def AppendTask(self, task):
		self.queue.put(task)

	def run(self):
		while not self.exitLoop:
			task = self.queue.get()
			try:
				task()
			except Exception as e:
				logging.error('{0} run error {1}'.format(task, e))

# tasks
class Task(object):
	def __init__(self):
		self.lock = threading.Lock()
		self.state = 0

	def Done(self):
		state = 0
		self.lock.acquire()
		state = self.state
		self.lock.release()
		return state != 0

	def SetState(self, state):
		self.lock.acquire()
		self.state = state
		self.lock.release()

	def WaitUntilDone(self):
		loopTime = 10
		while loopTime>0:
			self.lock.acquire()
			if self.state != 0:
				break
			self.lock.release()
			time.sleep(1)
		else:
			raise Exception("task run timeout")

class StopWorkerTask(Task):

	def __init__(self, worker):
		super(StopWorkerTask, self).__init__()
		self.worker = worker

	def __call__(self):
		self.worker.exitLoop = True
		self.SetState(1)

class PublisherMsgSenderTask(Task):
	# block tcp client.
	def __init__(self, address):
		super(PublisherMsgSenderTask, self).__init__()
		self.address = address
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect(address)
		self.msg = None
		pass

	def sendMsg(self, msg):
		self.msg = msg
		self.SetState(0)

	def __call__(self):
		self.sock.send(self.msg)
		self.msg = None
		self.SetState(1)
