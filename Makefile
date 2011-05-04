GCC=gcc
CFLAGS=-DCORO_UCONTEXT
CFLAGS_WARN=-Wall -Wno-unused-label -Wtrigraphs
CFLAGS_OPT=-O0 -g
CFLAGS_INCLUDE=-I/usr/local/include -I./data/c -I./data/c/libcoro
POST33=du

EXTRA_SOURCES=data/c/env.c data/c/closure.c data/c/funcobject.c data/c/genobject.c data/c/libcoro/coro.c
LIBS=-pthread

py31:
	gcc ${CFLAGS} ${CFLAGS_WARN} ${CFLAGS_OPT} ${CFLAGS_INCLUDE} -I/usr/include/python3.1 -o test-prog test.c ${EXTRA_SOURCES} -lpython3.1 ${LIBS} 

self:
	gcc ${CFLAGS} ${CFLAGS_WARN} ${CFLAGS_OPT} ${CFLAGS_INCLUDE} -I/usr/include/python3.1 -o millipede-x-3.1 melano.c ${EXTRA_SOURCES} -lpython3.1 ${LIBS} 


py33:
	gcc ${CFLAGS} ${CFLAGS_WARN} ${CFLAGS_OPT} ${CFLAGS_INCLUDE} -I/usr/local/include/python3.3${POST33} -o test-prog test.c ${EXTRA_SOURCES} -lpython3.3${POST33} ${LIBS} 

self33:
	gcc ${CFLAGS} ${CFLAGS_WARN} ${CFLAGS_OPT} ${CFLAGS_INCLUDE} -I/usr/local/include/python3.3${POST33} -o millipede-x-3.3 melano.c ${EXTRA_SOURCES} -lpython3.3${POST33} ${LIBS} 

perf-dispatcher: perf-dispatcher.c
	gcc -Wall -O0 -ggdb -o perf-dispatcher perf-dispatcher.c

