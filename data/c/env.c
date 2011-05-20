#include <Python.h>
#include <locale.h>
#include <coro.h>
#include "genobject.h"

extern int __millipede_main__(int argc, wchar_t **argv);
extern wchar_t* _Mp_char2wchar(const char* arg, size_t *size);


void __err_capture__(char *file, int lineno, int clineno, char *context,
				char *srcline, int err_start, int err_end) {
    PyObject *val, *src, *dict, *tb;
    int rv;

    // build current value
    val = PyUnicode_FromFormat("  File \"%s\", line %d (%d), in %s\n", file, lineno, clineno, context);
    if(!val)
		Py_FatalError("Failed to format captured error");
    src = PyUnicode_FromFormat("    %s\n", srcline);
    if(!src)
		Py_FatalError("Failed to format captured source line");

    // get the thread state dict
    dict = PyThreadState_GET()->dict;
    if(!dict) {
	    dict = PyThreadState_GET()->dict = PyDict_New();
	    if(!dict)
			Py_FatalError("Could not create thread state dict");
    }

    // get the traceback list
    tb = PyDict_GetItemString(dict, "__millipede_traceback__");
    if(!tb) {
		tb = PyList_New(0);
		if(!tb)
			Py_FatalError("Could not create traceback list");
		Py_INCREF(tb);
		rv = PyDict_SetItemString(dict, "__millipede_traceback__", tb);
		if(rv == -1)
			Py_FatalError("Failed to insert traceback into thread state");
    }

    // add the value to the traceback list
    rv = PyList_Append(tb, src);
    if(rv == -1)
		Py_FatalError("Failed to append to traceback");
    rv = PyList_Append(tb, val);
    if(rv == -1)
		Py_FatalError("Failed to append to traceback");
}


void __err_show_traceback__() {
	PyObject *dict, *tb, *val;
	Py_ssize_t i, cnt;

	fprintf(stderr, "Traceback (most recent call last):\n");

	dict = PyThreadState_GET()->dict;
	if(!dict)
		return;
	tb = PyDict_GetItemString(dict, "__millipede_traceback__");
	if(!tb)
		return;

	cnt = PyList_Size(tb);
	for(i = cnt - 1; i > -1; i--) {
		val = PyList_GetItem(tb, i);
		if(!val) {
			Py_FatalError("Failed to get_item in tb list when printing traceback");
		}
		if(!PyUnicode_Check(val)) {
			Py_FatalError("Non-Unicode object in traceback");
		}
		PyObject_Print(val, stderr, Py_PRINT_RAW);
	}
}


void __err_clear__() {
    int rv;
    PyObject *dict, *tb;

    // reset the error indicator
    PyErr_Clear();

    dict = PyThreadState_GET()->dict;
    if(!dict)
		return;

    // grab the traceback list
    tb = PyDict_GetItemString(dict, "__millipede_traceback__");
    if(!tb)
		return;

    // clear the traceback list
    rv = PyList_SetSlice(tb, 0, PyList_Size(tb), NULL);
    if(rv)
		Py_FatalError("Error clearing traceback list when clearing error.");
}


void
__init__(int argc, wchar_t **argv) {
    Py_Initialize();
    PySys_SetArgv(argc, argv);
    MpGenerator_Initialize();
}

/*
This is borrowed directly from python's sources.
*/

/* Decode a byte string from the locale encoding with the
   surrogateescape error handler (undecodable bytes are decoded as characters
   in range U+DC80..U+DC {FF). If a byte sequence can be decoded as a surrogate
   character, escape the bytes using the surrogateescape error handler instead
   of decoding them.

   Use _Py_wchar2char() to encode the character string back to a byte string.

   Return a pointer to a newly allocated wide character string (use
   PyMem_Free() to free the memory) and write the number of written wide
   characters excluding the null character into *size if size is not NULL, or
   NULL on error (conversion or memory allocation error).

   Conversion errors should never happen, unless there is a bug in the C
   library. */
