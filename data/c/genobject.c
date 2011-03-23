/* A generator is the type returned by a generator function or comprehension
	to provide values. */
#include "genobject.h"

// Initialized with MelanoGen_Initialize and used for returing from a coroutine
//	to the main thread.
static coro_context __main_coroutine__;


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
gen_iternext(MelanoGenObject *gen)
{
	PyObject *rv;
	coro_transfer(gen->coro_source, &gen->coro);
	rv = ((PyObject **)(gen->data))[1];
	if(!rv) {
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
	0, //(traverseproc)gen_traverse,                 /* tp_traverse */
	0,                                          /* tp_clear */
	0,                                          /* tp_richcompare */
	0, //offsetof(PyGenObject, gi_weakreflist),      /* tp_weaklistoffset */
	PyObject_SelfIter,                          /* tp_iter */
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
MelanoGen_New(char *name, coro_func func, void *data, int stacksize, coro_context *source)
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
	gen->coro_source = source;
	if(!source) {
		gen->coro_source = &__main_coroutine__;
	}

	gen->stacksize = stacksize;
	gen->stack = calloc(1, stacksize);
	if(!gen->stack) {
		return PyErr_NoMemory();
	}

	// NOTE: not reentrant -- this depends on the GIL currently
	coro_create(&gen->coro, func, data, gen->stack, gen->stacksize);

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

void
MelanoGen_Initialize()
{
	coro_create(&__main_coroutine__, 0, 0, 0, 0);
}
