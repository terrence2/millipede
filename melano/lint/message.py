'''
Defines an output from the linter.
'''

class LintMessage:
	def __init__(self, level:str, msg_name:str, location:str, context):
		self.level = level
		self.msg_name = msg_name
		self.location = location
		self.context = context

	#def report(self, log):
	#	fn = log.info
	#	if self.level == 'warning': fn = log.warning
	#	elif self.level == 'error': fn = log.error
	#	fn("{} @ line: {} col: {} -> {}".format(self.msg_name, self.context.startpos[0], self.context.startpos[1], self.context.endpos))
	

class LintError(LintMessage):
	def __init__(self, *args, **kwargs):
		super().__init__('error', *args, **kwargs)


class LintWarning(LintMessage):
	def __init__(self, *args, **kwargs):
		super().__init__('warning', *args, **kwargs)


