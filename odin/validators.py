"""
Odin validators

"""
import re

from typing import Pattern, Union, Any, Sized

from . import exceptions
from .typing import Number

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


class BaseValidator:
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

    def compare(self, a: Any, b: Any) -> bool:
        raise NotImplementedError()

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
    message = 'Ensure this value has exactly %(limit_value)d characters (it has %(show_value)d).'
    code = 'length'
    description = 'Ensure value has exactly %(limit_value)d characters.'

    def compare(self, a: Any, b: Any) -> bool:
        return a != b

    def clean(self, value: Sized) -> int:
        return len(value)


class MaxLengthValidator(LengthValidator):
    """
    Validate a values length is less than the limit value.
    """
    message = 'Ensure this value has at most %(limit_value)d characters (it has %(show_value)d).'
    code = 'max_length'
    description = 'Ensure value has at most %(limit_value)d characters.'

    def compare(self, a: Any, b: Any) -> bool:
        return a > b


class MinLengthValidator(LengthValidator):
    """
    Validate a values length is greater than the limit value.
    """
    message = 'Ensure this value has at least %(limit_value)d characters (it has %(show_value)d).'
    code = 'min_length'
    description = 'Ensure value has at least %(limit_value)d characters.'

    def compare(self, a: Any, b: Any) -> bool:
        return a < b
