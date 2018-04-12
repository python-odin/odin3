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

from typing import Generic, Sequence, Any, Mapping, Optional, List as ListType, TypeVar, Type

from odin.exceptions import ValidationError
from odin.utils import datetimeutil
from odin.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator
from odin.typing import Validator, ErrorMessageDict
from .base import BaseField, T

__all__ = (
    'String', 'Integer', 'Float', 'Boolean',
    'Date', 'Time', 'NaiveTime', 'DateTime', 'NaiveDateTime',
    'TimeStamp', 'HttpDateTime',
    'UUID', 'Enum',
    'List', 'Dict',
    'StringField', 'IntegerField', 'FloatField', 'BooleanField',
    'DateField', 'TimeField', 'NaiveTimeField', 'DateTimeField', 'NaiveDateTimeField',
    'TimeStampField', 'HttpDateTimeField',
    'UUIDField', 'EnumField',
    'ListField', 'DictField',
    'NotProvided', 'Field',
)

EMPTY_VALUES = (None, '', [], {}, ())


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
    default_validators = []  # type: ListType[Validator]
    default_error_messages = {
        'invalid_choice': 'Value {!r} is not a valid choice.',
        'null': 'This field cannot be null.',
        'required': 'This field is required.',
    }  # type: ErrorMessageDict

    def __init__(self,
                 null: bool=None,
                 default: T=NotProvided,
                 use_default_if_not_provided: bool=None,
                 choices: Sequence[Any]=None,
                 validators: ListType[Validator]=None,
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

    def to_python(self, value: Any) -> Optional[T]:
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

    def clean(self, value: Any) -> T:
        """
        Convert a value to the native type and validate the incoming value.
        Validation errors from :func:`to_python` and :func:`validate` are
        propagated. This current value is return if no error is raised.
        """
        if value is NotProvided:
            value = self.get_default() if self.use_default_if_not_provided else None
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value

    @property
    def has_default(self) -> bool:
        """
        A default value has been defined.
        """
        return self.default is not NotProvided

    def get_default(self) -> T:
        """
        Returns the default value for this field.
        """
        if self.has_default:
            if callable(self.default):
                return self.default()
            return self.default


class String(Field[str]):
    """
    A string.

    A String field has two extra arguments:

    :param max_length: The maximum length (in characters) of the field.
        The ``max_length`` value is enforced by validation rules.

    :param empty: The string can be empty. This is similar to ``None`` but
        captures an empty string in additional to ``None``. The default state
        of this flag is ``False``.

    """
    native_type = str

    def __init__(self, max_length=None, empty=None, **options):
        options.setdefault('validators')
        super().__init__(**options)

        # Mirror null is not explicitly defined
        if empty is None:
            empty = options.get('null', False)
        self.empty = empty

        if max_length is not None:
            self.validators.append(MaxLengthValidator(max_length))

    def to_python(self, value: Any) -> str:
        if value is None or isinstance(value, str):
            return value
        return str(value)

    def validate(self, value: str) -> None:
        if not self.empty and value == '':
            raise ValidationError(self.error_messages['null'])

        super().validate(value)


class Integer(Field[int]):
    """
    An integer.

    An Integer field has two extra arguments:

    :param min_value: The minimum value of the field. The ::attr:`min_value`
        value is enforced by validation rules.

    :param max_value: The maximum value of the field. The :attr:`max_value`
        value is enforced by validation rules.

    """
    native_type = int
    default_error_messages = {
        'invalid': "'{}' value must be an integer.",
    }

    def __init__(self, min_value: int=None, max_value: int=None, **options) -> None:
        super().__init__(**options)
        self.min_value = min_value
        if min_value is not None:
            self.validators.append(MinValueValidator(min_value))
        self.max_value = max_value
        if max_value is not None:
            self.validators.append(MaxValueValidator(max_value))

    def to_python(self, value: Any) -> Optional[int]:
        if value in EMPTY_VALUES:
            return
        try:
            return int(value)
        except (TypeError, ValueError):
            msg = self.error_messages['invalid'].format(value)
            raise ValidationError(msg)


class Float(Field[float]):
    """
    An float.

    A Float field has two extra arguments:

    :param min_value: The minimum value of the field. The ::attr:`min_value`
        value is enforced by validation rules.

    :param max_value: The maximum value of the field. The :attr:`max_value`
        value is enforced by validation rules.

    """
    native_type = float
    default_error_messages = {
        'invalid': "'{}' value must be an integer.",
    }

    def __init__(self, min_value: float=None, max_value: float=None, **options) -> None:
        super().__init__(**options)
        self.min_value = min_value
        if min_value is not None:
            self.validators.append(MinValueValidator(min_value))
        self.max_value = max_value
        if max_value is not None:
            self.validators.append(MaxValueValidator(max_value))

    def to_python(self, value: Any) -> Optional[float]:
        if value in EMPTY_VALUES:
            return
        try:
            return float(value)
        except (TypeError, ValueError):
            msg = self.error_messages['invalid'].format(value)
            raise ValidationError(msg)


class Boolean(Field[bool]):
    """
    A boolean value.
    """
    native_type = bool
    default_error_messages = {
        'invalid': "'{}' value must be either True or False."
    }
    true_strings = ('t', 'true', 'y', 'yes', 'on', '1', '✓')
    false_strings = ('f', 'false', 'n', 'no', 'off', '0')

    def to_python(self, value: Any) -> Optional[bool]:
        if value is None:
            return None

        if value in (True, False):
            # if value is 1 or 0 then it's equal to True or False, but we want
            # to return a true bool for semantic reasons.
            return bool(value)

        if isinstance(value, str):
            lvalue = value.lower()
            if lvalue in self.true_strings:
                return True
            if lvalue in self.false_strings:
                return False

        raise ValidationError(self.error_messages['invalid'].format(value))


class Date(Field[datetime.date]):
    """
    Field that handles date values encoded as a string.

    The format of the string is that defined by ISO-8601.
    """
    native_type = datetime.date
    default_error_messages = {
        'invalid': "Not a valid date string.",
    }
    data_type_name = "ISO-8601 Date"

    def to_python(self, value: Any) -> Optional[datetime.date]:
        if value in EMPTY_VALUES:
            return
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, datetime.datetime):
            return value.date()
        try:
            return datetimeutil.parse_iso_date(value)
        except ValueError:
            pass
        msg = self.error_messages['invalid']
        raise ValidationError(msg)


