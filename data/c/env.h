#ifndef _MP_ENV_H_
#define _MP_ENV_H_

#define likely(x)	__builtin_expect(!!(x), 1)
#define unlikely(x)	__builtin_expect(!!(x), 0)

#define Mp_DECREF_ALL(fst, rst...) Py_DECREF(fst); Mp_DECREF_ALL(...rst);

void __init__(int argc, wchar_t **argv);

void __err_capture__(char *file, int lineno, int clineno, char *context,
						char *srcline, int err_start, int err_end);
void __err_show_traceback__();
void __err_clear__();

#endif // _MP_ENV_H_
