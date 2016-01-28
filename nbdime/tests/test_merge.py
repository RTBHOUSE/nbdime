# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six.moves import xrange as range

import copy
import pytest

from nbdime import merge
from nbdime.dformat import PATCH, INSERT, DELETE, REPLACE, ADDRANGE, SEQDELETE
from nbdime.dformat import make_op


def cut(li, *indices):
    c = copy.deepcopy(li)
    for q in reversed(sorted(indices)):
        c.pop(q)
    return c


def test_shallow_merge_lists_delete_no_conflict():
    # local removes an entry
    b = [1, 3]
    l = [ 1 ]
    r = [1, 3]
    m, lc, rc = merge(b, l, r)
    assert m == [ 1 ]
    assert lc == []
    assert rc == []

    # remote removes an entry
    b = [1, 3]
    l = [1, 3]
    r = [ 1 ]
    m, lc, rc = merge(b, l, r)
    assert m == [ 1 ]
    assert lc == []
    assert rc == []

    # both remove the same entry
    b = [1, 3, 2, 7]
    for i in range(len(b)):
        l = copy.deepcopy(b)
        r = copy.deepcopy(b)
        l.pop(i)
        r.pop(i)
        m, lc, rc = merge(b, l, r)
        e = copy.deepcopy(b)
        e.pop(i)
        assert m == e
        assert lc == []
        assert rc == []

    # both remove the same entry plus one other each
    b = [1, 3, 2, 7]
    for i in range(len(b)):
        for j in range(len(b)):
            if j == i:
                continue
            for k in range(len(b)):
                if k == i or k == j:
                    continue
                l = cut(b, i, j)
                r = cut(b, i, k)
                e = cut(b, i, j, k)
                m, lc, rc = merge(b, l, r)
                assert m == e
                assert lc == []
                assert rc == []


def test_shallow_merge_lists_insert_no_conflict():
    # local adds an entry
    b = [ 1 ]
    l = b + [ 2 ]
    r = copy.deepcopy(b)
    m, lc, rc = merge(b, l, r)
    assert m == [1, 2]
    assert lc == []
    assert rc == []

    # remote adds an entry
    b = [ 1 ]
    l = copy.deepcopy(b)
    r = b + [3]
    m, lc, rc = merge(b, l, r)
    assert m == [1, 3]
    assert lc == []
    assert rc == []

    # local and remote adds an entry each
    b = [ 1 ]
    l = [1, 2]
    r = [1, 3]
    m, lc, rc = merge(b, l, r)
    assert m == [1, 2, 3]
    assert lc == []
    assert rc == []

    # local and remote adds an equal entry plus a different entry each
    b = [1, 9]
    l = [1, 2, 7, 9]
    r = [1, 3, 7, 9]
    m, lc, rc = merge(b, l, r)
    # whether this is a good result is disputable but this is how it currently works:
    assert m == [1, 2, 7, 3, 7, 9]
    assert lc == []
    assert rc == []

    # local and remote adds entries to empty base
    b = []
    l = [1, 2, 4]
    r = [1, 3, 4]
    m, lc, rc = merge(b, l, r)
    # whether this is a good result is disputable but this is how it currently works:
    assert m == [1, 2, 4, 1, 3, 4]
    assert lc == []
    assert rc == []

    # local and remote adds the same entries interleaved within each base entry
    b = [1, 3, 5]
    l = [0, 1, 2, 3, 4, 5]
    r = copy.deepcopy(l)
    m, lc, rc = merge(b, l, r)
    # whether this is a good result is disputable but this is how it currently works:
    assert m == [0, 0, 1, 2, 2, 3, 4, 4, 5]
    assert lc == []
    assert rc == []

    # local and remote adds different entries interleaved within each base entry
    b = [2, 5, 8]
    l = [0, 2, 3, 5, 6, 8, 9]
    r = [1, 2, 4, 5, 7, 8, 10]
    m, lc, rc = merge(b, l, r)
    # whether this is a good result is disputable but this is how it currently works:
    assert m == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert lc == []
    assert rc == []


def test_deep_merge_lists_delete_no_conflict():
    # local removes an entry
    b = [[1, 3, 5], [2, 4, 6]]
    for i in range(len(b)):
        for j in range(len(b[i])):
            l = copy.deepcopy(b)
            r = copy.deepcopy(b)
            l[i].pop(j)
            m, lc, rc = merge(b, l, r)
            assert m == l
            assert lc == []
            assert rc == []

    # remote removes an entry
    b = [[1, 3, 5], [2, 4, 6]]
    for i in range(len(b)):
        for j in range(len(b[i])):
            l = copy.deepcopy(b)
            r = copy.deepcopy(b)
            r[i].pop(j)
            m, lc, rc = merge(b, l, r)
            assert m == r
            assert lc == []
            assert rc == []

    # both remove the same entry and one each
    b = [[1, 3, 5], [2, 4, 6]]
    l = [[1, 5], [2, 4]]  # deletes 3 and 6
    r = [[1, 5], [4, 6]]  # deletes 3 and 2
    m, lc, rc = merge(b, l, r)
    assert m == [[1, 5], [2, 4], [1, 5], [4, 6]]  # This is expected behaviour today: clear b, add l, add r
    #assert m == [[1, 5], [4]]  # 2,3,6 should be gone. TODO: This is the behaviour we want.
    assert lc == []
    assert rc == []


