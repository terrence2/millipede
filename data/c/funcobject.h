/* Method object interface */

#ifndef _MP_FUNCTION_OBJECT_H_
#define _MP_FUNCTION_OBJECT_H_
#ifdef __cplusplus
extern "C" {
#endif

#include <Python.h>
#include "closure.h"

/* This is about the type 'builtin_function_or_method',
   not Python methods in user-defined classes.  See classobject.h
   for the latter. */

PyAPI_DATA(PyTypeObject) MpFunction_Type;

#define MpFunction_Check(op) (Py_TYPE(op) == &MpFunction_Type)

/* takes arguments: args, kwargs */
typedef PyObject *(*MpFunction)(PyObject *, PyObject *, PyObject *);

PyAPI_FUNC(MpFunction) MpFunction_GetFunction(PyObject *);
PyAPI_FUNC(PyObject *) MpFunction_GetSelf(PyObject *);

PyAPI_FUNC(MpStack *) MpFunction_GetStack(PyObject *);
PyAPI_FUNC(void) MpFunction_SetStack(PyObject *, MpStack *, Py_ssize_t);

/* Macros for direct access to these values. Type checks are *not*
   done, so use with care. */
#ifndef Py_LIMITED_API
#define MpFunction_GET_FUNCTION(func) \
        (((MpFunctionObject *)func) -> m_func)
#endif
PyAPI_FUNC(PyObject *) MpFunction_Call(PyObject *, PyObject *, PyObject *);


PyAPI_FUNC(PyObject *) MpFunction_New(
                                const char *name,
                                MpFunction func,
                                const char *doc
                                );



typedef struct {
    PyObject_HEAD
    // the name of the function
    const char *m_name;
    // the low-level function
    MpFunction m_func;
    // the docstring, or null
    const char *m_doc;
    // the (default NULL) stack array (only used by closures)
    MpStack *m_stack;
    Py_ssize_t m_stacksize;
    // the annotations, defaults, and kwdefaults
    PyObject *m_annotations;
    PyObject *m_defaults;
    PyObject *m_kwdefaults;
} MpFunctionObject;

#ifdef __cplusplus
}
#endif
#endif /* !_MP_FUNCTION_OBJECT_H_ */
