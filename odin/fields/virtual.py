import abc

from typing import Generic, Any, TypeVar, Callable

from ..utils.collections import force_tuple
from .base import BaseField, T


class VirtualField(Generic[T], BaseField[T], metaclass=abc.ABCMeta):
    """
    Common base value for virtual fields. A virtual fields is treated like any
    other field during encoding/decoding (provided it can be written to).

    Virtual fields implement the descriptor protocol.

    :param data_type_name: A name for the data type this field returns (used
        for generating documentation)

    :param is_attribute: Flag for codecs that support attributes on nodes
        eg XML to indicate this field should be treated as an attribute.

    :param key: Flag to make this value as a resources unique key field. This
        flag is an indicator only and does not affect processing by Odin. It
        is used by *OdinWeb* to identify the primary key.

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
    data_type_name = None

    def __init__(self, data_type_name: str=None, **options):
        super().__init__(**options)

        self.data_type_name = data_type_name

        self._container = None

    @abc.abstractmethod
    def __get__(self, instance, owner):
        """
        Get a calculated value.
        """

    def __set__(self, instance, value):
        raise AttributeError("Read only")

    def contribute_to_class(self, cls, attname: str) -> None:
        self.set_attributes_from_name(attname)
        self._container = cls
        getmeta(cls).add_virtual_field(self)
        setattr(cls, attname, self)


CT = TypeVar('CT')


class ConstantField(VirtualField[CT]):
    """
    A field that provides a constant value.
    """
    def __init__(self, value: CT, **options):
        super().__init__(**options)
        self.value = value

    def __get__(self, instance, owner) -> CT:
        return self.value


class CalculatedField(VirtualField[CT]):
    """
    A field whose value is calculated by an expression.

    The expression should accept a single "self" parameter that is a Resource instance.
    """
    def __init__(self, expr: Callable[[Any], CT], **options):
        super().__init__(**options)
        self.expr = expr

    def __get__(self, instance, owner) -> CT:
        return self.expr(instance)


def calculated_field(method=Callable[[Any], CT], **options):
    """
    Converts an instance method into a calculated field.
    """
    def inner(expr):
        if method.__doc__ is not None:
            help_text = method.__doc__.strip()
            if help_text:
                options.setdefault('help_text', help_text)
        return CalculatedField(expr, **options)

    return inner if method is None else inner(method)


class MultiPartField(VirtualField[str]):
    """
    A field whose value is the combination of several other fields.

    This field should be included after the field that make up the multipart value.
    """
    def __init__(self, field_names, separator='', **kwargs):
        """
        :param field_names: Name(s) of fields to make up key
        :type field_names: str | tuple[str] | list[str]
        :param separator: Separator to use between values.
        :type separator: str
        :param kwargs: Additional kwargs for VirtualField

        """
        kwargs.setdefault('data_type_name', 'String')
        super(MultiPartField, self).__init__(**kwargs)
        self.field_names = force_tuple(field_names)
        self.separator = separator
        self._fields = None

    def __get__(self, instance, owner):
        return self.generate_value(instance)

    def generate_value(self, instance) -> str:
        """
        Generate a key based on other values.
        """
        values = [f.prepare(f.value_from_object(instance)) for f in self._fields]
        return self.separator.join(str(v) for v in values)

    def on_resource_ready(self):
        # Extract reference to fields
        meta = getmeta(self._container)
        try:
            self._fields = tuple(meta.field_map[name] for name in self.field_names)
        except KeyError as ex:
            raise AttributeError("Attribute {0} not found on {1!r}".format(ex, self._container))
