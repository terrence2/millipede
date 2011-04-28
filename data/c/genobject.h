#ifndef _MP_GENERATOR_OBJECT_H_
#define _MP_GENERATOR_OBJECT_H_
#ifdef __cplusplus
extern "C" {
#endif

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

	// set to 1 after we have reached the end of generation for the first time
	int exhausted;
} MpGeneratorObject;

PyObject * MpGenerator_New(char *name, coro_func func, void *data, int stacksize);
void MpGenerator_Yield(PyObject *self);
coro_context * MpGenerator_GetContext(PyObject *self);
coro_context * MpGenerator_GetSourceContext(PyObject *self);

int MpGenerator_EnterContext(PyObject *obj);
int MpGenerator_LeaveContext(PyObject *obj);
void MpGenerator_Initialize();

#ifdef __cplusplus
}
#endif
#endif // _MP_GENERATOR_OBJECT_H_
