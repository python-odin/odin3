"""
Additional type definitions used in Odin.
"""
from typing import Any, Union, List, Dict, Callable

Number = Union[int, float]

ErrorMessageList = List[str]
ErrorMessageDict = Dict[str, List[str]]
ValidationMessages = Union[str, ErrorMessageList, ErrorMessageDict]

Validator = Callable[[Any], None]
ValidationErrorHandler = Callable[[Exception, 'Field', ErrorMessageList], None]
