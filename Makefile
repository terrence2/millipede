all:
	#gcc -Wall -O0 -g -I/usr/include/python3.1 -o test-prog test.c data/c/env.c -lpython3.1
	gcc -Wall -O0 -g -I/usr/local/include/python3.3dmu -o test-prog test.c data/c/env.c data/c/melanofuncobject.c -lpython3.3dmu

	
