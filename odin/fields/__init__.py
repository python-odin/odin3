"""
Fields that are supplied with Odin.

These are split into three types:

#. Value - Fields that hold a single value eg ``str`` or ``int``
#. Composite - Fields that are made up of other resources eg
   ``List[MyResource]``
#. Virtual - Fields that are not assigned to a resource, these could be
   generated or constant values.

"""
import datetime
import enum
import uuid

from typing import Generic, Sequence, Any, List, Callable, Mapping

from odin.exceptions import ValidationError
from .base import BaseField, T


Validator = Callable[[Any], None]
ErrorMessages = Mapping[str, str]

EMPTY_VALUES = frozenset((None, '', [], {}, ()))


class NotProvided:
    """
    This value was not provided.
    """


class Field(Generic[T], BaseField[T]):
    """
    Common base value for value fields.

    :param null: This field can accept a null/`None` value. This argument
        defaults to `None` which, which will use the default value provided by
        an associated meta instance.

    :param default: Default value for this field, this value is applied prior
        to validation.

    :param use_default_if_not_provided: If a value is not provided when
        mapping then use the default. This defaults to `None`, which will use
        the value provided by an associated meta instance.

    :param choices: Valid constant values that can be supplied to this field.

    :param validators: A sequence of additional validation callables which
        are called during the validation phase of a clean operation.

    :param error_messages: A dictionary of error messages that can be used to
        override the builtin error messages.

    :param is_attribute: Flag for codecs that support attributes on nodes
        eg XML to indicate this field should be treated as an attribute.

    :param key: Flag to make this value as a resources unique key field. This
        flag is an indicator only and does not affect processing by Odin. It
        is used by *OdinWeb* to identify the primary key.

    """
    native_type = None  # type: type
    default_validators = []  # type: List[Validator]
    default_error_messages = {
        'invalid_choice': 'Value %r is not a valid choice.',
        'null': 'This field cannot be null.',
        'required': 'This field is required.',
    }  # type: ErrorMessages

    def __init__(self,
                 null: bool=None,
                 default: T=NotProvided,
                 use_default_if_not_provided: bool=None,
                 choices: Sequence[Any]=None,
                 validators: List[Validator]=None,
                 error_messages: Mapping[str, str]=None,
                 is_attribute: bool=False,
                 key: bool=False,
                 **options) -> None:
        super().__init__(**options)

        self.null = null
        self.default = default
        self.use_default_if_not_provided = use_default_if_not_provided
        self.choices = choices
        self.validators = self.default_validators + (validators or [])
        self.is_attribute = is_attribute
        self.key = key

        # Walk up through inheritance tree and build list of error messages
        messages = {}
        for c in reversed(self.__class__.__mro__):
            messages.update(getattr(c, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

        self._container = None

    def contribute_to_class(self, cls, attname: str) -> None:
        """
        Bind to a container type
        """
        self.set_attributes_from_name(attname)
        self._container = cls
        # Add to _container...

    def to_python(self, value: Any) -> T:
        """
        Converts an input value into the expected Python data type.

        Raise :class:`odin.exceptions.ValidationError` if data can not be
        converted.
        """
        raise NotImplementedError()

    def run_validators(self, value: T) -> None:
        """
        Run each of the validators and capture any validation failures.
        """
        if value in EMPTY_VALUES:
            return  # Don't run validators if we don't have a value

        error_types = (ValidationError,)
        errors = []
        for v in self.validators:
            try:
                v(value)
            except error_types as e:
                pass  # TODO: fetch handlers from registration.
        if errors:
            raise ValidationError(errors)

    def validate(self, value: T) -> None:
        """
        Validate a value that has been successfully converted into this fields
        native type.
        """
        if self.choices and value not in EMPTY_VALUES:
            pass

        # Check if we have a null value
        if not self.null and value is None:
            raise ValidationError(self.error_messages['null'])


class String(Field[str]):
    """

    """
    native_type = str

    def __init__(self, max_length=None, empty=None, **options):
        options.setdefault('validators')
        super().__init__(**options)


class Integer(Field[int]):
    native_type = int


class Float(Field[float]):
    native_type = float


class Boolean(Field[bool]):
    native_type = bool


class UUID(Field[uuid.UUID]):
    native_type = uuid.UUID


class Enum(Field[enum.Enum]):
    native_type = enum.Enum


StringField = String
IntegerField = Integer
FloatField = Float
BooleanField = Boolean
UUIDField = UUID
EnumField = Enum
