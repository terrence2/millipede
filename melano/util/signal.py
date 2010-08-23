'''
Copyright (c) 2010, Terrence Cole.
'''

class Signal:
	def __init__(self):
		self.targets = []

	def connect(self, target):
		self.targets.append(target)

	def emit(self, *args, **kwargs):
		for tgt in self.targets:
			tgt(*args, **kwargs)

