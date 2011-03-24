#ifndef _MELANO_GEN_OBJECT_H_
#define _MELANO_GEN_OBJECT_H_
#include <Python.h>
#include <coro.h>

typedef struct {
	PyObject_HEAD

	// The name of this object, as for normal generator objects.
	//  - this will be freed on exit, so pass a malloced pointer.
	char *name;

	// Data passed into the coroutine on start.
	//  - this must be present
	//  - the first slot must be PyObject* which will point to the yielded
	//	  value after every iteration.
	//  - this will be freed on deletion, so pass a malloced pointer.
	void *data;

	// internally alloced based on the passed stack size.
	unsigned char *stack;
	Py_ssize_t stacksize;

	// The source "coroutine", which we will jump back to on yield.
	coro_context *coro_source;

	// the coroutine context representing the called function.
	coro_context coro;
} MelanoGenObject;

PyObject * MelanoGen_New(char *name, coro_func func, void *data, int stacksize);
coro_context * MelanoGen_GetContext(PyObject *self);
coro_context * MelanoGen_GetSourceContext(PyObject *self);

int MelanoGen_EnterContext(PyObject *obj);
int MelanoGen_LeaveContext(PyObject *obj);
void MelanoGen_Initialize();

#endif // _MELANO_GEN_OBJECT_H_
