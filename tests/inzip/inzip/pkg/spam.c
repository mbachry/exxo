#include <Python.h>

static PyObject *
spam_spam(PyObject *self, PyObject *args)
{
    int a, b;

    if (!PyArg_ParseTuple(args, "ii", &a, &b))
        return NULL;

    return PyLong_FromLong(a + b);
}


static PyMethodDef SpamMethods[] = {
    {"spam",  spam_spam, METH_VARARGS, "Add numbers"},
    {NULL, NULL, 0, NULL}
};


#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef spammodule = {
   PyModuleDef_HEAD_INIT, "spam", NULL, -1, SpamMethods
};


PyMODINIT_FUNC
PyInit_spam(void)
{
    return PyModule_Create(&spammodule);
}

#else

PyMODINIT_FUNC
initspam(void)
{
    Py_InitModule("spam", SpamMethods);
}

#endif
