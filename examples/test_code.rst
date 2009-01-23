Testing code blocks with CSS:

.. style::
   :literal.font_size: 16

.. code:: css

    @import url(../styles/styles.css);
    /* Main Styles for HTML Elements */
    HTML, BODY
    {
        padding: 0;
        font-family: Arial, Verdana, Geneva,
            "Bitstream Vera Sans", Helvetica, sans-serif;
        font-size: 103%;
        background-color: #FFF;
    }

and Python:

.. code::

    def code_block_with_no_language(defined):
       ''' Will hopefully come out using Python highlighting
       '''
       return maybe

and C:

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


and C with no idenfication (the "!" is an error):

.. code::


    if (!PyArg_ParseTuple(args, "si:string_peek", &pstr, &index)) {
        return NULL;
    }

fin

