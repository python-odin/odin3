"""
Fields that are supplied with Odin.

These are split into three types:

#. Value - Fields that hold a single value eg ``str`` or ``int``
#. Composite - Fields that are made up of other resources eg
   ``List[MyResource]``
#. Virtual - Fields that are not assigned to a resource, these could be
   generated or constant values.

"""
from .value import (
    ValueField,
    String, Integer, Float, Boolean,
    Date, Time, NaiveTime, DateTime, NaiveDateTime, TimeStamp, HttpDateTime,
    UUID, Enum,
    List, TypedList, Dict, TypedDict,
    Url, Email, IPv4, IPv6, IPv46
)
from .virtual import (
    VirtualField,
    Constant,
    Calculated, calculated,
    MultiPart
)
from .composite import (
    CompositeField,
)

# Fallback's for backwards compatibility.
Field = ValueField
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
