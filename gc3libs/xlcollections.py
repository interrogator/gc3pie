#! /usr/bin/env python
#
"""
Disk-backed collections, for handling a large number of items.
(I.e., potentially they would not fit into memory.)
"""

from __future__ import print_function

from collections import MutableSequence
from itertools import izip
import sys

import shove


# needed to work around Shove's issue 3
def _identity(x):
    return x


class XlList(MutableSequence):
    """
    A persisted list capable of handling more items than can fit in RAM.

    .. warning::

      The implementation is very naive and builds simply on top of the
      shove_ Python module.  Performance of this code is very likely
      to be dismal, and no attempt at optimization has been done yet.

    Instances of `XlList` are created just like "normal" lists, by
    passing any iterable to the `XlList` constructor::

      >>> x = XlList([1,2,3])

    Of course, the iterable can be another `XlList` instance too::

      >>> y = XlList(x)
      >>> for value in y:
      ...   print(value)
      1
      2
      3

    By default, all data is still kept in memory; additional
    parameters should be passed to the constructor to actually store
    the data on disk and configure the RAM cache size and eviction
    policy.

    ::

      >>> from tempfile import mkdtemp
      >>> tmpdir = mkdtemp(prefix='xllist.', suffix='.tmp.d')
      >>> x = XlList([1,2,3], store=('file://'+tmpdir))

    An additional method `sync` is provided to force flushing cached
    data to the persistent storage::

      >>> x.sync()

    When a list has been persisted, it retrieves contents from the
    disk-based storage upon initialization::

      >>> del x
      >>> x = XlList(store=('file://'+tmpdir))
      >>> len(x)
      3

    XlLists compare equal to normal lists or other XlLists, as long
    as all items are equal and occur in exactly the same order::

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

    def __init__(self, iterable=None, **kwargs):
        """
        XlList() -> new empty XlList

        XlList(iterable) -> new XlList initialized from iterable's items

        Any keyword arguments are passed unchanged to the
        `shove.Shove`:class: constructor (which see).
        """
        self._data = shove.Shove(**kwargs)
        self._top_index = len(self._data)
        # Shove's `FileStore` forces all keys to be strings;
        # work around that by using an additional "key formatting" layer
        store_uri = kwargs.get('store', 'none')
        if store_uri.startswith('file:'):
            self._to_key = str
        else:
            self._to_key = _identity
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
            if idx < 0:
                idx += self._top_index
            del self._data[self._to_key(idx)]
        except (ValueError, TypeError):
            raise TypeError("XlList indices must be integers")
        except KeyError:
            raise IndexError("list index `{0}` out of range".format(index))
        for idx in xrange(idx, self._top_index-1):
            self[idx] = self[idx+1]
        self._top_index -= 1

    def _del_items(self, start, stop, step):
        """Implement `__delitem__` on a slice. """
        dst = start
        top = len(self)
        for cur in xrange(start, top):
            if cur < stop and 0 == (cur - start) % step:
                # index in deletion range, delete it and skip to next
                del self._data[str(cur)]
            else:
                # renumber
                self._data[str(dst)] = self._data[str(cur)]
                dst += 1
        self._top_index -= (stop - start) / step

    def __eq__(self, other):
        # shortcut
        if len(self) != len(other):
            return False
        # check equality of all items
        for index in xrange(self._top_index):
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
            if idx < 0:
                idx += self._top_index
            return self._data[self._to_key(idx)]
        except (ValueError, TypeError):
            raise TypeError("XlList indices must be integers")
        except KeyError as err:

            raise IndexError("list index `{0}` out of range".format(index))

    def _get_items(self, start, stop, step):
        """Implement `__getitem__` on a slice. """
        return self.__class__(self._data[self._to_key(idx)] for idx in xrange(start, stop, step))


    def __len__(self):
        return self._top_index


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
            if idx < 0:
                idx += self._top_index
            self._data[self._to_key(idx)] = value
        except (ValueError, TypeError):
            import traceback as tb; tb.print_exc(file=sys.stderr)
            raise TypeError("XlList indices must be integers")
        except KeyError:
            raise IndexError("list index `{0}` out of range".format(index))

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
        else:
            # step is +1/-1
            delta = slice_size - replacement_size
            self._top_index = self._top_index + delta
            if delta > 0:
                # need to make room, from top index downwards
                for index in xrange(self._top_index-1, stop+delta-1, -1):
                    self._data[self._to_key(index)] = self._data[self._to_key(index-delta)]
            elif delta < 0:
                # shrinking list, from bottom index upwards
                for index in xrange(stop+delta, self._top_index):
                    self._data[self._to_key(index)] = self._data[self._to_key(index-delta)]
        # now do the replacement
        for index, value in izip(xrange(start, stop, step), values):
            self._data[self._to_key(index)] = value



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
        self[self._top_index] = value
        self._top_index += 1


    def insert(self, index, value):
        # make room for new index
        for idx in xrange(self._top_index-1, index-1, -1):
            self[idx+1] = self[idx]
        self[index] = value
        self._top_index += 1


    def sync(self):
        self._data.sync()
