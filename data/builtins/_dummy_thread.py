class LockType:
	def __enter__(self): pass
	def __exit__(self, typ, val, tb): pass
	def acquire(self, waitflag=None): pass
	def locked(self): pass
	def release(self): pass

class error(Exception):
	pass

def allocate_lock(*args, **kwargs): pass
def exit(*args, **kwargs): pass
def get_ident(*args, **kwargs): pass
def interrupt_main(*args, **kwargs): pass
def start_new_thread(function, *args, **kwargs): pass
