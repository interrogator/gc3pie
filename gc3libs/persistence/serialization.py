#! /usr/bin/env python
#
"""
Generic object serialization (using Python's *pickle*/*cPickle* modules).

See the documentation for Python's standard `*pickle* and *cPickle*
modules`__ for more details.

.. __: http://docs.python.org/library/pickle.html

"""
# Copyright (C) 2011-2012, 2018, 2019  University of Zurich. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import, print_function, unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import object

import pickle

from gc3libs.persistence.store import Persistable


__docformat__ = 'reStructuredText'


DEFAULT_PROTOCOL = pickle.HIGHEST_PROTOCOL


def make_pickler(driver, stream, root, protocol=pickle.HIGHEST_PROTOCOL):
    return _PicklerWithPersistentID(driver, root, stream, protocol=protocol)


def make_unpickler(driver, stream):
    return _UnpicklerWithPersistentID(driver, stream)


class _PicklerWithPersistentID(pickle.Pickler):

    """Used internally to provide `persistent_id` support to *cPickle*.

    This class is needed because:

    * we want to save each `Persistable`:class: object as a separate record,
    * we want to use the *cPickle* module for performance reasons.

    Check the `documentation of Python's *pickle* module`__ for
    details on `persistent_id` support:

    .. __: http://goo.gl/CCknrT

    """

    def __init__(self, driver, root, stream, **kwargs):
        self._root = root
        self._driver = driver
        self._stream = stream
        pickle.Pickler.__init__(self, stream, **kwargs)

    def persistent_id(self, obj):
        if obj is self._root:
            return None
        elif isinstance(obj, Persistable):
            if (not hasattr(obj, 'persistent_id')
                or getattr(obj, 'changed', True)):
                self._driver.save(obj)
            return obj.persistent_id


class _UnpicklerWithPersistentID(pickle.Unpickler):

    """Used internally to provide `persistent_id` support to *cPickle*.

    This class is needed because:

    * we want to save each `Persistable`:class: object as a separate record,
    * we want to use the *cPickle* module for performance reasons.

    Check the `documentation of Python's *pickle* module`__ for
    details on the differences between *pickle* and *cPickle* modules.

    .. __: http://goo.gl/CCknrT

    """

    def __init__(self, driver, *args, **kwargs):
        self._driver = driver
        pickle.Unpickler.__init__(self, *args, **kwargs)

    def persistent_load(self, id_):
        return self._driver.load(id_)
