all:
	gcc -Wall -O0 -g -I/usr/local/include/python3.3dmu -o test-prog test.c data/c/env.c data/c/melanofuncobject.c data/c/melanogenobject.c -lpython3.3dmu -lpcl

	
