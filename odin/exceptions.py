from typing import Union, List, Dict

from . import registration
from .typing import ValidationMessages, ErrorMessageDict


class OdinException(Exception):
    pass


NON_FIELD_ERRORS = '__all__'


class ValidationError(OdinException):
    """
    ValidationError can be passed any object that can be printed (usually a
    string), a list of objects or a dictionary.
    """
    def __init__(self, message: ValidationMessages, code: str=None, params: Dict[str, str]=None) -> None:
        if isinstance(message, dict):
            self.message_dict = message
        elif isinstance(message, list):
            self.messages = message
        else:
            self.messages = [message]
            self.code = code
            self.params = params

    def __str__(self) -> str:
        # This is needed because, without a __str__(), printing an exception
        # instance would result in this:
        # AttributeError: ValidationError instance has no attribute 'args'
        # See http://www.python.org/doc/current/tut/node10.html#handling
        if hasattr(self, 'message_dict'):
            message_dict = self.message_dict
            return '{{{}}}'.format(', '.join(
                "'{}': {!r}".format(k, message_dict[k]) for k in sorted(message_dict)
            ))
        return repr(self.messages)

    def __repr__(self) -> str:
        return '<ValidationError: {}>'.format(self)

    @property
    def error_messages(self) -> Union[List, Dict]:
        if hasattr(self, 'message_dict'):
            return self.message_dict
        else:
            return self.messages

    def update_error_dict(self, error_dict: ErrorMessageDict) -> ErrorMessageDict:
        if hasattr(self, 'message_dict'):
            if error_dict:
                for k, v in self.message_dict.items():
                    error_dict.setdefault(k, []).extend(v)
            else:
                error_dict = self.message_dict
        else:
            error_dict[NON_FIELD_ERRORS] = self.messages
        return error_dict


@registration.register_validation_error_handler(ValidationError)
def validation_error_handler(exception: ValidationError, field, errors) -> None:
    if hasattr(exception, 'code') and exception.code in field.error_messages:
        message = field.error_messages[exception.code]
        if exception.params:
            message = message.format(exception.params)
        errors.append(message)
    else:
        errors.extend(exception.messages)


class ResourceException(ValidationError):
    """
    Errors raised when generating resource from files.

    Exception inherits from ``ValidationError`` for backwards compatibility.

    """
