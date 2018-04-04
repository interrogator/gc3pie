#! /usr/bin/env python
#
"""
Disk-backed collections, for handling a large number of items.
(I.e., potentially they would not fit into memory.)
"""

from __future__ import (absolute_import, division, print_function)

from collections import deque, MutableMapping, MutableSequence
from itertools import izip
import sys

from pylru import WriteThroughCacheManager


class XlList(MutableSequence):
    """
    A persisted list capable of handling more items than can fit in RAM.

    .. warning::

      The implementation is very naive and builds simply on top of the
      pylru_ Python module.  Performance of this code is very likely
      to be dismal, and no attempt at optimization has been done yet.

    Instances of `XlList` are created with two mandatory parameters:

    - a *store* (can be any Python object implementing a
      Mapping/dict-like interface), which will be used for saving and
      loading objects when they are not kept in memory; and

    - a *size*, i.e., the maximum number of objects that should be
      kept in memory at any given time: if the list gets larger than
      this *size*, items are removed from the memory cache and will be
      loaded again from the *store* when accessed.

    So the following code creates an empty `XlList` with maximum
    in-memory size of 100 objects (note that this example uses a
    regular Python dictionary as the *store*, which is pointless
    because the ``dict`` object keeps all data in memory and does not
    persist any portion of it -- but it makes for easy demoing the
    `XlList` interface)::

      >>> store = dict()
      >>> l = XlList(store, 100)
      >>> len(l)
      0

    Like for standard Python containers, an additional iterable can be
    passed to populate the list with items::

      >>> x = XlList(store, 100, [1,2,3])
      >>> for value in x:
      ...   print(value)
      1
      2
      3

    Finally, the optional keyword argument *key* allows controlling
    how items are saved and retrieved from the *store*.  The *key*
    function takes two arguments, *index* and *value*, and must return
    a "handle" (any Python hashable object) that will be used to save
    the object into the *store* and will be later used to retrieve it.
    In other words, the following equation must hold: ``value ==
    store[key(index, value)]``.  The default setting for *key* is to
    take the entire pair *(index, value)* as the combined key, which
    is rather pointless as the key index becomes then larger than the
    entire *store*!

    .. warning::

      The same *store* can back multiple ``XlList`` instances.
      Whether this makes sense depends on the actual use of the lists,
      on the store, and on the *key* function.  However, keep in mind
      that modification or deletion of items in a list will affect
      other items in a different list, if they map to the same backing
      key: for instance, deleting an item may make lookup operations
      in other lists sharing the same backing store fail with
      ``KeyError``.

    XlLists compare equal to normal lists or other XlLists, as long
    as all items are equal and occur in exactly the same order::

      >>> y = XlList(store, 10, x)
      >>> x == y
      True
      >>> x == [1, 2, 3]
      True
      >>> x == [1, 3, 2]
      False
      >>> x == [1, 4, 9, 16]
      False

    All normal "mutable sequence" operations like `append` and `insert`
    are supported::

      >>> x.append(4)
      >>> len(x)
      4
      >>> x == [1, 2, 3, 4]
      True

      >>> x.insert(0, 0)
      >>> x == [0, 1, 2, 3, 4]
      True
      >>> x.insert(2, 0)
      >>> x.insert(4, 0)
      >>> x == [0, 1, 0, 2, 0, 3, 4]
      True

      >>> x.count(0)
      3
      >>> x.count(1)
      1

      >>> x.pop(2)
      0
      >>> x.remove(0)
      >>> x == [1, 2, 0, 3, 4]
      True

      >>> x.extend([5, 6])
      >>> x == [1, 2, 0, 3, 4, 5, 6]
      True

      >>> x.pop()
      6
      >>> len(x)
      6
      >>> x == [1, 2, 0, 3, 4, 5]
      True

    Slice operations are supported like in basic Python `list`s::

      >>> x[2]
      0
      >>> x[2] = 'zero'
      >>> x[2]
      'zero'

      >>> del x[4:]
      >>> x == [1, 2, 'zero', 3]
      True

      >>> x[1::2] == [2, 3]
      True

      >>> x[1::2] = ['two', 'three']
      >>> x == [1, 'two', 'zero', 'three']
      True

    Note that taking a slice of an XlList results in another XlList,
    independent of the size of the slice::

      >>> type(x[0:2])
      <class 'gc3libs.xlcollections.XlList'>

    .. _shove: https://bitbucket.org/lcrees/shove/src
    """

    # if a list contains more than this number of items, the middle
    # ones are substituted by an ellipsis in string representations
    max_repr_items = 10

    def __init__(self, store, maxsize, iterable=None,
                 key=(lambda index, value: (index, value))):
        """
        XlList(store, size) -> new empty XlList with backing store

        XlList(store, size, iterable) -> new XlList initialized from iterable's items
        """
        self._cache = WriteThroughCacheManager(store, maxsize)
        self._munge = key
        self._index_to_key = []
        # initialize from given items
        if iterable:
            for item in iterable:
                self.append(item)


    def __delitem__(self, index_or_slice):
        try:
            # were we passed a slice object?
            start, stop, step = index_or_slice.indices(len(self))
            return self._del_items(start, stop, step)
        except AttributeError:
            # conversion of index to int is handled in `_del_item1`
            return self._del_item1(index_or_slice)

    def _del_item1(self, index):
        """Implement `__delitem__` on a single item index."""
        try:
            idx = int(index)
        except (ValueError, TypeError):
            raise TypeError("XlList indices must be integers")
        if idx < 0:
            idx += len(self._index_to_key)
        if not (0 <= idx < len(self._index_to_key)):
            raise IndexError("list index `{0}` out of range".format(index))
        key = self._index_to_key[idx]
        del self._cache[key]
        del self._index_to_key[index]

    def _del_items(self, start, stop, step):
        """Implement `__delitem__` on a slice. """
        top = len(self._index_to_key)
        for cur in xrange(start, top):
            if cur < stop and 0 == (cur - start) % step:
                # index in deletion range, delete it and skip to next
                key = self._index_to_key[cur]
                del self._cache[key]
        del self._index_to_key[start:stop:step]


    def __eq__(self, other):
        # shortcut
        if len(self) != len(other):
            return False
        # check equality of all items
        for index in xrange(len(self._index_to_key)):
            if self[index] != other[index]:
                return False
        # all items are ==, so are the lists
        return True


    def __getitem__(self, index_or_slice):
        try:
            # were we passed a slice object?
            start, stop, step = index_or_slice.indices(len(self))
            return self._get_items(start, stop, step)
        except AttributeError:
            # conversion of index to int is handled in `_get_item1`
            return self._get_item1(index_or_slice)

    def _get_item1(self, index):
        """Implement `__getitem__` on a single item ref."""
        try:
            idx = int(index)
        except (ValueError, TypeError):
            raise TypeError("XlList indices must be integers")
        if idx < 0:
            idx += len(self._index_to_key)
        if not (0 <= idx < len(self._index_to_key)):
            raise IndexError("list index `{0}` out of range".format(index))
        # FIXME: may raise `KeyError` -- what should we do?
        key = self._index_to_key[idx]
        return self._cache[key]

    def _get_items(self, start, stop, step):
        """Implement `__getitem__` on a slice. """
        return self.__class__(
            self._cache.store, self._cache.size(),
            (self._cache[self._index_to_key[idx]]
             for idx in xrange(start, stop, step)),
            self._munge)


    def __len__(self):
        return len(self._index_to_key)


    def __setitem__(self, index_or_slice, value):
        try:
            # were we passed a slice object?
            start, stop, step = index_or_slice.indices(len(self))
            return self._set_items(start, stop, step, value)
        except AttributeError:
            # conversion of index to int is handled in `_set_item1`
            return self._set_item1(index_or_slice, value)

    def _set_item1(self, index, value):
        """Implement `__setitem__` on a single item ref."""
        try:
            idx = int(index)
        except (ValueError, TypeError):
            raise TypeError("XlList indices must be integers")
        if idx < 0:
            idx += len(self._index_to_key)
        if not (0 <= idx < len(self._index_to_key)):
            raise IndexError("list index `{0}` out of range".format(index))
        self._set_item1_unchecked(idx, value)

    def _set_item1_unchecked(self, index, value):
        """Set a list item, performs no checks on *index*."""
        key = self._munge(index, value)
        self._index_to_key[index] = key
        self._cache[key] = value

    def _set_items(self, start, stop, step, values):
        """Implement `__setitem__` on a slice."""
        replacement_size = len(values)
        slice_size = (stop - start + 1) / step
        if step not in [+1, -1]:
            if slice_size != replacement_size:
                raise ValueError(
                    "attempt to assign sequence of size {0}"
                    " to extended slice of size {1}"
                    .format(replacement_size, slice_size))
            # now do the replacement, one element at a time
            for index, value in izip(xrange(start, stop, step), values):
                self._set_item1_unchecked(index, value)
        else:  # step is +1/-1
            delta = replacement_size - slice_size
            self._index_to_key[start:stop:step] = \
                    [None] * (delta if delta>0 else -delta)
            for offset, value in enumerate(values):
                index = ((start + offset) if step == +1
                         else (stop - offset))
                self._set_item1_unchecked(index, value)


    def __repr__(self):
        return self._to_string(conv=repr)

    def __str__(self):
        return self._to_string(conv=str)

    def _to_string(self, conv=str):
        if len(self) > self.max_repr_items:
            items = [conv(self[0]), conv(self[1]), '...', conv(self[-1])]
        else:
            items = [conv(item) for item in self]
        return ("XlList([{0}])".format(', '.join(items)))


    def append(self, value):
        key = self._munge(len(self._index_to_key), value)
        self._cache[key] = value
        self._index_to_key.append(key)


    def forget(self, index):
        key = self._index_to_key[index]
        del self._cache[key]


    def insert(self, index, value):
        assert 0 <= index < len(self._index_to_key)
        key = self._munge(index, value)
        self._index_to_key.insert(index, key)
        self._cache[key] = value