class Time(Field[datetime.time]):
    """
    Field that handles time values encoded as a string.

    The format of the string is that defined by ISO-8601.

    Use the ``assume_local`` flag to customise how naive (datetime values with
    no timezone) are handled and also how dates are decoded. If
    ``assume_local`` is True naive dates are assumed to represent the current
    system timezone.

    """
    native_type = datetime.time
    default_error_messages = {
        'invalid': "Not a valid time string.",
    }
    data_type_name = "ISO-8601 Time"

    def __init__(self, assume_local: bool=False, **options) -> None:
        super().__init__(**options)
        self.assume_local = assume_local

    def to_python(self, value: Any) -> Optional[datetime.time]:
        if value in EMPTY_VALUES:
            return
        if isinstance(value, datetime.time):
            return value
        default_timezone = datetimeutil.local if self.assume_local else datetimeutil.utc
        try:
            return datetimeutil.parse_iso_time(value, default_timezone)
        except ValueError:
            pass
        msg = self.error_messages['invalid']
        raise ValidationError(msg)


class NaiveTime(Field[datetime.time]):
    native_type = datetime.time


class DateTime(Field[datetime.datetime]):
    native_type = datetime.datetime


class NaiveDateTime(Field[datetime.datetime]):
    native_type = datetime.datetime


class HttpDateTime(Field[datetime.datetime]):
    native_type = datetime.datetime


class TimeStamp(Field[int]):
    native_type = int


class UUID(Field[uuid.UUID]):
    """
    A UUID value.
    """
    native_type = uuid.UUID
    default_error_messages = {
        'invalid': "'{}' is not a valid UUID."
    }

    def to_python(self, value: Any) -> Optional[uuid.UUID]:
        if value is None or value == '':
            return

        if isinstance(value, uuid.UUID):
            return value

        if isinstance(value, str):
            # Optimisation to skip multiple if/else blocks
            pass

        elif isinstance(value, bytes):
            # Handle bytes
            if len(value) == 16:
                return uuid.UUID(bytes=value)

            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError as e:
                raise ValidationError(self.error_messages['invalid'].format(value))

        elif isinstance(value, int):
            # Handle integer UUID
            try:
                return uuid.UUID(int=value)
            except ValueError as e:
                raise ValidationError(self.error_messages['invalid'].format(value))

        elif isinstance(value, (tuple, list)):
            try:
                return uuid.UUID(fields=value)
            except ValueError as e:
                raise ValidationError(self.error_messages['invalid'].format(value))

        try:
            return uuid.UUID(value)
        except ValueError as e:
            raise ValidationError(self.error_messages['invalid'].format(value))


ET = TypeVar('ET', enum.Enum, enum.Enum)


class Enum(Field[enum.Enum]):
    """
    An Enum field utilising the :class:`enum.Enum` builtin.

    An Enum field has one extra required argument:

    :param enum_type: The enum type to convert to from.

    Example::

        >>> class Colour(enum.Enum):
        ...     Red = 'red'
        ...     Green = 'green'
        ...     Blue = 'blue'

        >>> field = Enum(Colour)
        >>> value = field.clean('green')
        >>> assert value is Colour.Green

    """
    native_type = enum.Enum

    def __init__(self, enum_type: Type[enum.Enum], **options) -> None:
        super().__init__(**options)
        self.enum = enum_type

    def to_python(self, value: Any) -> Optional[enum.Enum]:
        if value in (None, ''):
            return

        # Attempt to convert
        try:
            return self.enum(value)
        except ValueError:
            raise ValidationError(self.error_messages['invalid_choice'] % value)

    def prepare(self, value: Optional[enum.Enum]) -> Any:
        if value in self.enum:
            return value.value


class List(Field[list]):
    native_type = list


class Dict(Field[dict]):
    native_type = dict


class TypedList(Field[list]):
    native_type = list


class TypedDict(Field[dict]):
    native_type = dict


class Url(Field[str]):
    native_type = str


class Email(Field[str]):
    native_type = str


class IPv4(Field[str]):
    native_type = str


class IPv6(Field[str]):
    native_type = str


class IPv46(Field[str]):
    native_type = str


# Fallback to maintain some backwards compatibility.
StringField = String
IntegerField = Integer
FloatField = Float
BooleanField = Boolean
DateField = Date
TimeField = Time
DateTimeField = DateTime
NaiveTimeField = NaiveTime
NaiveDateTimeField = NaiveDateTime
HttpDateTimeField = HttpDateTime
TimeStampField = TimeStamp
UUIDField = UUID
EnumField = Enum
ListField = List
DictField = Dict
