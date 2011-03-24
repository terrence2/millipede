
/* Method object implementation */

#include "Python.h"
#include "funcobject.h"
#include "structmember.h"


MelanoLocals *
MelanoLocals_Create(Py_ssize_t cnt) {
    MelanoLocals *locals;
    locals = (MelanoLocals *)malloc(sizeof(MelanoLocals));
    locals->refcnt = 0;
    if(cnt > 0) {
        locals->locals = (PyObject **)calloc(cnt, sizeof(PyObject*));
    } else {
        locals->locals = NULL;
    }
    return locals;
}

void
MelanoLocals_Destroy(MelanoLocals **stack, Py_ssize_t level) {
    stack[level]->refcnt -= 1;
    if(stack[level]->refcnt == 0) {
        if(stack[level]->locals)
            free(stack[level]->locals);
        free(stack[level]);
        stack[level] = NULL;
    }
}

MelanoLocals **
MelanoStack_Create(Py_ssize_t cnt) {
    MelanoLocals** stack;
    stack = calloc(cnt, sizeof(MelanoLocals*));
    return stack;
}

void
MelanoStack_SetLocals(MelanoLocals **stack, Py_ssize_t level, MelanoLocals *locals) {
    stack[level] = locals;
    locals->refcnt += 1;
}

MelanoLocals *
MelanoStack_FetchLocals(MelanoLocals **stack, Py_ssize_t level) {
    return stack[level];
}

void
MelanoStack_RestoreLocals(MelanoLocals **stack, Py_ssize_t level, MelanoLocals *locals) {
    stack[level] = locals;
}

void
MelanoStack_Destroy(MelanoLocals **stack, Py_ssize_t cnt) {
    Py_ssize_t i;
    for(i = 0; i < cnt; i++ ) {
        MelanoLocals_Destroy(stack, i);
    }
    free(stack);
}

PyObject *
PyMelanoFunction_New(const char *name,
                    PyMelanoFunction func,
                    const char *doc)
{
    PyMelanoFunctionObject *op;
    op = PyObject_GC_New(PyMelanoFunctionObject, &PyMelanoFunction_Type);
    if (op == NULL)
        return NULL;
    op->m_name = name;
    op->m_func = func;
    op->m_doc = doc;
    op->m_stack = NULL;
    op->m_stacksize = 0;
    _PyObject_GC_TRACK(op);
    return (PyObject *)op;
}

PyMelanoFunction
PyMelanoFunction_GetFunction(PyObject *op)
{
    if (!PyMelanoFunction_Check(op)) {
        PyErr_BadInternalCall();
        return NULL;
    }
    return (PyMelanoFunction)((PyMelanoFunctionObject *)op) -> m_func;
}


MelanoLocals **
PyMelanoFunction_GetStack(PyObject *op)
{
    if (!PyMelanoFunction_Check(op)) {
        PyErr_BadInternalCall();
        return NULL;
    }
    PyMelanoFunctionObject *fn = (PyMelanoFunctionObject *)op;
    return fn->m_stack;
}


void
PyMelanoFunction_SetStack(PyObject *op, MelanoLocals **stack, Py_ssize_t stacksize)
{
    if (!PyMelanoFunction_Check(op)) {
        PyErr_BadInternalCall();
        return;
    }
    PyMelanoFunctionObject *fn = (PyMelanoFunctionObject *)op;
    fn->m_stack = stack;
    fn->m_stacksize = stacksize;
}


PyObject *
PyMelanoFunction_Call(PyObject *func, PyObject *arg, PyObject *kw)
{
    PyMelanoFunctionObject* f = (PyMelanoFunctionObject*)func;
    PyMelanoFunction meth = PyMelanoFunction_GET_FUNCTION(f);
    return (*meth)(func, arg, kw);
}

/* Methods (the standard built-in methods, that is) */

static void
meth_dealloc(PyMelanoFunctionObject *m)
{
    if(m->m_stack) {
        MelanoStack_Destroy(m->m_stack, m->m_stacksize);
    }
    _PyObject_GC_UNTRACK(m);
    PyObject_GC_Del(m);
}

static PyObject *
meth_get__doc__(PyMelanoFunctionObject *m, void *closure)
{
    const char *doc = m->m_doc;
    if (doc != NULL)
        return PyUnicode_FromString(doc);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
meth_get__name__(PyMelanoFunctionObject *m, void *closure)
{
    return PyUnicode_FromString(m->m_name);
}

static int
meth_traverse(PyMelanoFunctionObject *m, visitproc visit, void *arg)
{
    return 0;
}

static PyGetSetDef meth_getsets [] = {
    {"__doc__",  (getter)meth_get__doc__,  NULL, NULL},
    {"__name__", (getter)meth_get__name__, NULL, NULL},
    {0}
};

static PyMemberDef meth_members[] = {
    {NULL}
};

static PyObject *
meth_repr(PyMelanoFunctionObject *m)
{
    return PyUnicode_FromFormat("<melano function %s", m->m_name);
}

static PyObject *
meth_richcompare(PyObject *self, PyObject *other, int op)
{
    PyMelanoFunctionObject *a, *b;
    PyObject *res;
    int eq;

    if ((op != Py_EQ && op != Py_NE) ||
        !PyMelanoFunction_Check(self) ||
        !PyMelanoFunction_Check(other))
    {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }
    a = (PyMelanoFunctionObject *)self;
    b = (PyMelanoFunctionObject *)other;
    eq = a->m_func == b->m_func;
    if (op == Py_EQ)
        res = eq ? Py_True : Py_False;
    else
        res = eq ? Py_False : Py_True;
    Py_INCREF(res);
    return res;
}

static Py_hash_t
meth_hash(PyMelanoFunctionObject *a)
{
    Py_hash_t x;
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

PyTypeObject PyMelanoFunction_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "builtin_function_or_method",
    sizeof(PyMelanoFunctionObject),
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
    PyMelanoFunction_Call,                           /* tp_call */
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
PyMelanoFunction_Fini(void)
{
}
