#include <Python.h>

void __err_capture__(char *file, int lineno, int clineno, char *context,
				char *srcline, int err_start, int err_end) {
	PyObject *val, *src, *dict, *tb;
	int rv;

	// build current value
	val = PyUnicode_FromFormat("  File \"%s\", line %d (%d), in %s\n", file, lineno, clineno, context);
	if(!val)
		Py_FatalError("Failed to format captured error");
	src = PyUnicode_FromFormat("    %s\n", srcline);
	if(!src)
		Py_FatalError("Failed to format captured source line");

	// get the thread state dict
	dict = PyThreadState_GET()->dict;
	if(!dict) {
		dict = PyThreadState_GET()->dict = PyDict_New();
		if(!dict)
			Py_FatalError("Could not create thread state dict");
	}

	// get the traceback list
	tb = PyDict_GetItemString(dict, "__melano_traceback__");
	if(!tb) {
		tb = PyList_New(0);
		if(!tb)
			Py_FatalError("Could not create traceback list");
		rv = PyDict_SetItemString(dict, "__melano_traceback__", tb);
		if(rv == -1)
			Py_FatalError("Failed to insert traceback into thread state");
	}

	// add the value to the traceback list
	rv = PyList_Append(tb, src);
	if(rv == -1)
		Py_FatalError("Failed to append to traceback");
	rv = PyList_Append(tb, val);
	if(rv == -1)
		Py_FatalError("Failed to append to traceback");
}


void __err_show_traceback__() {
	PyObject *dict, *tb, *val;
	Py_ssize_t i, cnt;

	fprintf(stderr, "Traceback (most recent call last):\n");

	dict = PyThreadState_GET()->dict;
	if(!dict)
		return;
	tb = PyDict_GetItemString(dict, "__melano_traceback__");
	if(!tb)
		return;

	cnt = PyList_Size(tb);
	for(i = cnt - 1; i > -1; i--) {
		val = PyList_GET_ITEM(tb, i);
		PyObject_Print(val, stderr, Py_PRINT_RAW);
	}
}
