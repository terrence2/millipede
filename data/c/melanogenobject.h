#ifndef _MELANO_GEN_OBJECT_H_
#define _MELANO_GEN_OBJECT_H_
#include <Python.h>
#include <pcl.h>

typedef struct {
	PyObject_HEAD
	char *name;
	void *data;
	coroutine_t coro;
} MelanoGenObject;

PyObject * MelanoGen_New(char *name, void *func, void *data, int stacksize);

#endif // _MELANO_GEN_OBJECT_H_
