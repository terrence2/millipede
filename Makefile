all:
	gcc -Wall -O0 -I/usr/include/python3.1 -o test-prog test.c -lpython3.1
