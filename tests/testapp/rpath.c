#include <Python.h>

extern int add(int a, int b);

static PyObject *
rpath_spam(PyObject *self, PyObject *args)
{
    int a, b;

    if (!PyArg_ParseTuple(args, "ii", &a, &b))
        return NULL;

    return PyLong_FromLong(add(a, b));
}


static PyMethodDef RPathMethods[] = {
    {"spam",  rpath_spam, METH_VARARGS, "Add numbers"},
    {NULL, NULL, 0, NULL}
};


#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef rpathmodule = {
   PyModuleDef_HEAD_INIT, "rpath", NULL, -1, RPathMethods
};


PyMODINIT_FUNC
PyInit_rpath(void)
{
    return PyModule_Create(&rpathmodule);
}

#else

PyMODINIT_FUNC
initrpath(void)
{
    Py_InitModule("rpath", RPathMethods);
}

#endif
