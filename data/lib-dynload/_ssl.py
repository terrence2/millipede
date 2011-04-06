class SSLError(socket.error):
	def __init__(self, *args, **kwargs):
		self.errno = None
		self.filename = None
		self.strerror = None

class SSLContext:
	def cipher(self, *args, **kwargs): pass
	def do_handshake(self, *args, **kwargs): pass
	def peer_certificate(self, *args, **kwargs): pass
	def pending(self, *args, **kwargs): pass
	def read(self, *args, **kwargs): pass
	def shutdown(self, *args, **kwargs): pass
	def write(self, *args, **kwargs): pass
SSLType = SSLContext

def RAND_add(*args, **kwargs): pass
def RAND_egd(*args, **kwargs): pass
def RAND_status(*args, **kwargs): pass
def sslwrap(*args, **kwargs): pass


CERT_NONE = 0
CERT_OPTIONAL = 1
CERT_REQUIRED = 2
PROTOCOL_SSLv2 = 0
PROTOCOL_SSLv23 = 2
PROTOCOL_SSLv3 = 1
PROTOCOL_TLSv1 = 3
SSL_ERROR_EOF = 8
SSL_ERROR_INVALID_ERROR_CODE = 10
SSL_ERROR_SSL = 1
SSL_ERROR_SYSCALL = 5
SSL_ERROR_WANT_CONNECT = 7
SSL_ERROR_WANT_READ = 2
SSL_ERROR_WANT_WRITE = 3
SSL_ERROR_WANT_X509_LOOKUP = 4
SSL_ERROR_ZERO_RETURN = 6
