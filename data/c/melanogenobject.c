/* A generator is the type returned by a generator function or comprehension
	to provide values. */
#include "melanogenobject.h"

static void
gen_del(PyObject *self) {
	MelanoGenObject *gen = (MelanoGenObject *)self;
	co_delete(gen->coro);
	gen->coro = NULL;
	if(gen->data) {
		free(gen->data);
		gen->data = NULL;
	}
}

static void
gen_dealloc(MelanoGenObject *gen)
{
	assert(gen->coro == NULL);
	PyObject_Del(gen);
}

static PyObject *
gen_iternext(MelanoGenObject *gen) {
	PyObject *out;
	co_call(gen->coro);
	out = (PyObject *)co_get_data(gen->coro);
	return out;
}

static PyObject *
gen_repr(MelanoGenObject *gen)
{
	return PyUnicode_FromFormat("<generator object %S at %p>", gen->name, gen);
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
MelanoGen_New(char *name, void *func, void *data, int stacksize) {
	MelanoGenObject *gen = PyObject_New(MelanoGenObject, &MelanoGen_Type);
	if(!gen) {
		return NULL;
	}

	gen->name = name;
	gen->data = data;

	gen->coro = co_create(func, data, NULL, stacksize);
	if(!gen->coro) {
		return NULL;
	}

	return (PyObject *)gen;
}
