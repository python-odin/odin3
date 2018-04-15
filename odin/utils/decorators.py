import functools

from typing import Callable, TypeVar

T = TypeVar('T')


class Lazy:
    """
    Property descriptor that performs lazy evaluation and caches the result.

    Based off Bottles cached_property.
    """
    @staticmethod
    def invalidate(instance: object, *names: str) -> None:
        """
        Invalidate a cached property
        """
        for name in names:
            if name in instance.__dict__:
                del instance.__dict__[name]

    def __init__(self, get: Callable[[object], T]):
        self._get = get
        functools.wraps(self._get)(self)

    def __get__(self, instance: object, owner: type(object)) -> T:
        if instance is None:
            return self
        value = instance.__dict__[self.__name__] = self._get(instance)
        return value


lazy_property = Lazy
