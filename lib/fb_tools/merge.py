#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@summary: Module providing functions for merging dicts an arrays.

@author: Frank Brehm
@contact: frank.brehm@pixelpark.com
"""

import itertools

__version__ = '2.0.1'


# =============================================================================
class ZipExhausted(Exception):
    """An exception, which is raised, when the longest iterable is exhausted."""

    pass


# =============================================================================
def izip_longest(*args, **kwds):
    """Make an iterator that aggregates elements from each of the iterables.

    Function izip_longest() does not exists anymore in Python3 itertools.
    Taken from https://docs.python.org/2/library/itertools.html#itertools.izip_longest
    """
    # izip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-

    fillvalue = kwds.get('fillvalue')
    counter = [len(args) - 1]

    # ------------------
    def sentinel():
        if not counter[0]:
            raise ZipExhausted
        counter[0] -= 1
        yield fillvalue

    # ------------------
    fillers = itertools.repeat(fillvalue)
    iterators = [itertools.chain(it, sentinel(), fillers) for it in args]
    try:
        while iterators:
            yield tuple(map(next, iterators))
    except ZipExhausted:
        pass


# =============================================================================
def merge_structure(a, b):
    """Merge two arbitrary data structures.

    Taken from https://gist.github.com/saurabh-hirani/6f3f5d119076df70e0da
    """
    if isinstance(a, dict) and isinstance(b, dict):
        d = dict(a)
        d.update({k: merge_structure(a.get(k, None), b[k]) for k in b})
        return d

    if isinstance(a, list) and isinstance(b, list):
        is_a_nested = any(x for x in a if isinstance(x, list) or isinstance(x, dict))
        is_b_nested = any(x for x in b if isinstance(x, list) or isinstance(x, dict))
        if is_a_nested or is_b_nested:
            return [merge_structure(x, y) for x, y in izip_longest(a, b)]
        else:
            return a + b

    return a if b is None else b


# =============================================================================

if __name__ == "__main__":

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
