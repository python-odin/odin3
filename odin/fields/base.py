from typing import Any, TypeVar, Generic

T = TypeVar('T')


class BaseField(Generic[T]):
    """
    This is the base class for all odin fields. The base field provides
    primarily provides naming operations for other field types.

    :param verbose_name: A human-readable name for the field. If the verbose name
        is not provided, Odin will automatically create one using the field’s
        attribute name and converting underscores to spaces.

    :param verbose_name_plural: The plural form of the `verbose_name` option. The
        default is to append an *s* to the `verbose_name`.

    :param name: Name of the field as it appears in the serialised format. If the
        name is not provided, Odin will use the field's attribute name.

    :param doc_text: Used to provide field level documentation. This can be used
        when generating documentation of resources either via `Sphinx` or using
        `OdinWeb` OpenAPI tools.

    The option also provides useful inline documentation.

    """
    # These track each time an instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, verbose_name: str=None, verbose_name_plural: str=None,
                 name: str=None, doc_text: str='') -> None:
        self.verbose_name, self.verbose_name_plural = verbose_name, verbose_name_plural
        self.name = name
        self.doc_text = doc_text

        self.creation_counter = BaseField.creation_counter
        BaseField.creation_counter += 1

        self.attname = None

    def __hash__(self) -> int:
        return self.creation_counter

    def __repr__(self) -> str:
        """
        Displays the module, class and name of the field.
        """
        path = '{}.{}'.format(self.__class__.__module__, self.__class__.__name__)
        name = getattr(self, 'name', None)
        if name is not None:
            return '<{}: name={!r}>'.format(path, name)
        return '<{}>'.format(path)

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

    def prepare(self, value: T) -> T:
        """
        Prepare a value for serialisation.
        """
        return value

    def as_string(self, value: T) -> str:
        """
        Generate a string representation of a field value.
        """
        if value is not None:
            return str(value)

    def value_from_object(self, obj: Any) -> Any:
        """
        Obtain a field value from a supplied object.
        """
        return getattr(obj, self.attname)
