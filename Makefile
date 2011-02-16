all:
	gcc -Wall -O0 -g -I/usr/include/python3.1 -o test-prog test.c -lpython3.1
