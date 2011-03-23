all:
	gcc -Wall -O0 -g -I/usr/local/include/python3.3dmu -I/usr/local/include -I./data/c -I./data/c/libcoro -DCORO_UCONTEXT -o test-prog test.c data/c/env.c data/c/funcobject.c data/c/genobject.c data/c/libcoro/coro.c -lpython3.3dmu -pthread