wchar_t*
_Mp_char2wchar(const char* arg, size_t *size)
{
    wchar_t *res;
#ifdef HAVE_BROKEN_MBSTOWCS
    /* Some platforms have a broken implementation of
     * mbstowcs which does not count the characters that
     * would result from conversion.  Use an upper bound.
     */
    size_t argsize = strlen(arg);
#else
    size_t argsize = mbstowcs(NULL, arg, 0);
#endif
    size_t count;
    unsigned char *in;
    wchar_t *out;
#ifdef HAVE_MBRTOWC
    mbstate_t mbs;
#endif
    if (argsize != (size_t)-1) {
        res = (wchar_t *)PyMem_Malloc((argsize+1)*sizeof(wchar_t));
        if (!res)
            goto oom;
        count = mbstowcs(res, arg, argsize+1);
        if (count != (size_t)-1) {
            wchar_t *tmp;
            /* Only use the result if it contains no
               surrogate characters. */
            for (tmp = res; *tmp != 0 &&
                         (*tmp < 0xd800 || *tmp > 0xdfff); tmp++)
                ;
            if (*tmp == 0) {
                if (size != NULL)
                    *size = count;
                return res;
            }
        }
        PyMem_Free(res);
    }
    /* Conversion failed. Fall back to escaping with surrogateescape. */
#ifdef HAVE_MBRTOWC
    /* Try conversion with mbrtwoc (C99), and escape non-decodable bytes. */

    /* Overallocate; as multi-byte characters are in the argument, the
       actual output could use less memory. */
    argsize = strlen(arg) + 1;
    res = (wchar_t*)PyMem_Malloc(argsize*sizeof(wchar_t));
    if (!res)
        goto oom;
    in = (unsigned char*)arg;
    out = res;
    memset(&mbs, 0, sizeof mbs);
    while (argsize) {
        size_t converted = mbrtowc(out, (char*)in, argsize, &mbs);
        if (converted == 0)
            /* Reached end of string; null char stored. */
            break;
        if (converted == (size_t)-2) {
            /* Incomplete character. This should never happen,
               since we provide everything that we have -
               unless there is a bug in the C library, or I
               misunderstood how mbrtowc works. */
            fprintf(stderr, "unexpected mbrtowc result -2\n");
            PyMem_Free(res);
            return NULL;
        }
        if (converted == (size_t)-1) {
            /* Conversion error. Escape as UTF-8b, and start over
               in the initial shift state. */
            *out++ = 0xdc00 + *in++;
            argsize--;
            memset(&mbs, 0, sizeof mbs);
            continue;
        }
        if (*out >= 0xd800 && *out <= 0xdfff) {
            /* Surrogate character.  Escape the original
               byte sequence with surrogateescape. */
            argsize -= converted;
            while (converted--)
                *out++ = 0xdc00 + *in++;
            continue;
        }
        /* successfully converted some bytes */
        in += converted;
        argsize -= converted;
        out++;
    }
#else
    /* Cannot use C locale for escaping; manually escape as if charset
       is ASCII (i.e. escape all bytes > 128. This will still roundtrip
       correctly in the locale's charset, which must be an ASCII superset. */
    res = PyMem_Malloc((strlen(arg)+1)*sizeof(wchar_t));
    if (!res) goto oom;
    in = (unsigned char*)arg;
    out = res;
    while(*in)
        if(*in < 128)
            *out++ = *in++;
        else
            *out++ = 0xdc00 + *in++;
    *out = 0;
#endif
    if (size != NULL)
        *size = out - res;
    return res;
oom:
    fprintf(stderr, "out of memory\n");
    return NULL;
}

int main(int argc, char **argv) {
    wchar_t **argv_copy = (wchar_t **)PyMem_Malloc(sizeof(wchar_t*)*argc);
    /* We need a second copies, as Python might modify the first one. */
    wchar_t **argv_copy2 = (wchar_t **)PyMem_Malloc(sizeof(wchar_t*)*argc);
    int i, res;
    char *oldloc;
    /* 754 requires that FP exceptions run in "no stop" mode by default,
     * and until C vendors implement C99's ways to control FP exceptions,
     * Python requires non-stop mode.  Alas, some platforms enable FP
     * exceptions by default.  Here we disable them.
     */
#ifdef __FreeBSD__
    fp_except_t m;

    m = fpgetmask();
    fpsetmask(m & ~FP_X_OFL);
#endif
    if (!argv_copy || !argv_copy2) {
        fprintf(stderr, "out of memory\n");
        return 1;
    }
    oldloc = strdup(setlocale(LC_ALL, NULL));
    setlocale(LC_ALL, "");
    for (i = 0; i < argc; i++) {
#ifdef __APPLE__
        argv_copy[i] = _Py_DecodeUTF8_surrogateescape(argv[i], strlen(argv[i]));
#else
        argv_copy[i] = _Mp_char2wchar(argv[i], NULL);
#endif
        if (!argv_copy[i])
            return 1;
        argv_copy2[i] = argv_copy[i];
    }
    setlocale(LC_ALL, oldloc);
    free(oldloc);
    res = __millipede_main__(argc, argv_copy);
    for (i = 0; i < argc; i++) {
        PyMem_Free(argv_copy2[i]);
    }
    PyMem_Free(argv_copy);
    PyMem_Free(argv_copy2);
    return res;
}
