#ifndef _MELANO_ENV_H_
#define _MELANO_ENV_H_

#define likely(x)	__builtin_expect(!!(x), 1)
#define unlikely(x)	__builtin_expect(!!(x), 0)

#endif // _MELANO_ENV_H_
