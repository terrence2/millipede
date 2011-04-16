/* Method object interface */

#ifndef Py_MELANOFUNCOBJECT_H
#define Py_MELANOFUNCOBJECT_H
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    Py_ssize_t refcnt;
    PyObject **locals;
} MelanoLocals;

MelanoLocals * MelanoLocals_Create(Py_ssize_t cnt);
void MelanoLocals_Destroy(MelanoLocals **stack, Py_ssize_t level);

MelanoLocals * MelanoStack_FetchLocals(MelanoLocals **stack, Py_ssize_t level);
void MelanoStack_RestoreLocals(MelanoLocals **stack, Py_ssize_t level, MelanoLocals *locals);

MelanoLocals ** MelanoStack_Create(Py_ssize_t cnt);
void MelanoStack_SetLocals(MelanoLocals **stack, Py_ssize_t level, MelanoLocals *locals);
void MelanoStack_Destroy(MelanoLocals **stack, Py_ssize_t cnt);


/* This is about the type 'builtin_function_or_method',
   not Python methods in user-defined classes.  See classobject.h
   for the latter. */

PyAPI_DATA(PyTypeObject) PyMelanoFunction_Type;

#define PyMelanoFunction_Check(op) (Py_TYPE(op) == &PyMelanoFunction_Type)

/* takes arguments: args, kwargs */
typedef PyObject *(*PyMelanoFunction)(PyObject *, PyObject *, PyObject *);

PyAPI_FUNC(PyMelanoFunction) PyMelanoFunction_GetFunction(PyObject *);
PyAPI_FUNC(PyObject *) PyMelanoFunction_GetSelf(PyObject *);

PyAPI_FUNC(MelanoLocals **) PyMelanoFunction_GetStack(PyObject *);
PyAPI_FUNC(void) PyMelanoFunction_SetStack(PyObject *, MelanoLocals **, Py_ssize_t);

/* Macros for direct access to these values. Type checks are *not*
   done, so use with care. */
#ifndef Py_LIMITED_API
#define PyMelanoFunction_GET_FUNCTION(func) \
        (((PyMelanoFunctionObject *)func) -> m_func)
#endif
PyAPI_FUNC(PyObject *) PyMelanoFunction_Call(PyObject *, PyObject *, PyObject *);


PyAPI_FUNC(PyObject *) PyMelanoFunction_New(
                                const char *name,
                                PyMelanoFunction func,
                                const char *doc
                                );



typedef struct {
    PyObject_HEAD
    // the name of the function
    const char *m_name;
    // the low-level function
    PyMelanoFunction m_func;
    // the docstring, or null
    const char *m_doc;
    // the (default NULL) stack array (only used by closures)
    MelanoLocals **m_stack;
    Py_ssize_t m_stacksize;
    // the annotations, defaults, and kwdefaults
    PyObject *m_annotations;
    PyObject *m_defaults;
    PyObject *m_kwdefaults;
} PyMelanoFunctionObject;

PyAPI_FUNC(int) PyMelanoFunction_ClearFreeList(void);

#ifdef __cplusplus
}
#endif
#endif /* !Py_MELANOFUNCOBJECT_H */
