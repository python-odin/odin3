from typing import Callable


class lazy_property:  # noqa - Made to match the property builtin
    """
    The bottle cached property, requires a alternate name so as not to
    clash with existing cached_property behaviour
    """
    def __init__(self, func: Callable) -> None:
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
        self.__doc__ = func.__module__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance.__dict__[self.func.__name__] = self.func(instance)
        return value
