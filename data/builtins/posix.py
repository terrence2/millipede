def _exit(c): pass
class stat_result:
	n_fields = 16
	n_sequence_fields = 10
	n_unnamed_fields = 3
	def __init__(self, *args, **kwargs):
		self.st_atime = None
		self.st_blksize = None
		self.st_blocks = None
		self.st_ctime = None
		self.st_dev = None
		self.st_gid = None
		self.st_ino = None
		self.st_mode = None
		self.st_mtime = None
		self.st_nlink = None
		self.st_rdev = None
		self.st_size = None
		self.st_uid = None

class statvfs_result:
	n_fields = 10
	n_sequence_fields = 10
	n_unnamed_fields = 0
	def __init__(self, *args, **kwargs):
		self.f_bavail = None
		self.f_bfree = None
		self.f_blocks = None
		self.f_bsize = None
		self.f_favail = None
		self.f_ffree = None
		self.f_files = None
		self.f_flag = None
		self.f_frsize = None
		self.f_namemax = None

def WCOREDUMP(*args, **kwargs): pass
def WEXITSTATUS(*args, **kwargs): pass
def WIFCONTINUED(*args, **kwargs): pass
def WIFEXITED(*args, **kwargs): pass
def WIFSIGNALED(*args, **kwargs): pass
def WIFSTOPPED(*args, **kwargs): pass
def WSTOPSIG(*args, **kwargs): pass
def WTERMSIG(*args, **kwargs): pass

def abort(*args, **kwargs): pass
def access(*args, **kwargs): pass
def chdir(*args, **kwargs): pass
def chmod(*args, **kwargs): pass
def chown(*args, **kwargs): pass
def chroot(*args, **kwargs): pass
def close(*args, **kwargs): pass
def closerange(*args, **kwargs): pass
def confstr(*args, **kwargs): pass
def ctermid(*args, **kwargs): pass
def device_encoding(*args, **kwargs): pass
def dup(*args, **kwargs): pass
def dup2(*args, **kwargs): pass
def execv(*args, **kwargs): pass
def execve(*args, **kwargs): pass
def fchdir(*args, **kwargs): pass
def fchmod(*args, **kwargs): pass
def fchown(*args, **kwargs): pass
def fdatasync(*args, **kwargs): pass
def fork(*args, **kwargs): pass
def forkpty(*args, **kwargs): pass
def fpathconf(*args, **kwargs): pass
def fstat(*args, **kwargs): pass
def fstatvfs(*args, **kwargs): pass
def fsync(*args, **kwargs): pass
def ftruncate(*args, **kwargs): pass
def getcwd(*args, **kwargs): pass
def getcwdb(*args, **kwargs): pass
def getegid(*args, **kwargs): pass
def geteuid(*args, **kwargs): pass
def getgid(*args, **kwargs): pass
def getgroups(*args, **kwargs): pass
def getloadavg(*args, **kwargs): pass
def getlogin(*args, **kwargs): pass
def getpgid(*args, **kwargs): pass
def getpgrp(*args, **kwargs): pass
def getpid(*args, **kwargs): pass
def getppid(*args, **kwargs): pass
def getsid(*args, **kwargs): pass
def getuid(*args, **kwargs): pass
def isatty(*args, **kwargs): pass
def kill(*args, **kwargs): pass
def killpg(*args, **kwargs): pass
def lchown(*args, **kwargs): pass
def link(*args, **kwargs): pass
def listdir(*args, **kwargs): pass
def lseek(*args, **kwargs): pass
def lstat(*args, **kwargs): pass
def major(*args, **kwargs): pass
def makedev(*args, **kwargs): pass
def minor(*args, **kwargs): pass
def mkdir(*args, **kwargs): pass
def mkfifo(*args, **kwargs): pass
def mknod(*args, **kwargs): pass
def nice(*args, **kwargs): pass
def open(*args, **kwargs): pass
def openpty(*args, **kwargs): pass
def pathconf(*args, **kwargs): pass
def pipe(*args, **kwargs): pass
def putenv(*args, **kwargs): pass
def read(*args, **kwargs): pass
def readlink(*args, **kwargs): pass
def remove(*args, **kwargs): pass
def rename(*args, **kwargs): pass
def rmdir(*args, **kwargs): pass
def setegid(*args, **kwargs): pass
def seteuid(*args, **kwargs): pass
def setgid(*args, **kwargs): pass
def setgroups(*args, **kwargs): pass
def setpgid(*args, **kwargs): pass
def setpgrp(*args, **kwargs): pass
def setregid(*args, **kwargs): pass
def setreuid(*args, **kwargs): pass
def setsid(*args, **kwargs): pass
def setuid(*args, **kwargs): pass
def stat(*args, **kwargs): pass
def stat_float_times(*args, **kwargs): pass
def statvfs(*args, **kwargs): pass
def strerror(*args, **kwargs): pass
def symlink(*args, **kwargs): pass
def sysconf(*args, **kwargs): pass
def system(*args, **kwargs): pass
def tcgetpgrp(*args, **kwargs): pass
def tcsetpgrp(*args, **kwargs): pass
def times(*args, **kwargs): pass
def ttyname(*args, **kwargs): pass
def umask(*args, **kwargs): pass
def uname(*args, **kwargs): pass
def unlink(*args, **kwargs): pass
def unsetenv(*args, **kwargs): pass
def utime(*args, **kwargs): pass
def wait(*args, **kwargs): pass
def wait3(*args, **kwargs): pass
def wait4(*args, **kwargs): pass
def waitpid(*args, **kwargs): pass
def write(*args, **kwargs): pass


EX_CANTCREAT = 73
EX_CONFIG = 78
EX_DATAERR = 65
EX_IOERR = 74
EX_NOHOST = 68
EX_NOINPUT = 66
EX_NOPERM = 77
EX_NOUSER = 67
EX_OK = 0
EX_OSERR = 71
EX_OSFILE = 72
EX_PROTOCOL = 76
EX_SOFTWARE = 70
EX_TEMPFAIL = 75
EX_UNAVAILABLE = 69
EX_USAGE = 64
F_OK = 0
NGROUPS_MAX = 65536
O_APPEND = 1024
O_ASYNC = 8192
O_CREAT = 64
O_DIRECT = 16384
O_DIRECTORY = 65536
O_DSYNC = 4096
O_EXCL = 128
O_LARGEFILE = 0
O_NDELAY = 2048
O_NOATIME = 262144
O_NOCTTY = 256
O_NOFOLLOW = 131072
O_NONBLOCK = 2048
O_RDONLY = 0
O_RDWR = 2
O_RSYNC = 4096
O_SYNC = 4096
O_TRUNC = 512
O_WRONLY = 1
R_OK = 4
TMP_MAX = 238328
WCONTINUED = 8
WNOHANG = 1
WUNTRACED = 2
W_OK = 2
X_OK = 1
