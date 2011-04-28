/* Millipede Function/Method object implementation */

#include "Python.h"
#include "funcobject.h"
#include "structmember.h"



PyObject *
MpFunction_New(const char *name,
                    MpFunction func,
                    const char *doc)
{
    MpFunctionObject *op;
    op = PyObject_GC_New(MpFunctionObject, &MpFunction_Type);
    if (op == NULL)
        return NULL;
    op->m_name = name;
    op->m_func = func;
    op->m_doc = doc;
    op->m_stack = NULL;
    op->m_stacksize = 0;
    op->m_annotations = NULL;
    op->m_defaults = NULL;
    op->m_kwdefaults = NULL;
    PyObject_GC_Track(op);
    return (PyObject *)op;
}

MpFunction
MpFunction_GetFunction(PyObject *op)
{
    if (!MpFunction_Check(op)) {
        PyErr_BadInternalCall();
        return NULL;
    }
    return (MpFunction)((MpFunctionObject *)op) -> m_func;
}


MpStack *
MpFunction_GetStack(PyObject *op)
{
    if (!MpFunction_Check(op)) {
        PyErr_BadInternalCall();
        return NULL;
    }
    MpFunctionObject *fn = (MpFunctionObject *)op;
    return fn->m_stack;
}


void
MpFunction_SetStack(PyObject *op, MpStack *stack, Py_ssize_t stacksize)
{
    if (!MpFunction_Check(op)) {
        PyErr_BadInternalCall();
        return;
    }
    MpFunctionObject *fn = (MpFunctionObject *)op;
    fn->m_stack = stack;
    fn->m_stacksize = stacksize;
}


PyObject *
MpFunction_Call(PyObject *func, PyObject *arg, PyObject *kw)
{
    MpFunctionObject* f = (MpFunctionObject*)func;
    MpFunction meth = MpFunction_GET_FUNCTION(f);
    return (*meth)(func, arg, kw);
}

/* Methods (the standard built-in methods, that is) */

static void
meth_dealloc(MpFunctionObject *m)
{
    PyObject_GC_UnTrack(m);
    if(m->m_stack) {
        MpStack_Destroy(m->m_stack, m->m_stacksize);
    }
    PyObject_GC_Del(m);
}

