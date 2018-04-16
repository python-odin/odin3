import abc

from typing import Any, Optional, Generic, Type, TypeVar

from .. import getmeta
from .. import Resource
from ..exceptions import ValidationError
from .value import ValueField, EMPTY_VALUES

R = TypeVar('R', bound=Resource)


class CompositeField(Generic[R], ValueField[R]):
    """
    Composite Field

    These are fields that are made up of other resource types.

    :param resource: Resource to group
    :param use_container: Special flag for codecs that support containers or just multiple instances of a
        sub element (ie XML).
    :param empty: This collection can be empty
    :param options: Additional options passed to :py:class:`odin.fields.Field` super class.

    """
    def __init__(self, resource: Type[R], use_container: bool=False, **options):
        if not getmeta(resource):
            raise TypeError("``{!r}`` is not a valid type for a related field.".format(resource))

        if not options.get('null', False):
            options.setdefault('default', resource)

        super().__init__(**options)

        self.of = resource
        self.use_container = use_container

    def to_python(self, value: Any) -> Optional[R]:
        if value is None:
            return None

        if isinstance(value, self.of):
            return value

        if isinstance(value, dict):
            return create_resource_from_dict(value, getmeta(self.of).resource_name)

        msg = self.error_messages['invalid'].format(self.of)
        raise ValidationError(msg)

    def validate(self, value: R) -> None:
        super().validate(value)
        if value not in EMPTY_VALUES:
            value.full_clean()

    @abc.abstractmethod
    def item_iter_from_object(self, obj: object):
        """
        Return an iterator of items (resource, idx) from composite field.

        For single items (eg ``DictAs`` will return a list a single item (resource, None))
        """

    @abc.abstractmethod
    def key_to_python(self, key: Any) -> Optional[R]:
        """
        A to python method for the key value.
        """


class DictAs(CompositeField):
    """
    Treat a dictionary as a Resource.
    """
    default_error_messages = {
        'invalid': "Must be a dict of type ``{!r}``.",
    }

    def item_iter_from_object(self, obj):
        resource = self.value_from_object(obj)
        if resource:
            yield (None, resource)

    def key_to_python(self, key):
        pass  # Not required as keys are not used.


class ListOf(CompositeField):
    """
    List of resources.
    """
    default_error_messages = {
        'invalid': "Must be a list of ``{!r}`` objects.",
        'null': "List cannot contain null entries.",
        'empty': "List cannot be empty",
    }
    data_type_name = "List of"

    def __init__(self, resource, empty=True, **options):
        options.setdefault('default', list)
        super().__init__(resource, **options)
        self.empty = empty

    @staticmethod
    def _process_list(value_list, method):
        values = []
        errors = {}
        for idx, value in enumerate(value_list):
            error_key = str(idx)

            try:
                values.append(method(value))
            except ValidationError as ve:
                errors[error_key] = ve.error_messages

        if errors:
            raise ValidationError(errors)

        return values

    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, (list, bases.ResourceIterable)):
            super_to_python = super(ListOf, self).to_python

            def process(val):
                if val is None:
                    raise ValidationError(self.error_messages['null'])
                return super_to_python(val)

            return self._process_list(value, process)
        msg = self.error_messages['invalid'].format(self.of)
        raise ValidationError(msg)

    def validate(self, value):
        # Skip The direct super method and apply it to each list item.
        super(CompositeField, self).validate(value)  # noqa
        if value is not None:
            super_validate = super(ListOf, self).validate
            self._process_list(value, super_validate)

        if (value is not None) and (not value) and (not self.empty):
            raise ValidationError(self.error_messages['empty'])

    def __iter__(self):
        # This does nothing but it does prevent inspections from complaining.
        return None  # NoQA

    def item_iter_from_object(self, obj):
        resources = self.value_from_object(obj)
        if resources:
            for i in enumerate(resources):
                yield i

    def key_to_python(self, key):
        """
        A to python method for the key value.
        :param key:
        :return:
        """
        return int(key)


class DictOf(CompositeField):
    """
    Dictionary of resources.
    """
    default_error_messages = {
        'invalid': "Must be a dict of ``{!r}`` objects.",
        'null': "Dict cannot contain null entries.",
        'empty': "List cannot be empty",
        'invalid_key': 'Key {!r} is not a valid choice.',
    }
    data_type_name = "Dict of"

    def __init__(self, resource, empty=True, key_choices=None, **options):
        options.setdefault('default', dict)
        super(DictOf, self).__init__(resource, **options)
        self.empty = empty
        self.key_choices = key_choices

    def _process_dict(self, value_dict, method):
        values = {}
        errors = {}
        key_choices = self.key_choices
        for key, value in value_dict.items():
            if key_choices and not value_in_choices(key, key_choices):
                msg = self.error_messages['invalid_key'] % value
                raise ValidationError(msg)

            try:
                values[key] = method(value)
            except ValidationError as ve:
                errors[key] = ve.error_messages

        if errors:
            raise ValidationError(errors)

        return values

    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, dict):
            super_to_python = super(DictOf, self).to_python

            def process(val):
                if val is None:
                    raise ValidationError(self.error_messages['null'], code='null')
                return super_to_python(val)

            return self._process_dict(value, process)
        msg = self.error_messages['invalid'].format(self.of)
        raise ValidationError(msg)

    def validate(self, value):
        # Skip The direct super method and apply it to each list item.
        super(CompositeField, self).validate(value)  # noqa
        if value is not None:
            super_validate = super(DictOf, self).validate
            self._process_dict(value, super_validate)

        if (value is not None) and (not value) and (not self.empty):
            raise ValidationError(self.error_messages['empty'], code='empty')

    def __iter__(self):
        # This does nothing but it does prevent inspections from complaining.
        return None  # NoQA

    def item_iter_from_object(self, obj):
        resources = self.value_from_object(obj)
        if resources:
            for key in sorted(resources):
                yield key, resources[key]

    def key_to_python(self, key):
        """
        A to python method for the key value.
        """
        return key
