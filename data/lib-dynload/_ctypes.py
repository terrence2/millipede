class ArgumentError(Exception):
	pass

class FormatError(Exception):
	pass

class CData:
	def __ctypes_from_outparam__(self, *args, **kwargs): pass
	def __hash__(self, *args, **kwargs): pass
	def __reduce__(self, *args, **kwargs): pass
	def __setstate__(self, *args, **kwargs): pass

class _SimpleCData(_CData):
	pass

class Array(_CData):
	def __delitem__(self, *args, **kwargs): pass
	def __getitem__(self, *args, **kwargs): pass
	def __init__(self, *args, **kwargs): pass
	def __len__(self, *args, **kwargs): pass
	def __setitem__(self, *args, **kwargs): pass

class PyCFuncPtr(_CData):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.argtypes = None
		self.errcheck = None
		self.restype = None
	def __bool__(self, *args, **kwargs): pass
	def __bool__(self): pass
	def __call__(self, *args, **kwargs): pass
CFuncPtr = PyCFuncPtr

class Structure(_CData):
	pass

class Union(_CData):
	pass

class _Pointer(_CData):
	pass


def LoadLibrary(*args, **kwargs): pass
def POINTER(*args, **kwargs): pass
def PyObj_FromPtr(*args, **kwargs): pass
def Py_DECREF(*args, **kwargs): pass
def Py_INCREF(*args, **kwargs): pass
def addressof(*args, **kwargs): pass
def alignment(*args, **kwargs): pass
def buffer_info(*args, **kwargs): pass
def byref(*args, **kwargs): pass
def call_cdeclfunction(*args, **kwargs): pass
def call_function(*args, **kwargs): pass
def dlclose(*args, **kwargs): pass
def dlopen(*args, **kwargs): pass
def dlsym(*args, **kwargs): pass
def get_errno(*args, **kwargs): pass
def pointer(*args, **kwargs): pass
def resize(*args, **kwargs): pass
def set_conversion_mode(*args, **kwargs): pass
def set_errno(*args, **kwargs): pass
def sizeof(*args, **kwargs): pass
def get_last_error(*args, **kwargs): pass
def set_last_error(*args, **kwargs): pass
def _memmove_addr(*args, **kwargs): pass
def _memset_addr(*args, **kwargs): pass
def _string_at_addr(*args, **kwargs): pass
def _cast_addr(*args, **kwargs): pass
def _wstring_at_addr(*args, **kwargs): pass
def _check_HRESULT(*args, **kwargs): pass

__version__ = None
_pointer_type_cache = None
FUNCFLAG_CDECL = 1
FUNCFLAG_PYTHONAPI = 4
FUNCFLAG_STDCALL = None
FUNCFLAG_USE_ERRNO = 8
FUNCFLAG_USE_LASTERROR = 16
RTLD_GLOBAL = 256
RTLD_LOCAL = 0
