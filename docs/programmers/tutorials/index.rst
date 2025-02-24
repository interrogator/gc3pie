.. Hey Emacs, this is -*- rst -*-

   This file follows reStructuredText markup syntax; see
   http://docutils.sf.net/rst.html for more information.

.. include:: ../../global.inc



================================
  GC3Pie programming tutorials
================================


Slides on specific topics
-------------------------

This is a list of tutorials made for the `GC3Pie 2012 Training event`_
that has been held in Zurich on 1st and 2nd  of October 2012. The
slides and tutorials are an introduction to the GC3Pie python
package.


`Introduction to GC3Pie <http://gc3pie.googlecode.com/svn/trunk/gc3pie/docs/programmers/tutorials/part01.pdf>`_

    Introduction to the software: what is GC3Pie, what is it for, and
    an overview of its features for writing high-throughput computing
    scripts.

`Basic GC3Pie programming <http://gc3pie.googlecode.com/svn/trunk/gc3pie/docs/programmers/tutorials/part03.pdf>`_

    The `Application` class, the smallest building block of
    GC3Pie. Introduction to the concept of Job, states of an
    application and to the `Core` class.

`Application requirements <http://gc3pie.googlecode.com/svn/trunk/gc3pie/docs/programmers/tutorials/part04.pdf>`_

    How to define extra requirements for an application, such as the
    minimum amount of memory it will use, the number of cores needed
    or the architecture of the CPUs.

`Managing applications: the SessionBasedScript class <http://gc3pie.googlecode.com/svn/trunk/gc3pie/docs/programmers/tutorials/part05.pdf>`_

    Introduction to the highest-level interface to build applications
    with GC3Pie, the `SessionBasedScript`. Information on how to
    create simple scripts that take care of the execution of your
    applications, from submission to getting back the final results.

`The GC3Utils commands <http://gc3pie.googlecode.com/svn/trunk/gc3pie/docs/programmers/tutorials/part06.pdf>`_

    Low-level tools to aid debugging the scripts.

`Introduction to Workflows with GC3Pie <http://gc3pie.googlecode.com/svn/trunk/gc3pie/docs/programmers/tutorials/part08.pdf>`_

    Using a practical example (the :ref:`warholize tutorial`) we show
    how workflows are implemented with GC3Pie. The following slides
    will cover in more details the single steps needed to produce a
    complex workflow.

`ParallelTaskCollection <http://gc3pie.googlecode.com/svn/trunk/gc3pie/docs/programmers/tutorials/part09.pdf>`_

    Description of the `ParallelTaskCollection` class, used to run
    tasks in parallel.

`StagedTaskCollection <http://gc3pie.googlecode.com/svn/trunk/gc3pie/docs/programmers/tutorials/part10.pdf>`_

    Description of the `StagedTaskCollection` class, used to run a
    sequence of a fixed number of jobs.

`SequentialTaskCollection <http://gc3pie.googlecode.com/svn/trunk/gc3pie/docs/programmers/tutorials/part11.pdf>`_

    Description of the `SequentialTaskCollection` class, used to run a
    sequence of jobs that can be altered during runtime.


Example scripts
---------------

`gdemo_simple.py`_

    Simplest script you can create. It only uses `Application` and
    `Engine` classes to create an application, submit it, check its
    status and retrieve its output.

`grun.py`_

    a `SessionBasedScript` that executes its argument as command. It
    can also run it multiple times by wrapping it in a
    ParallelTaskCollection or a SequentialTaskCollection, depending on
    a command line option. Useful for testing a configured resource.

`gdemo_session.py`_

    a simple `SessionBasedScript` that sums two values by customizing
    a `SequentialTaskCollection`.

`warholize.py`_

    an enhanched version of the `warholize` script proposed in the
    :ref:`Warholize Tutorial`

.. _`gdemo_simple.py`: http://gc3pie.googlecode.com/svn/trunk/gc3pie/examples/gdemo_simple.py
.. _`gdemo_session.py`: http://gc3pie.googlecode.com/svn/trunk/gc3pie/examples/gdemo_session.py
.. _`grun.py`: http://gc3pie.googlecode.com/svn/trunk/gc3pie/examples/grun.py
.. _`warholize.py`: http://gc3pie.googlecode.com/svn/trunk/gc3pie/examples/warholize.py



.. _`Warholize Tutorial`:

Warholize Tutorial
------------------

In this tutorial we will show you how to use GC3Pie libraries in order
to build a command line script which will run a complex workflow with
both parallel and sequential tasks.

The tutorial itself contains the complete source code of the
application (cfr. `Literate Programming`_ on Wikipedia), so that you
will be able to test/modify it and produce a working ``warholize.py``
script by downloading the ``pylit.py``:file: script from the `PyLit
Homepage`_ and running the following command on the
``gc3pie/docs/programmers/tutorials/warholize/warholize.rst`` file,
from within the SVN tree of GC3Pie::

  $ ./pylit warholize.rst warholize.py


.. toctree::

  warholize/warholize

.. _`GC3Pie 2012 Training event`: https://ocikbapps.uzh.ch/gc3wiki/teaching/gc3pie2012/

.. _`Literate Programming`: http://en.wikipedia.org/wiki/Literate_programming

.. _`PyLit Homepage`: https://github.com/gmilde/PyLit
