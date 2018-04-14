from typing import Any, Type, Callable, Tuple

from .utils import lazy_property
from .bases import FieldResolver
from .typing import ErrorMessageList, ValidationErrorHandler


class ResourceCache:
    # Use the Borg pattern to share state between all instances. Details at
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66531.
    __shared_state = dict(
        resources={},
        mappings={},
        field_resolvers=set(),
        validation_error_handlers={},
    )

    __slots__ = ('resources', 'mappings', 'field_resolvers', 'validation_error_handlers')

    def __init__(self):
        self.__dict__.update(self.__shared_state)

    # def register_resources(self, *resources):
    #     """
    #     Register a resource (or resources).
    #
    #     :param resources: Argument list of resources to register.
    #
    #     """
    #     for resource in resources:
    #         meta = getmeta(resource)
    #         resource_name = meta.resource_name.lower()
    #         self.resources[resource_name] = resource
    #         class_name = meta.class_name.lower()
    #         if resource_name != class_name:
    #             self.resources[class_name] = resource

    # def get_resource(self, resource_name):
    #     """
    #     Get a resource by name.
    #
    #     :param resource_name: Name of the resource to find.
    #     :returns: The resource type that matches requested name (case insensitive); or :const:`None` if the requested
    #         name has not been registered.
    #
    #     """
    #     return self.resources.get(resource_name.lower())

    # def register_mapping(self, mapping):
    #     """
    #     Register a mapping
    #
    #     :param mapping: Mapping object to register.
    #
    #     """
    #     mapping_name = generate_mapping_cache_name(mapping.from_obj, mapping.to_obj)
    #     self.mappings[mapping_name] = mapping

    # def get_mapping(self, from_obj, to_obj):
    #     """
    #     Get a mapping based on the from and to objects (likely to be resources).
    #
    #     :param from_obj: Object to map from.
    #     :param to_obj: Object to map to.
    #     :returns: A mapping object that supports mapping from *from_obj* to *to_obj*
    #     :raises: KeyError if a mapping cannot be found.
    #
    #     """
    #     mapping_name = generate_mapping_cache_name(from_obj, to_obj)
    #     return self.mappings[mapping_name]

    # Field Resolvers ###############################################

    def register_field_resolver(self, resolver: FieldResolver, base_type: Type[Any]) -> None:
        """
        Register a field resolver.

        The *base_type* will also cover all subclasses.

        :param base_type: Base type for subclasses that this resolver will work with.
        :param resolver: Resolver object used to resolve subclasses of *base_type*.

        """
        self.field_resolvers.add((base_type, resolver))

    def get_field_resolver(self, obj_type: Type[Any]) -> FieldResolver:
        """
        Get a field resolver for an object type.

        :param obj_type: Object type to find a field resolver for.
        :return: A field resolver instance for resolving fields on *obj_type*.
        :raises: KeyError if a resolver cannot be found.

        """
        for base_type, field_resolver in self.field_resolvers:
            if issubclass(obj_type, base_type):
                return field_resolver(obj_type)
        raise KeyError('No field resolver could be found for {!r}'.format(obj_type))

    # Validation Error handlers #####################################

    def register_validation_error_handler(self, error_type: Exception,
                                          handler: ValidationErrorHandler=None) -> Callable:
        """
        Register a validation error handler. This method can behave as a
        decorator.

        Validation error handlers are used to handle exceptions identified as
        validation errors during the field cleaning process. They are expected
        to extract failure reasons from the exception and update the supplied
        list of errors.

        Having handlers external to the core process allows for validators
        from other projects to be used (eg Django validators can be used with
        Odin).

        :param error_type: Error exception to register a handler for.
        :param handler: A method that can handle the exception type.

        Example::

            >>> @register_validation_error_handler(ValueError)
            ... def value_error_handler(exception: ValueError, field: 'Field', messages: ErrorMessageList) -> None:
            ...     ...

        """
        def inner(func):
            self.validation_error_handlers[error_type] = func
            return func

        return inner if handler is None else inner(inner)

    @lazy_property
    def validation_errors(self) -> Tuple[Exception]:
        """
        Get validation exception types that can be used in an except clause.
        """
        return tuple(self.validation_error_handlers.keys())

    def get_validation_error_handler(self, error_type: Exception) -> ValidationErrorHandler:
        """
        Get the handler for a particular exception type.

        :raises KeyError: If exception type isn't registered.

        """
        return self.validation_error_handlers[error_type.__class__]


cache = ResourceCache()

# register_resources = cache.register_resources
# get_resource = cache.get_resource
#
# register_mapping = cache.register_mapping
# get_mapping = cache.get_mapping

register_field_resolver = cache.register_field_resolver
get_field_resolver = cache.get_field_resolver

register_validation_error_handler = cache.register_validation_error_handler
validation_errors = cache.validation_errors
get_validation_error_handler = cache.get_validation_error_handler
