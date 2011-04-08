/* A generator is the type returned by a generator function or comprehension
	to provide values. */
#include "genobject.h"

// Initialized with MelanoGen_Initialize and used for returing from a coroutine
//	to the main thread.
static coro_context __main_coroutine__;

#define GEN_CAPSULE_NAME "coroutine context"
#define RETURN_INDEX 2

#define DEBUG 0

static void
gen_del(PyObject *self) {
	MelanoGenObject *gen = (MelanoGenObject *)self;
	coro_destroy(&gen->coro);
	free(gen->stack);
	gen->stack = NULL;
	if(gen->name) {
		free(gen->name);
		gen->name = NULL;
	}
	if(gen->data) {
		free(gen->data);
		gen->data = NULL;
	}
}

static void
gen_dealloc(MelanoGenObject *gen)
{
	PyObject_Del(gen);
}

static PyObject *
gen_iter(PyObject *obj)
{
	MelanoGenObject *gen = (MelanoGenObject *)obj;
	PyObject *dict, *stack, *cap;

    // get the thread state dict
    dict = PyThreadState_GET()->dict;
    if(!dict)
		Py_FatalError("No threadstate dict set");

	// get the generator context stack
	stack = PyDict_GetItemString(dict, "__generator_stack__");
	if(!stack)
		Py_FatalError("No generator stack in thread.");

	// get the topmost coroutine (in a capsule)
	cap = PyList_GetItem(stack, PyList_Size(stack) - 1);
	if(!cap)
		return NULL;

	// set from the top coroutine
	gen->coro_source = PyCapsule_GetPointer(cap, GEN_CAPSULE_NAME);

	if(DEBUG)
		printf("GetIter:     %p\n", gen->coro_source);

    Py_INCREF(obj);
    return obj;
}

static PyObject *
gen_iternext(MelanoGenObject *gen)
{
	PyObject *rv;

	// once we have reached the end, we cannot run again
	if(gen->exhausted) {
		PyErr_SetNone(PyExc_StopIteration);
		return NULL;
	}

	// If the runtime did not call __iter__ to get an iterator first, we need
	// to call it manually to set ourself up for usage.
	if(!gen->coro_source) {
		PyObject *obj = gen_iter((PyObject *)gen);
		Py_DECREF(obj);
	}

	if(DEBUG)
		printf("(0)IterNext: %p -> %p\n", gen->coro_source, &gen->coro);
	coro_transfer(gen->coro_source, &gen->coro);
	if(DEBUG)
		printf("(1)IterNext: %p -> %p\n", gen->coro_source, &gen->coro);
	rv = ((PyObject **)(gen->data))[RETURN_INDEX];
	if(!rv) {
		gen->exhausted = 1;
		PyErr_SetNone(PyExc_StopIteration);
		return NULL;
	}
	return rv;
}

static PyObject *
gen_repr(MelanoGenObject *gen)
{
	return PyUnicode_FromFormat("<generator object %s at %p>", gen->name, gen);
}

static PyObject *
gen_get_name(MelanoGenObject *gen)
{
	PyObject *name = PyUnicode_FromString(gen->name);
	return name;
}


PyDoc_STRVAR(gen__name__doc__,
"Return the name of the generator's associated code object.");

static PyGetSetDef gen_getsetlist[] = {
    {"__name__", (getter)gen_get_name, NULL, gen__name__doc__},
    {NULL}
};



PyTypeObject MelanoGen_Type = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	"generator",                                /* tp_name */
	sizeof(MelanoGenObject),                 /* tp_basicsize */
	0,                                          /* tp_itemsize */
	/* methods */
	(destructor)gen_dealloc,                    /* tp_dealloc */
	0,                                          /* tp_print */
	0,                                          /* tp_getattr */
	0,                                          /* tp_setattr */
	0,                                          /* tp_reserved */
	(reprfunc)gen_repr,                         /* tp_repr */
	0,                                          /* tp_as_number */
	0,                                          /* tp_as_sequence */
	0,                                          /* tp_as_mapping */
	0,                                          /* tp_hash */
	0,                                          /* tp_call */
	0,                                          /* tp_str */
	PyObject_GenericGetAttr,                    /* tp_getattro */
	0,                                          /* tp_setattro */
	0,                                          /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT,                         /* tp_flags */
	0,                                          /* tp_doc */
	0, //(traverseproc)gen_traverse,            /* tp_traverse */
	0,                                          /* tp_clear */
	0,                                          /* tp_richcompare */
	0, //offsetof(PyGenObject, gi_weakreflist), /* tp_weaklistoffset */
	gen_iter,                                   /* tp_iter */
	(iternextfunc)gen_iternext,                 /* tp_iternext */
	0, //(WE MAY NEED THIS)gen_methods,                                /* tp_methods */
	0, //gen_memberlist,                             /* tp_members */
	gen_getsetlist,                             /* tp_getset */
	0,                                          /* tp_base */
	0,                                          /* tp_dict */

	0,                                          /* tp_descr_get */
	0,                                          /* tp_descr_set */
	0,                                          /* tp_dictoffset */
	0,                                          /* tp_init */
	0,                                          /* tp_alloc */
	0,                                          /* tp_new */
	0,                                          /* tp_free */
	0,                                          /* tp_is_gc */
	0,                                          /* tp_bases */
	0,                                          /* tp_mro */
	0,                                          /* tp_cache */
	0,                                          /* tp_subclasses */
	0,                                          /* tp_weaklist */
	gen_del,                                    /* tp_del */
};

