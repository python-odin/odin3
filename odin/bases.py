import abc

from typing import IO, Any


class FieldResolver(metaclass=abc.ABCMeta):
    """
    Field Resolver
    ==============

    Object that can resolve the available fields on an object.

    Field resolvers are used to verify mappings etc.

    """


class ResourceIterable(metaclass=abc.ABCMeta):
    """
    Resource Iterable
    =================

    An iterable that yields resources.

    """


class Codec(metaclass=abc.ABCMeta):
    """
    Codec
    =====

    An object that serialises/de-serialises odin objects from an external
    data format.

    """
    mime_type = None  # type: str


class DocumentCodec(Codec, metaclass=abc.ABCMeta):
    """
    Document Codec
    ==============

    A document style codec, this is where an entire structure is loaded in a
    single shot, eg a JSON, YAML or XML document.

    """
    @abc.abstractmethod
    def dump(self, fp: IO, obj: Any):
        pass

    @abc.abstractmethod
    def dumps(self, obj: Any) -> str:
        pass

    @abc.abstractmethod
    def load(self, fp: IO) -> Any:
        pass

    @abc.abstractmethod
    def loads(self, data: str) -> Any:
        pass


class RecordCodec(ResourceIterable, Codec, metaclass=abc.ABCMeta):
    """
    Record Codec
    ============

    A record style codec, this is where a entries are yielded from a file or
    stream object, eg a CSV document.

    """


class StreamCodec(Codec, metaclass=abc.ABCMeta):
    """
    Stream Codec
    ============

    Similar to a record codec except a resources are only used to validate
    values, the codec will export tuples rather than Resources.

    """