# TODO: We want this to work, requires improvements to nested list diffing.
@pytest.mark.xfail(run=False, reason="flaws in deep diffing of lists, not identifying almost equal sublists")
def test_deep_merge_lists_delete_no_conflict__currently_expected_failures():
    # both remove the same entry
    b = [[1, 3, 5], [2, 4, 6]]
    for i in range(len(b)):
        for j in range(len(b[i])):
            l = copy.deepcopy(b)
            r = copy.deepcopy(b)
            l[i].pop(j)
            r[i].pop(j)
            assert l == r
            m, lc, rc = merge(b, l, r)
            assert m == r
            assert lc == []
            assert rc == []


def test_deep_merge_lists_insert_no_conflict():

    # local adds an entry
    b = [[ 1 ]]
    l = [[1, 2]]
    r = [[ 1 ]]
    m, lc, rc = merge(b, l, r)
    assert m == [[1, 2]]
    assert lc == []
    assert rc == []

    # remote adds an entry
    b = [[ 1 ]]
    l = [[ 1 ]]
    r = [[1, 3]]
    m, lc, rc = merge(b, l, r)
    assert m == [[1, 3]]
    assert lc == []
    assert rc == []

    # local and remote adds an entry each
    b = [[ 1 ]]
    l = [[1, 2]]
    r = [[1, 3]]
    m, lc, rc = merge(b, l, r)
    assert m == [[1, 2], [1, 3]]  # This is expected behaviour today
    #assert m == [[1, 2, 3]]  # TODO: This is the behaviour we want
    assert lc == []
    assert rc == []

    # local and remote adds the same entry plus an entry each
    b = [[ 1 ]]
    l = [[1, 2, 4]]
    r = [[1, 3, 4]]
    m, lc, rc = merge(b, l, r)
    # No identification of equal insert value 4 expected from current algorithm
    assert m == [[1, 2, 4], [1, 3, 4]]  # This is expected behaviour today
    #assert m == [[1, 2, 4, 3, 4]]  # TODO: This is the behaviour we want
    assert lc == []
    assert rc == []

    # local and remote adds an entry each in a new sublist
    b = [[ 1 ]]
    l = [[ 1 ], [ 2 ], [3]]
    r = [[ 1 ], [ 2 ], [4]]
    m, lc, rc = merge(b, l, r)
    # No identification of equal inserted list [ 2 ] expected from current algorithm
    assert m == [[ 1 ], [ 2 ], [3], [ 2 ], [4]]
    assert lc == []
    assert rc == []


def test_shallow_merge_dicts_delete_no_conflict():
    # local removes an entry
    b = {"b": 1, "a": 3}
    l = {"b": 1}
    r = {"b": 1, "a": 3}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1}
    assert lc == []
    assert rc == []

    # remote removes an entry
    b = {"b": 1, "a": 3}
    l = {"b": 1, "a": 3}
    r = {"b": 1}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1}
    assert lc == []
    assert rc == []

    # both remove the same entry
    b = {"b": 1, "a": 3}
    l = {"b": 1}
    r = {"b": 1}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1}
    assert lc == []
    assert rc == []


def test_shallow_merge_dicts_insert_no_conflict():
    # local adds an entry
    b = {"b": 1}
    l = {"b": 1, "l": 2}
    r = {"b": 1}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1, "l": 2}
    assert lc == []
    assert rc == []

    # remote adds an entry
    b = {"b": 1}
    l = {"b": 1}
    r = {"b": 1, "r": 3}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1, "r": 3}
    assert lc == []
    assert rc == []

    # local and remote adds an entry each
    b = {"b": 1}
    l = {"b": 1, "l": 2}
    r = {"b": 1, "r": 3}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1, "l": 2, "r": 3}
    assert lc == []
    assert rc == []

    # local and remote adds an equal entry plus a different entry each
    b = {"b": 1}
    l = {"b": 1, "l": 2, "s": 7}
    r = {"b": 1, "r": 3, "s": 7}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1, "l": 2, "r": 3, "s": 7}
    assert lc == []
    assert rc == []


