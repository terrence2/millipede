GCC=gcc
CFLAGS=-DCORO_UCONTEXT
CFLAGS_WARN=-Wall -Wno-unused-label
CFLAGS_OPT=-O0 -g
CFLAGS_INCLUDE=-I/usr/local/include -I./data/c -I./data/c/libcoro

EXTRA_SOURCES=data/c/env.c data/c/funcobject.c data/c/genobject.c data/c/libcoro/coro.c
LIBS=-pthread

py31:
	gcc ${CFLAGS} ${CFLAGS_WARN} ${CFLAGS_OPT} ${CFLAGS_INCLUDE} -I/usr/include/python3.1 -o test-prog test.c ${EXTRA_SOURCES} -lpython3.1 ${LIBS} 

py33:
	gcc ${CFLAGS} ${CFLAGS_WARN} ${CFLAGS_OPT} ${CFLAGS_INCLUDE} -I/usr/local/include/python3.3dmu -o test-prog test.c ${EXTRA_SOURCES} -lpython3.3dmu ${LIBS} 

