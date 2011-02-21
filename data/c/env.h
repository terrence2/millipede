#ifndef _MELANO_ENV_H_
#define _MELANO_ENV_H_

#define likely(x)	__builtin_expect(!!(x), 1)
#define unlikely(x)	__builtin_expect(!!(x), 0)

void __err_capture__(char *file, int lineno, int clineno, char *context,
						char *srcline, int err_start, int err_end);
void __err_show_traceback__();

#endif // _MELANO_ENV_H_