def test_deep_merge_dicts_delete_no_conflict():
    # local removes an entry
    b = {"p": {"b": 1, "a": 3}}
    l = {"p": {"b": 1}}
    r = {"p": {"b": 1, "a": 3}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1}}
    assert lc == []
    assert rc == []

    # remote removes an entry
    b = {"p": {"b": 1, "a": 3}}
    l = {"p": {"b": 1, "a": 3}}
    r = {"p": {"b": 1}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1}}
    assert lc == []
    assert rc == []

    # both remove the same entry
    b = {"p": {"b": 1, "a": 3}}
    l = {"p": {"b": 1}}
    r = {"p": {"b": 1}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1}}
    assert lc == []
    assert rc == []

    # both remove the same entry and one each
    b = {"p": {"b": 1, "a": 3, "c": 5, "d": 7}}
    l = {"p": {"b": 1, "c": 5}}
    r = {"p": {"b": 1, "d": 7}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1}}
    assert lc == []
    assert rc == []


def test_deep_merge_dicts_insert_no_conflict():
    # local adds an entry
    b = {"p": {"b": 1}}
    l = {"p": {"b": 1, "l": 2}}
    r = {"p": {"b": 1}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1, "l": 2}}
    assert lc == []
    assert rc == []

    # remote adds an entry
    b = {"p": {"b": 1}}
    l = {"p": {"b": 1}}
    r = {"p": {"b": 1, "r": 3}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1, "r": 3}}
    assert lc == []
    assert rc == []

    # local and remote adds an entry each
    b = {"p": {"b": 1}}
    l = {"p": {"b": 1, "l": 2}}
    r = {"p": {"b": 1, "r": 3}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1, "l": 2, "r": 3}}
    assert lc == []
    assert rc == []

    # local and remote adds the same entry plus an entry each
    b = {"p": {"b": 1}}
    l = {"p": {"b": 1, "s": 7, "l": 2}}
    r = {"p": {"b": 1, "s": 7, "r": 3}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1, "s": 7, "l": 2, "r": 3}}
    assert lc == []
    assert rc == []

    # local and remote adds the same entry plus an entry each in a new subdict
    b = {"p": {"b": 1}}
    l = {"p": {"b": 1}, "n": {"s": 7, "l": 2}}
    r = {"p": {"b": 1}, "n": {"s": 7, "r": 3}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1}, "n": {"s": 7, "l": 2, "r": 3}}
    assert lc == []
    assert rc == []


def test_merge_nonconflicting_nested_dicts():
    # local and remote each adds, deletes, and modifies entries inside nested structure without conflicts
    b = {"a": {}, "d": {"x": 4, "y": 5, "z": 6}, "m": {"x": 7, "y": 8, "z": 9}}
    l = {"a": {"x": 1, "y": 2}, "d": {"z": 6}, "m": {"x": 17, "y": 18, "z": 9}}
    r = {"a": {"x": 1, "z": 3}, "d": {"y": 5}, "m": {"x": 17, "y": 8, "z": 19}}
    m, lc, rc = merge(b, l, r)
    assert m == {"a": {"x": 1, "y": 2, "z": 3}, "d": {}, "m": {"x": 17, "y": 18, "z": 19}}
    assert lc == []
    assert rc == []


def test_merge_conflicting_nested_dicts():
    # local and remote each adds, deletes, and modifies entries inside nested structure with everything conflicting
    b = {"a": {"x": 1},         "d": {"x": 4, "y": 5}, "m": {"x": 7}}
    l = {"a": {"x": 2, "y": 4}, "d":         {"y": 6}, "m": {"x": 17}, "n": {"q": 9}}
    r = {"a": {"x": 3, "y": 5}, "d": {"x": 5},         "m": {"x": 27}, "n": {"q": 19}}
    m, lc, rc = merge(b, l, r)
    assert m == {"a": {}, "d": {}, "m": {}, "n": {}}
    assert lc == [make_op(PATCH, "a", [make_op(REPLACE, "x", 2), make_op(INSERT, "y", 4)]),
                  make_op(PATCH, "d", [make_op(DELETE, "x"), make_op(REPLACE, "y", 6)]),
                  make_op(PATCH, "m", [make_op(REPLACE, "x", 17)]),
                  make_op(PATCH, "n", [make_op(INSERT, "q", 9)])
                  ]
    assert rc == [make_op(PATCH, "a", [make_op(REPLACE, "x", 3), make_op(INSERT, "y", 5)]),
                  make_op(PATCH, "d", [make_op(REPLACE, "x", 5), make_op(DELETE, "y")]),
                  make_op(PATCH, "m", [make_op(REPLACE, "x", 27)]),
                  make_op(PATCH, "n", [make_op(INSERT, "q", 19)])
                  ]
