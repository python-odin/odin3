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
