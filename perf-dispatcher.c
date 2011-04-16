/*
The python performance testing utility expects to test a python
interpreter, not a bunch of separately compiled programs.  This
simple program emulates a python interpreter by "interpeting" the
perf testing scripts.  It does this by execing the correct binary
for the given script, getting out of the way as fast as possible.
*/
#include <assert.h>
#include <errno.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

char * join(char *dir, char *name) {
	char *dst;
	size_t len = strlen(dir) + 1 + strlen(name) + 1;
	dst = malloc(len);
	dst[len - 1] = '\0';
	strcat(dst, dir);
	strcat(dst, "/");
	strcat(dst, name);
	return dst;
}

int dispatch(char *name, char *dir, char **argv) {
	int rv = 1;
	char *tmp = NULL;

	if(0 == strcmp(name, "performance/bm_float.py"))
		tmp = join(dir, "build/bm_float");
	else if(0 == strcmp(name, "performance/bm_pidigits.py"))
		tmp = join(dir, "build/bm_pidigits");
	else {
		fprintf(stderr, "Unknown test named: %s\n", name);
		return 2;
	}

	assert(tmp != NULL);
	argv[0] = tmp;
	rv = execv(tmp, (char *const *)argv);
	free(tmp);
	if(rv)
		fprintf(stderr, "Exec Error: %s\n", strerror(errno));

	return rv;
}

char **build_second_args(int argc, char **argv) {
	char **out = NULL;
	int cnt = -2 + 1 + argc + 1;
	int i;
	assert(cnt > 0);

	out = (char **)calloc(cnt, sizeof(char*));
	for(i = 2; i < argc; ++i) {
		out[i - 1] = argv[i];
	}
	out[cnt - 1] = NULL;
	return out;
}

int main(int argc, char **argv) {
	char *basedir;
	char **args;
	int rv;
	if(argc < 2) {
		fprintf(stderr, "Too few args\n");
		return 1;
	}
	basedir = dirname(argv[0]);
	args = build_second_args(argc, argv);
	rv = dispatch(argv[1], basedir, args);
	free(basedir);
	free((void *)args);
	return rv;
}
