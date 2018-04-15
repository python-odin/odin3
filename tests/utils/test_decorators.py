import pytest
import typing

from odin.utils import decorators


class Example:
    def __init__(self):
        self.bool_value = True

    @decorators.Lazy
    def bool_prop(self) -> bool:
        return self.bool_value

    @decorators.Lazy
    def int_prop(self) -> int:
        pass

    @decorators.lazy_property
    def str_prop(self) -> str:
        pass


class TestLazyProperty:
    def test_usage(self):
        target = Example()

        assert 'bool_prop' not in target.__dict__
        assert target.bool_prop is True
        assert 'bool_prop' in target.__dict__

        target.bool_value = False

        assert target.bool_prop is True
        assert 'bool_prop' in target.__dict__

    def test_invalidation(self):
        target = Example()

        assert target.bool_prop is True
        assert 'bool_prop' in target.__dict__

        target.bool_value = False
        decorators.Lazy.invalidate(target, 'bool_prop')

        assert 'bool_prop' not in target.__dict__
        assert target.bool_prop is False
        assert 'bool_prop' in target.__dict__

    def test_del_invalidation(self):
        target = Example()

        assert target.bool_prop is True
        assert 'bool_prop' in target.__dict__

        target.bool_value = False
        del target.bool_prop

        assert 'bool_prop' not in target.__dict__
        assert target.bool_prop is False
        assert 'bool_prop' in target.__dict__

    @pytest.mark.parametrize('attr, expected', (
        ('bool_prop', bool),
        ('int_prop', int),
        ('str_prop', str),
    ))
    def test_type_hinting(self, attr, expected):
        x = typing.get_type_hints(getattr(Example, attr))
        assert x['return'] == expected
