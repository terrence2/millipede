class Connection:
	def __init__(self, *args, **kwargs):
		self.closed = None
		self.readable = None
		self.writable = None
	def close(self, *args, **kwargs): pass
	def fileno(self, *args, **kwargs): pass
	def poll(self, *args, **kwargs): pass
	def recv(self, *args, **kwargs): pass
	def recv_bytes(self, *args, **kwargs): pass
	def recv_bytes_into(self, *args, **kwargs): pass
	def send(self, *args, **kwargs): pass
	def send_bytes(self, *args, **kwargs): pass

PipeConnection = Connection
win32 = None

class SemLock:
	SEM_VALUE_MAX = 2147483647
	def __init__(self, *args, **kwargs):
		self.handle = None
		self.kind = None
		self.maxvalue = None
	def __enter__(self, *args, **kwargs): pass
	def __exit__(self, *args, **kwargs): pass
	def acquire(self, *args, **kwargs): pass
	def release(self, *args, **kwargs): pass

def address_of_buffer(*args, **kwargs): pass
def recvfd(*args, **kwargs): pass
def sendfd(*args, **kwargs): pass

flags = {}
