
class error(EnvironmentException):
	pass

class mmap:
	def __init__(self, fileno, length, *args, **kwargs): pass
	def close(self, *args, **kwargs): pass
	def find(self, *args, **kwargs): pass
	def flush(self, *args, **kwargs): pass
	def move(self, *args, **kwargs): pass
	def read(self, *args, **kwargs): pass
	def read_byte(self, *args, **kwargs): pass
	def readline(self, *args, **kwargs): pass
	def resize(self, *args, **kwargs): pass
	def rfind(self, *args, **kwargs): pass
	def seek(self, *args, **kwargs): pass
	def size(self, *args, **kwargs): pass
	def tell(self, *args, **kwargs): pass
	def write(self, *args, **kwargs): pass
	def write_byte(self, *args, **kwargs): pass

ACCESS_COPY = 3
ACCESS_READ = 1
ACCESS_WRITE = 2
ALLOCATIONGRANULARITY = 4096
MAP_ANON = 32
MAP_ANONYMOUS = 32
MAP_DENYWRITE = 2048
MAP_EXECUTABLE = 4096
MAP_PRIVATE = 2
MAP_SHARED = 1
PAGESIZE = 4096
PROT_EXEC = 4
PROT_READ = 1
PROT_WRITE = 2