static PyObject *
meth_get__doc__(MpFunctionObject *m, void *closure)
{
    const char *doc = m->m_doc;
    if (doc != NULL)
        return PyUnicode_FromString(doc);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
meth_get__name__(MpFunctionObject *m, void *closure)
{
    return PyUnicode_FromString(m->m_name);
}

static PyObject *
meth_get__annotations__(MpFunctionObject *m, void *closure)
{
    PyObject *out;
    if(!m->m_annotations)
        out = Py_None;
    else
        out = m->m_annotations;
    Py_INCREF(out);
    return out;
}

static int
meth_set__annotations__(MpFunctionObject *m, PyObject *value)
{
    PyObject *tmp;

    if(value == NULL || !PyDict_Check(value)) {
        PyErr_SetString(PyExc_TypeError,
                    "__annotations__ must be set to a dict object");
        return -1;
    }
    tmp = m->m_annotations;
    Py_INCREF(value);
    m->m_annotations = value;
    Py_XDECREF(tmp);
    return 0;
}


static PyObject *
meth_get__defaults__(MpFunctionObject *m, void *closure)
{
    PyObject *out;
    if(!m->m_defaults)
        out = Py_None;
    else
        out = m->m_defaults;
    Py_INCREF(out);
    return out;
}

static int
meth_set__defaults__(MpFunctionObject *m, PyObject *value)
{
    PyObject *tmp;

    if(value == NULL || !PyTuple_Check(value)) {
        PyErr_SetString(PyExc_TypeError,
                    "__defaults__ must be set to a tuple object");
        return -1;
    }
    tmp = m->m_defaults;
    Py_INCREF(value);
    m->m_defaults = value;
    Py_XDECREF(tmp);
    return 0;
}


static PyObject *
meth_get__kwdefaults__(MpFunctionObject *m, void *closure)
{
    if(!m->m_kwdefaults) {
        Py_RETURN_NONE;
    }
    Py_INCREF(m->m_kwdefaults);
    return m->m_kwdefaults;
}

static int
meth_set__kwdefaults__(MpFunctionObject *m, PyObject *value)
{
    PyObject *tmp;

    if(value == NULL || !PyDict_Check(value)) {
        PyErr_SetString(PyExc_TypeError,
                    "__kwdefaults__ must be set to a dict object");
        return -1;
    }
    tmp = m->m_kwdefaults;
    Py_INCREF(value);
    m->m_kwdefaults = value;
    Py_XDECREF(tmp);
    return 0;
}


static int
meth_traverse(MpFunctionObject *m, visitproc visit, void *arg)
{
    Py_VISIT(m->m_annotations);
    Py_VISIT(m->m_defaults);
    Py_VISIT(m->m_kwdefaults);
    return 0;
}

static PyGetSetDef meth_getsets [] = {
    {"__doc__",  (getter)meth_get__doc__,  NULL, NULL},
    {"__name__", (getter)meth_get__name__, NULL, NULL},
    {"__annotations__", (getter)meth_get__annotations__, (setter)meth_set__annotations__, NULL},
    {"__defaults__", (getter)meth_get__defaults__, (setter)meth_set__defaults__, NULL},
    {"__kwdefaults__", (getter)meth_get__kwdefaults__, (setter)meth_set__kwdefaults__, NULL},
    {0}
};

static PyMemberDef meth_members[] = {
    {NULL}
};

static PyObject *
meth_repr(MpFunctionObject *m)
{
    return PyUnicode_FromFormat("<melano function %s", m->m_name);
}

static PyObject *
meth_richcompare(PyObject *self, PyObject *other, int op)
{
    MpFunctionObject *a, *b;
    PyObject *res;
    int eq;

    if ((op != Py_EQ && op != Py_NE) ||
        !MpFunction_Check(self) ||
        !MpFunction_Check(other))
    {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }
    a = (MpFunctionObject *)self;
    b = (MpFunctionObject *)other;
    eq = a->m_func == b->m_func;
    if (op == Py_EQ)
        res = eq ? Py_True : Py_False;
    else
        res = eq ? Py_False : Py_True;
    Py_INCREF(res);
    return res;
}

static Py_ssize_t
meth_hash(MpFunctionObject *a)
{
    Py_ssize_t x;
    x = _Py_HashPointer((void*)(a->m_func));
    return x;
}

/* Bind a function to an object */
static PyObject *
meth_descr_get(PyObject *func, PyObject *obj, PyObject *type)
{
    if (obj == Py_None || obj == NULL) {
        Py_INCREF(func);
        return func;
    }
    return PyMethod_New(func, obj);
}

PyTypeObject MpFunction_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "function",
    sizeof(MpFunctionObject),
    0,
    (destructor)meth_dealloc,                   /* tp_dealloc */
    0,                                          /* tp_print */
    0,                                          /* tp_getattr */
    0,                                          /* tp_setattr */
    0,                                          /* tp_reserved */
    (reprfunc)meth_repr,                        /* tp_repr */
    0,                                          /* tp_as_number */
    0,                                          /* tp_as_sequence */
    0,                                          /* tp_as_mapping */
    (hashfunc)meth_hash,                        /* tp_hash */
    MpFunction_Call,                      /* tp_call */
    0,                                          /* tp_str */
    PyObject_GenericGetAttr,                    /* tp_getattro */
    PyObject_GenericSetAttr,                    /* tp_setattro */
    0,                                          /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,    /* tp_flags */
    0,                                          /* tp_doc */
    (traverseproc)meth_traverse,                /* tp_traverse */
    0,                                          /* tp_clear */
    meth_richcompare,                           /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    0,                                          /* tp_methods */
    meth_members,                               /* tp_members */
    meth_getsets,                               /* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
    meth_descr_get,                                /* tp_descr_get */
};


void
MpFunction_Fini(void)
{
}
