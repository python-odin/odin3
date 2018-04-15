from typing import TypeVar, Union, Sequence, Iterable

T = TypeVar('T')


def chunk(iterable: Iterable[T], n: int) -> Iterable[Iterable[T]]:
    """
    Return iterable of n items from an iterable.

    :param iterable: Iterable of items
    :param n: Size of iterable chunks to return.
    :return: Iterable chunk of input iterable

    """
    iterator = iter(iterable)
    cont = True

    def inner():
        nonlocal cont
        for _ in range(n):
            try:
                yield next(iterator)
            except StopIteration:
                cont = False

    while cont:
        yield inner()


def force_tuple(value: Union[T, Sequence[T]]) -> Sequence[T]:
    """
    Forces a value to be a tuple.

    Either by converting into a tuple (if is a list) or changing value to be a tuple.

    """
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return value,
