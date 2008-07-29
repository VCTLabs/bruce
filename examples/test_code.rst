Testing a code block with some shell CSS source in it:

.. style::
   :literal.font_size: 16

.. code:: css

    @import url(../styles/styles.css);

    /* Main Styles for HTML Elements */
    HTML, BODY
    {
        margin: 0;
        padding: 0;
        font-family: Arial, Verdana, Geneva,
            "Bitstream Vera Sans", Helvetica, sans-serif;
        font-size: 103%;
        background-color: #FFF;
    }



.. code:: c

    #include "Python.h"

    static int
    internal_bisect_right(PyObject *list, PyObject *item, Py_ssize_t lo, Py_ssize_t hi)
    {
        PyObject *litem;
        Py_ssize_t mid, res;

        if (lo < 0) {
            PyErr_SetString(PyExc_ValueError, "lo must be non-negative");
            return -1;
        }

