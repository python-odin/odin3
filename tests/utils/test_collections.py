import pytest

from odin.utils import collections


class TestForceTuple:
    """
    Tests for odin.utils.force_tuple
    """

    @pytest.mark.parametrize(('value', 'expected'), (
            (None, ()),
            ('', ('',)),
            (0, (0,)),
            (False, (False,)),
            (True, (True,)),
            (123, (123,)),
            ('Foo', ('Foo',)),
            (['Foo', 'bar'], ('Foo', 'bar')),
            (('Foo', 'bar'), ('Foo', 'bar')),
            (['Foo', 123, 'bar', 'eek'], ('Foo', 123, 'bar', 'eek')),
    ))
    def test_values(self, value, expected):
        assert collections.force_tuple(value) == expected


class TestChunk:
    """
    Tests for odin.utils.chunk
    """

    @pytest.mark.parametrize(('value', 'size', 'expected'), (
        ("This is a block of text split by 4", 4, [
            ['T', 'h', 'i', 's'],
            [' ', 'i', 's', ' '],
            ['a', ' ', 'b', 'l'],
            ['o', 'c', 'k', ' '],
            ['o', 'f', ' ', 't'],
            ['e', 'x', 't', ' '],
            ['s', 'p', 'l', 'i'],
            ['t', ' ', 'b', 'y'],
            [' ', '4']
        ]),
    ))
    def test_small_values(self, value, size, expected):
        """Small scale test (eg small iterable that can be easily verified)"""
        assert [list(c) for c in collections.chunk(value, size)] == expected
