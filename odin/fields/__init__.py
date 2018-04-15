"""
Fields that are supplied with Odin.

These are split into three types:

#. Value - Fields that hold a single value eg ``str`` or ``int``
#. Composite - Fields that are made up of other resources eg
   ``List[MyResource]``
#. Virtual - Fields that are not assigned to a resource, these could be
   generated or constant values.

"""
from .base import BaseField, T, NotProvided
from .value import *
from .virtual import *

__all__ = (
    'NotProvided', 'Field',

    # Value fields
    'String', 'Integer', 'Float', 'Boolean',
    'Date', 'Time', 'NaiveTime', 'DateTime', 'NaiveDateTime',
    'TimeStamp', 'HttpDateTime',
    'UUID', 'Enum',
    'List', 'Dict', 'TypedList', 'TypedDict',
    'Url', 'Email', 'IPv4', 'IPv6', 'IPv46',

    # Composite fields

    # Virtual fields
    'ConstantField', 'CalculatedField', 'calculated_field', 'MultiPartField',

    # Fall-back field names
    'StringField', 'IntegerField', 'FloatField', 'BooleanField',
    'DateField', 'TimeField', 'NaiveTimeField', 'DateTimeField', 'NaiveDateTimeField',
    'TimeStampField', 'HttpDateTimeField',
    'UUIDField', 'EnumField',
    'ListField', 'DictField', 'TypedListField', 'TypedDictField',
    'UrlField', 'EmailField', 'IPv4Field', 'IPv6Field', 'IPv46Field',
)

# Fallback's for backwards compatibility.
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
TypedListField = TypedList
TypedDictField = TypedDict
UrlField = Url
EmailField = Email
IPv4Field = IPv4
IPv6Field = IPv6
IPv46Field = IPv46