PyObject *
MelanoGen_New(char *name, coro_func func, void *data, int stacksize)
{
	if(!name) {
		PyErr_BadArgument();
		return NULL;
	}

	MelanoGenObject *gen = PyObject_New(MelanoGenObject, &MelanoGen_Type);
	if(!gen) {
		return NULL;
	}

	gen->name = name;
	gen->data = data;
	gen->coro_source = NULL;
	gen->exhausted = 0;

	gen->stacksize = stacksize;
	gen->stack = calloc(1, stacksize);
	if(!gen->stack) {
		return PyErr_NoMemory();
	}

	// NOTE: not reentrant -- this depends on the GIL currently
	coro_create(&gen->coro, func, data, gen->stack, gen->stacksize);
	if(DEBUG)
		printf("New:         %p\n", &gen->coro);

	return (PyObject *)gen;
}

coro_context *
MelanoGen_GetContext(PyObject *self) {
	MelanoGenObject *gen = (MelanoGenObject *)self;
	return &gen->coro;
}

coro_context *
MelanoGen_GetSourceContext(PyObject *self) {
	MelanoGenObject *gen = (MelanoGenObject *)self;
	return gen->coro_source;
}

int
MelanoGen_EnterContext(PyObject *obj) {
	MelanoGenObject *gen = (MelanoGenObject *)obj;
	PyObject *dict, *stack, *cap;
	int rv;

    // get the thread state dict
    dict = PyThreadState_GET()->dict;
    if(!dict)
		Py_FatalError("No threadstate dict set");

	// get the generator context stack
	stack = PyDict_GetItemString(dict, "__generator_stack__");
	if(!stack)
		Py_FatalError("No generator stack in thread.");

	if(DEBUG) {
		cap = PyList_GetItem(stack, PyList_Size(stack) - 1);
		if(!cap) return -1;
		printf("EnterCtx:    %p -> %p\n", PyCapsule_GetPointer(cap, GEN_CAPSULE_NAME), &gen->coro);
	}

	// build a new capsule for this context
	cap = PyCapsule_New(&gen->coro, GEN_CAPSULE_NAME, NULL);
	if(!cap)
		return -1;

	// append our capsule
	rv = PyList_Append(stack, cap);
	if(rv)
		return -1;

	return 0;
}

int
MelanoGen_LeaveContext(PyObject *obj) {
	PyObject *dict, *stack, *top0, *top1;
	int rv;

    // get the thread state dict
    dict = PyThreadState_GET()->dict;
    if(!dict)
		Py_FatalError("No threadstate dict set");

	// get the generator context stack
	stack = PyDict_GetItemString(dict, "__generator_stack__");
	if(!stack)
		Py_FatalError("No generator stack in thread.");

	if(DEBUG) {
		top0 = PyList_GetItem(stack, PyList_Size(stack) - 1);
		if(!top0) return -1;
	}

	// pop the top element
	rv = PyList_SetSlice(stack, PyList_GET_SIZE(stack) - 1, PyList_GET_SIZE(stack), NULL);
	if(rv)
		return -1;

	if(DEBUG) {
		top1 = PyList_GetItem(stack, PyList_Size(stack) - 1);
		if(!top1) return -1;
		printf("LeaveCtx:    %p -> %p\n",
			PyCapsule_GetPointer(top0, GEN_CAPSULE_NAME),
			PyCapsule_GetPointer(top1, GEN_CAPSULE_NAME));
	}

	return 0;
}

void
MelanoGen_Yield(PyObject *self) {
	MelanoGenObject *gen = (MelanoGenObject *)self;

	if(DEBUG)
		printf("(0)GenYld:%p -> %p", &gen->coro, gen->coro_source);
	coro_transfer(&gen->coro, gen->coro_source);
	if(DEBUG)
		printf("(1)GenYld:%p -> %p", &gen->coro, gen->coro_source);
}


void
MelanoGen_Initialize()
{
	PyObject *dict, *stack, *cap;

	coro_create(&__main_coroutine__, 0, 0, 0, 0);

	if(DEBUG)
		printf("GenMain:     %p\n", &__main_coroutine__);

    // get the thread state dict
    dict = PyThreadState_GET()->dict;
    if(!dict) {
	    dict = PyThreadState_GET()->dict = PyDict_New();
	    if(!dict)
			Py_FatalError("Could not create thread state dict");
    }

	cap = PyCapsule_New(&__main_coroutine__, GEN_CAPSULE_NAME, NULL);
	if(!cap)
		Py_FatalError("could not create main coroutine capsule");

	stack = PyList_New(1);
	if(!stack)
		Py_FatalError("could not create generator stack");
	PyList_SET_ITEM(stack, 0, cap);

	PyDict_SetItemString(dict, "__generator_stack__", stack);
}
