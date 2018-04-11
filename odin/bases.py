import abc

from typing import TextIO, Any


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


class DocumentCodec(metaclass=abc.ABCMeta, Codec):
    """
    Document Codec
    ==============

    A document style codec, this is where an entire structure is loaded in a
    single shot, eg a JSON, YAML or XML document.

    """
    @abc.abstractmethod
    def dump(self, fp: TextIO, obj: Any):
        pass

    @abc.abstractmethod
    def dumps(self, obj: Any) -> str:
        pass

    @abc.abstractmethod
    def load(self, fp: TextIO) -> Any:
        pass

    @abc.abstractmethod
    def loads(self, fp: TextIO) -> Any:
        pass


class RecordCodec(metaclass=abc.ABCMeta, ResourceIterable, Codec):
    """
    Record Codec
    ============

    A record style codec, this is where a entries are yielded from a file or
    stream object, eg a CSV document.

    """


class StreamCodec(metaclass=abc.ABCMeta, Codec):
    """
    Stream Codec
    ============

    Similar to a record codec except a resources are only used to validate
    values, the codec will export tuples rather than Resources.

    """
