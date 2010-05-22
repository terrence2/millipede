
class fwddecl(type):
	'''Metaclass to allow type annotations of the current class within the
		class definition.'''
	@classmethod
	def __prepare__(metacls, name, bases, **kwargs):
		return {name: metacls}

	def __new__(cls, name, bases, classdict):
		del classdict[name]
		real = type.__new__(cls, name, bases, classdict)
		for func in classdict.values():
			if type(func).__name__ == 'function':
				for key, ann in func.__annotations__.items():
					if ann == fwddecl:
						func.__annotations__[key] = real.__mro__[0]
		return real

