'''
Defines an output from the linter.
'''

class LintMessage:
	def __init__(self, level:str, msg_name:str, location:str, context):
		self.level = level
		self.msg_name = msg_name
		self.location = location
		self.context = context


class LintError(LintMessage):
	def __init__(self, *args, **kwargs):
		super().__init__('error', *args, **kwargs)


class LintWarning(LintMessage):
	def __init__(self, *args, **kwargs):
		super().__init__('warning', *args, **kwargs)


class LintStyle(LintMessage):
	def __init__(self, *args, **kwargs):
		super().__init__('coding', *args, **kwargs)
