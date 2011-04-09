class ZipImportError(ImportError): pass
class zipimporter:
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.archive = None
		self.prefix = None
	def find_module(self, *args, **kwargs): pass
	def get_code(self, *args, **kwargs): pass
	def get_data(self, *args, **kwargs): pass
	def get_filename(self, *args, **kwargs): pass
	def get_source(self, *args, **kwargs): pass
	def is_package(self, *args, **kwargs): pass
	def load_module(self, *args, **kwargs): pass
