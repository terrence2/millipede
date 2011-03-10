
/* Method object interface */

#ifndef Py_MELANOFUNCOBJECT_H
#define Py_MELANOFUNCOBJECT_H
#ifdef __cplusplus
extern "C" {
#endif

/* This is about the type 'builtin_function_or_method',
   not Python methods in user-defined classes.  See classobject.h
   for the latter. */

PyAPI_DATA(PyTypeObject) PyMelanoFunction_Type;

#define PyMelanoFunction_Check(op) (Py_TYPE(op) == &PyMelanoFunction_Type)

/* takes arguments: args, kwargs */
typedef PyObject *(*PyMelanoFunction)(PyObject *, PyObject *);

PyAPI_FUNC(PyMelanoFunction) PyMelanoFunction_GetFunction(PyObject *);
PyAPI_FUNC(PyObject *) PyMelanoFunction_GetSelf(PyObject *);
PyAPI_FUNC(int) PyMelanoFunction_GetFlags(PyObject *);

/* Macros for direct access to these values. Type checks are *not*
   done, so use with care. */
#ifndef Py_LIMITED_API
#define PyMelanoFunction_GET_FUNCTION(func) \
        (((PyMelanoFunctionObject *)func) -> m_func)
#endif
PyAPI_FUNC(PyObject *) PyMelanoFunction_Call(PyObject *, PyObject *, PyObject *);


PyAPI_FUNC(PyObject *) PyMelanoFunction_New(const char *name, \
                                PyMelanoFunction func, const char *doc);

typedef struct {
    PyObject_HEAD
    const char *m_name;
    PyMelanoFunction m_func;
    const char *m_doc;
} PyMelanoFunctionObject;

PyAPI_FUNC(int) PyMelanoFunction_ClearFreeList(void);

#ifdef __cplusplus
}
#endif
#endif /* !Py_MELANOFUNCOBJECT_H */
