"""
Odin validators

"""
import abc
import re

from typing import Pattern, Union, Any, Sized, Callable, TypeVar

from . import exceptions
from .typing import Number
from .utils.ipv6 import is_valid_ipv6_address

EMPTY_VALUES = (None, '', [], (), {})


class RegexValidator:
    """
    Regular expression validator.
    """
    regex = r''
    message = 'Enter a valid value.'
    code = 'invalid'

    def __init__(self, regex: Union[str, Pattern]=None, message: str=None, code: str=None):
        if regex is not None:
            self.regex = regex
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code

        # Compile the regex if it was not passed pre-compiled.
        if isinstance(self.regex, str):
            self.regex = re.compile(self.regex)

    def __call__(self, value: str) -> None:
        """
        Validates that the input matches the regular expression.
        """
        if not self.regex.search(value):
            raise exceptions.ValidationError(self.message, code=self.code)


class URLValidator(RegexValidator):
    """
    Validate a URL.
    """
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    message = "Enter a valid URL value."


validate_url = URLValidator()


class BaseValidator(metaclass=abc.ABCMeta):
    """
    Common base for validators.
    """
    message = 'Ensure this value is {limit_value} (it is {show_value}).'
    code = 'limit_value'
    description = 'Ensure that a value is {limit_value}.'

    def __init__(self, limit_value: Number) -> None:
        self.limit_value = limit_value

    def __call__(self, value):
        cleaned = self.clean(value)
        params = dict(limit_value=self.limit_value, show_value=cleaned)
        if self.compare(cleaned, self.limit_value):
            raise exceptions.ValidationError(
                self.message.format(**params),
                code=self.code, params=params
            )

    def __str__(self) -> str:
        return self.description.format(limit_value=self.limit_value)

    @abc.abstractmethod
    def compare(self, a: Any, b: Any) -> bool:
        """
        Comparison function.
        """

    def clean(self, value: Any) -> Any:
        """
        Clean value prior to validation (eg get it's length)
        """
        return value


class MaxValueValidator(BaseValidator):
    """
    Validate a value is less than or equal to the limit value.
    """
    message = 'Ensure this value is less than or equal to {limit_value}.'
    code = 'max_value'
    description = 'Ensure value is less than or equal to {limit_value}.'

    def compare(self, a: Any, b: Any) -> bool:
        return a > b


class MinValueValidator(BaseValidator):
    """
    Validate a value is greater than or equal to the limit value.
    """
    message = 'Ensure this value is greater than or equal to {limit_value}.'
    code = 'min_value'
    description = 'Ensure value is greater than or equal to {limit_value}.'

    def compare(self, a: Any, b: Any) -> bool:
        return a < b


class LengthValidator(BaseValidator):
    """
    Validate a value exactly the expected length.
    """
    message = 'Ensure this value has exactly {limit_value:d} characters (it has {show_value:d}).'
    code = 'length'
    description = 'Ensure value has exactly {limit_value:d} characters.'

    def compare(self, a: Any, b: Any) -> bool:
        return a != b

    def clean(self, value: Sized) -> int:
        return len(value)


class MaxLengthValidator(LengthValidator):
    """
    Validate a values length is less than the limit value.
    """
    message = 'Ensure this value has at most {limit_value:d} characters (it has {show_value:d}).'
    code = 'max_length'
    description = 'Ensure value has at most {limit_value:d} characters.'

    def compare(self, a: Any, b: Any) -> bool:
        return a > b


class MinLengthValidator(LengthValidator):
    """
    Validate a values length is greater than the limit value.
    """
    message = 'Ensure this value has at least {limit_value:d} characters (it has {show_value:d}).'
    code = 'min_length'
    description = 'Ensure value has at least {limit_value:d} characters.'

    def compare(self, a: Any, b: Any) -> bool:
        return a < b


T = TypeVar('T')


def simple_validator(message: str='The supplied value is invalid', code: str='invalid',
                     assertion: Callable[[T], bool]=None) -> Callable[[T], None]:
    """
    Create a simple validator.

    :param message: Message to raised in Validation exception if validation fails.
    :param code: Code to included in Validation exception. This can be used to customise the message at the resource
        level.
    :param assertion: An Validation exception will be raised if this check returns a none True value.

    Usage::

        >>> none_validator = simple_validator(lambda x: x is not None, message="This value cannot be none")

    This can also be used as a decorator::

        >>> @simple_validator("This value cannot be none")
        ... def none_validator(v):
        ...     return v is not None

    """
    if callable(message):
        message, code, assertion = 'The supplied value is invalid', 'invalid', message

    def inner(func):
        def wrapper(value):
            params = {'show_value': value}
            if not func(value):
                raise exceptions.ValidationError(message.format(params), code=code, params=params)
        return wrapper

    return inner(assertion) if assertion else inner


class IPv4Address(RegexValidator):
    """
    Validate an IPv4 address
    """
    regex = r'^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9]?[0-9])){3}\Z'
    message = 'Enter a valid IPv4 address.'


validate_ipv4_address = IPv4Address()


@simple_validator("Enter a valid IPv6 address")
def validate_ipv6_address(value):
    """
    Validate an IPv6 address
    """
    return is_valid_ipv6_address(value)


def validate_ipv46_address(value):
    """
    Validate is either an IPv4 or IPv6 address
    """
    try:
        validate_ipv4_address(value)
    except exceptions.ValidationError:
        try:
            validate_ipv6_address(value)
        except exceptions.ValidationError:
            raise exceptions.ValidationError('Enter a valid IPv4 or IPv6 address.', code='invalid')


class EmailValidator(object):
    """
    Validate an Email address.
    """
    message = 'Enter a valid email address.'
    code = 'invalid'
    user_regex = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)',  # quoted-string
        re.IGNORECASE)
    domain_regex = re.compile(
        # max length for domain name labels is 63 characters per RFC 1034
        r'((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))\Z',
        re.IGNORECASE)
    literal_regex = re.compile(
        # literal form, ipv4 or ipv6 address (SMTP 4.1.3)
        r'\[([A-f0-9:.]+)\]\Z',
        re.IGNORECASE)
    domain_whitelist = ['localhost']

    def __init__(self, message=None, code=None, whitelist=None):
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if whitelist is not None:
            self.domain_whitelist = whitelist

    def __call__(self, value):
        if not value or '@' not in value:
            raise exceptions.ValidationError(self.message, code=self.code)

        user_part, domain_part = value.rsplit('@', 1)

        if not self.user_regex.match(user_part):
            raise exceptions.ValidationError(self.message, code=self.code)

        if (domain_part not in self.domain_whitelist and
                not self.validate_domain_part(domain_part)):
            # Try for possible IDN domain-part
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
                if self.validate_domain_part(domain_part):
                    return
            except UnicodeError:
                pass
            raise exceptions.ValidationError(self.message, code=self.code)

    def validate_domain_part(self, domain_part):
        if self.domain_regex.match(domain_part):
            return True

        literal_match = self.literal_regex.match(domain_part)
        if literal_match:
            ip_address = literal_match.group(1)
            try:
                validate_ipv46_address(ip_address)
                return True
            except exceptions.ValidationError:
                pass


validate_email_address = EmailValidator()
