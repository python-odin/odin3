import abc

from typing import IO, Any, Generic, TypeVar, Optional, Sequence

FT = TypeVar('FT')


class FieldBase(Generic[FT], metaclass=abc.ABCMeta):
    """
    Base class for all field instances.

    The base field handles the basics of naming and some common options.

    Note that the base field implements the descriptor protocol, while this
    definition is used for certain field types (virtual field for example) the
    secondary use case here is the aid static type checkers.

    :param verbose_name: A human-readable name for the field. If the verbose
        name is not provided, Odin will automatically create one using the
        field’s attribute name and converting underscores to spaces.

    :param verbose_name_plural: The plural form of the `verbose_name` option.
        The default is to append an *s* to the `verbose_name`.

    :param name: Name of the field as it appears in the serialised format. If
        the name is not provided, Odin will use the field's attribute name.

    :param doc_text: Used to provide field level documentation. This can be
        used when generating documentation of resources either via `Sphinx` or
        using `OdinWeb` OpenAPI tools. The option also provides useful inline
        documentation.

    """
    # Track each time an instance is created. Used to retain order.
    creation_counter = 0

    __slots__ = ('name', 'key', 'is_attribute', 'verbose_name', 'verbose_name_plural',
                 'doc_text',  '_hash', 'attname', 'container', )

    def __init__(self, name: str=None, key: bool=False, is_attribute: bool=False,
                 verbose_name: str=None, verbose_name_plural: str=None,
                 doc_text: str=None) -> None:
        self.name = name
        self.key = key
        self.is_attribute = is_attribute
        self.verbose_name = verbose_name
        self.verbose_name_plural = verbose_name_plural
        self.doc_text = doc_text

        self._hash = FieldBase.creation_counter
        FieldBase.creation_counter += 1

        # The name used to reference this field when bound
        self.attname = None  # type: str

        # Container type this field bound to.
        self.container = None  # type: object

    def __hash__(self) -> int:
        return self._hash

    def __repr__(self) -> str:
        """
        Displays the module, class and name of the field.
        """
        path = '{}.{}'.format(self.__class__.__module__, self.__class__.__name__)
        name = getattr(self, 'name', None)
        if name is not None:
            return '<{}: name={!r}>'.format(path, name)
        return '<{}>'.format(path)

    def __get__(self, instance: object, owner: type) -> FT:
        pass

    def __set__(self, instance: object, value: FT) -> None:
        pass

    def set_attributes_from_name(self, attname: str) -> None:
        """
        Generate any name attributes based on the name the field is
        provided when bound to a class.
        """
        self.attname = attname
        if not self.name:
            self.name = attname

        if self.verbose_name is None:
            self.verbose_name = self.name.replace('_', ' ')

        if self.verbose_name_plural is None and self.verbose_name:
            self.verbose_name_plural = self.verbose_name + 's'

    def prepare(self, value: Optional[FT]) -> Optional[FT]:
        """
        Prepare a value for serialisation.
        """
        return value

    def value_from_object(self, obj: object) -> Optional[FT]:
        """
        Obtain a field value from a supplied object.
        """
        return getattr(obj, self.attname)

    def value_to_object(self, obj: object, value: Optional[FT]) -> None:
        """
        Assign a field value to a supplied object.
        """
        setattr(obj, self.attname, value)

    def bind_to_object(self, cls: type, attname: str):
        """
        Similar to contribute to class but only handles binding and not
        contributing. This is used to bind to container classes which don't
        hold values (eg binding to a param in an URL path).
        """
        self.set_attributes_from_name(attname)
        self.container = cls

    def contribute_to_class(self, cls: type, attname: str):
        """
        Contribute to a class.
        """
        self.bind_to_object(cls, attname)


class ValueFieldBase(Generic[FT], FieldBase[FT], metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def has_default(self) -> bool:
        """
        A default value has been defined.
        """

    @abc.abstractmethod
    def get_default(self) -> FT:
        """
        Returns the default value for this field.
        """


class ResourceBase(metaclass=abc.ABCMeta):
    """
    Base class for resources.
    """
    @abc.abstractmethod
    def full_clean(self, exclude: Sequence[str] = None, ignore_not_provided: bool = False) -> None:
        pass


class FieldResolver(metaclass=abc.ABCMeta):
    """
    Field Resolver
    ==============

    Object that can resolve the available fields on an object.

    Field resolvers are used to verify mappings etc.

    """


class ResourceIterable:
    """
    Resource Iterable
    =================

    An iterable that yields resources.

    """
    def __init__(self, sequence):
        self.sequence = sequence

    def __iter__(self):
        yield from self.sequence


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
    def dump(self, fp: IO, obj: Any): pass

    @abc.abstractmethod
    def dumps(self, obj: Any) -> str: pass

    @abc.abstractmethod
    def load(self, fp: IO) -> Any: pass

    @abc.abstractmethod
    def loads(self, data: str) -> Any: pass


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
