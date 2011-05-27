
def qt_debug():
	from PyQt4.QtCore import pyqtRemoveInputHook
	pyqtRemoveInputHook()
	import pdb
	pdb.set_trace()


