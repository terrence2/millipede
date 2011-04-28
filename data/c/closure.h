/* Objects and helpers used to implement python closures on top of C */
#ifndef _MP_CLOSURE_H_
#define _MP_CLOSURE_H_
#ifdef __cplusplus
extern "C" {
#endif

#include <Python.h>

typedef struct {
    Py_ssize_t refcnt;
    PyObject **locals;
} MpLocals;

typedef MpLocals* MpStack;

MpLocals * MpLocals_Create(Py_ssize_t cnt);
void MpLocals_Destroy(MpStack *stack, Py_ssize_t level);

MpLocals * MpStack_FetchLocals(MpStack *stack, Py_ssize_t level);
void MpStack_RestoreLocals(MpStack *stack, Py_ssize_t level, MpLocals *locals);

MpStack * MpStack_Create(Py_ssize_t cnt);
void MpStack_SetLocals(MpStack *stack, Py_ssize_t level, MpLocals *locals);
void MpStack_Destroy(MpStack *stack, Py_ssize_t cnt);

#ifdef __cplusplus
}
#endif
#endif /* !_MP_FUNCTION_OBJECT_H_ */
