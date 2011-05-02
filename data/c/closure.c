/* Objects and helpers used to implement python closures on top of C */
#include "closure.h"


MpLocals *
MpLocals_Create(Py_ssize_t cnt) {
    MpLocals *locals;
    locals = (MpLocals *)malloc(sizeof(MpLocals));
    locals->refcnt = 0;
    if(cnt > 0) {
        locals->locals = (PyObject **)calloc(cnt, sizeof(PyObject*));
    } else {
        locals->locals = NULL;
    }
    return locals;
}

void
MpLocals_Destroy(MpStack *stack, Py_ssize_t level) {
    if(!stack[level])
        return;
    stack[level]->refcnt -= 1;
    if(stack[level]->refcnt == 0) {
        if(stack[level]->locals) {
            free(stack[level]->locals);
        }
        free(stack[level]);
        stack[level] = NULL;
    }
}

MpStack *
MpStack_Create(Py_ssize_t cnt) {
    MpStack *stack;
    stack = calloc(cnt, sizeof(MpStack));
    return stack;
}

void
MpStack_SetLocals(MpStack *stack, Py_ssize_t level, MpLocals *locals) {
    stack[level] = locals;
    locals->refcnt += 1;
}

MpLocals *
MpStack_FetchLocals(MpStack *stack, Py_ssize_t level) {
    return stack[level];
}

void
MpStack_RestoreLocals(MpStack *stack, Py_ssize_t level, MpLocals *locals) {
    stack[level] = locals;
}

void
MpStack_Destroy(MpStack *stack, Py_ssize_t cnt) {
    Py_ssize_t i;
    for(i = 0; i < cnt; i++ ) {
        MpLocals_Destroy(stack, i);
    }
    free(stack);
}
