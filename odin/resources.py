import copy

from typing import TypeVar, List, Dict, Any, Union, Type, Callable, Sequence, Generator, Tuple, Iterable

from . import exceptions, registration
from .bases import FieldBase, ValueFieldBase
from .exceptions import ValidationError
from .typing import NotProvided
from .utils.collections import force_tuple
from .utils.decorators import lazy_property

DEFAULT_TYPE_FIELD = '$'


class ResourceOptions:
    """
    Options definition for each resource type.
    """
    META_OPTION_NAMES = (
        'name', 'namespace', 'name_space', 'verbose_name', 'verbose_name_plural', 'abstract', 'doc_group',
        'type_field', 'key_field_name', 'key_field_names', 'field_sorting', 'default_null'
    )

    INHERITED_META_OPTIONS = {
        'name_space': NotProvided,
        'field_sorting': False,
        'default_null': False,
        'type_field': DEFAULT_TYPE_FIELD,
        'key_field_names': [],
    }

    def __init__(self, meta: Any) -> None:
        self.meta = meta
        self.parents = []  # type: List[Resource]

        self.fields = []  # type: List[ValueFieldBase]
        self._key_fields = []  # type: List[FieldBase]
        self.virtual_fields = []  # type: List[FieldBase]

        self.name = None  # type: str
        self.class_name = None  # type: str
        self.verbose_name = None  # type: str
        self.verbose_name_plural = None  # type: str
        self.abstract = False
        self.doc_group = None  # type: str

        self.name_space = NotProvided       # type: str
        self.field_sorting = NotProvided    # type: Callable[[Sequence[FieldBase]], List[FieldBase]]
        self.default_null = NotProvided     # type: bool
        self.type_field = NotProvided       # type: str
        self.key_field_names = NotProvided  # type: str

    def __repr__(self):
        return '<Options for {}>'.format(self.resource_name)

    def contribute_to_class(self, cls, _):
        # Assign self to resource class and get name details
        cls._meta = self
        self.name = cls.__name__
        self.class_name = '{}.{}'.format(cls.__module__, cls.__name__)

        if self.meta:
            meta_attrs = {
                k: v for k, v in self.meta.__dict__.copy().items()
                if not k.startswith('_')
            }

            for attr_name in self.META_OPTION_NAMES:
                if attr_name in meta_attrs:
                    value = meta_attrs.pop(attr_name)

                    # Allow name_space to be defined as namespace
                    if attr_name == 'namespace':
                        attr_name = 'name_space'

                    # Allow key_field_names to be defined as key_field_name
                    elif attr_name == 'key_field_name':
                        attr_name = 'key_field_names'
                        value = [value]

                    setattr(self, attr_name, value)

            # Any leftover attributes must be invalid.
            if meta_attrs != {}:
                raise TypeError(
                    "'class Meta' got invalid attribute(s): {}".format(
                        ','.join(meta_attrs.keys())
                    )
                )

        del self.meta

        if not self.verbose_name:
            self.verbose_name = self.name.replace('_', ' ').strip('_ ')
        if not self.verbose_name_plural:
            self.verbose_name_plural = self.verbose_name + 's'

    def inherit_from(self, parent_meta: 'ResourceOptions'=None) -> None:
        """
        Handle inheritance.
        """
        if parent_meta:
            # Copy inherited fields if not defined.
            for field in self.INHERITED_META_OPTIONS.keys():
                if getattr(self, field) is NotProvided:
                    setattr(self, field, getattr(parent_meta, field))

        # Set defaults
        for field, value in self.INHERITED_META_OPTIONS.items():
            if getattr(self, field) is NotProvided:
                setattr(self, field, value)

        # Ensure key fields is a tuple
        self.key_field_names = force_tuple(self.key_field_names)

    def add_field(self, field: ValueFieldBase) -> None:
        """
        Dynamically add a field.
        """
        self.fields.append(field)
        if field.key:
            self._key_fields.append(field)

    def add_virtual_field(self, field: FieldBase) -> None:
        """
        Dynamically add a virtual field.
        """
        self.virtual_fields.append(field)
        if field.key:
            self._key_fields.append(field)

    @lazy_property
    def resource_name(self) -> str:
        """
        Full name of resource including namespace (if specified)
        """
        if self.name_space:
            return "{}.{}".format(self.name_space, self.name)
        else:
            return self.name

    @lazy_property
    def parent_resource_names(self) -> Sequence[str]:
        """
        List of parent resource names.
        """
        return tuple(getmeta(p).resource_name for p in self.parents)

    @lazy_property
    def all_fields(self) -> Sequence[FieldBase]:
        """
        All fields both standard and virtual.
        """
        return tuple(self.fields + self.virtual_fields)

    @lazy_property
    def field_map(self) -> Dict[str, ValueFieldBase]:
        """
        Map of fields field names to fields.
        :return:
        """
        return {f.attname: f for f in self.fields}

    @lazy_property
    def element_field_map(self) -> Dict[str, ValueFieldBase]:
        """
        Map of element field names to fields.
        """
        return {f.attname: f for f in self.element_fields}

    @lazy_property
    def init_fields(self) -> Sequence[ValueFieldBase]:
        """
        Fields used in resource initialisation
        """
        return self.fields

    @lazy_property
    def composite_fields(self) -> Sequence[ValueFieldBase]:
        """
        All composite fields.
        """
        # Not the nicest solution but is a fairly safe way of detecting a composite field.
        return tuple(f for f in self.fields if (hasattr(f, 'of') and issubclass(f.of, Resource)))

    @lazy_property
    def container_fields(self) -> Sequence[ValueFieldBase]:
        """
        All composite fields with the container flag.

        Used by XML like codecs.

        """
        return tuple(f for f in self.composite_fields if getattr(f, 'use_container', False))

    @lazy_property
    def attribute_fields(self) -> Sequence[ValueFieldBase]:
        """
        List of fields where is_attribute is True.
        """
        return tuple(f for f in self.fields if f.is_attribute)

    @lazy_property
    def element_fields(self) -> Sequence[ValueFieldBase]:
        """
        List of fields where is_attribute is False.
        """
        return tuple(f for f in self.fields if not f.is_attribute)

    @lazy_property
    def key_fields(self) -> Sequence[FieldBase]:
        """
        Tuple of fields specified as the key fields
        """
        # Key fields names in meta go first
        field_names = set(self.key_field_names) if self.key_field_names else set()

        # Move over any fields defined as keys
        if self._key_fields:
            field_names.update(f.attname for f in self._key_fields)

        fields = (self.field_map[f] for f in field_names)  # type: Generator[FieldBase]
        return sorted(fields, key=hash)

    @lazy_property
    def readonly_fields(self) -> Sequence[FieldBase]:
        """
        Fields that can only be read from.
        """
        return self.virtual_fields


class ResourceType(type):
    """
    Resource metaclass.

    This metaclass is used to detect and process field instances and the
    ``Meta`` class definition into a common :class:`ResourceOptions` object.
    """
    meta_options = ResourceOptions

    def __new__(mcs, name, base_objects, attrs):
        super_new = super(ResourceType, mcs).__new__

        # attrs will never be empty for classes declared in the standard way
        # (ie. with the `class` keyword). This is quite robust.
        if name == 'NewBase' and attrs == {}:
            return super_new(mcs, name, base_objects, attrs)

        parents = [
            b for b in base_objects if
            isinstance(b, ResourceType) and not (b.__name__ == 'NewBase' and b.__mro__ == (b, object))
        ]
        if not parents:
            # If this isn't a subclass of Resource, don't do anything special.
            return super_new(mcs, name, base_objects, attrs)

        # Create the class.
        module = attrs.pop('__module__')
        new_class = super_new(mcs, name, base_objects, {'__module__': module})
        attr_meta = attrs.pop('Meta', None)
        abstract = getattr(attr_meta, 'abstract', False)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
        base_meta = getattr(new_class, '_meta', None)

        new_meta = mcs.meta_options(meta)
        new_class.add_to_class('_meta', new_meta)

        # Handle inheritance
        new_meta.inherit_from(base_meta)

        # Bail out early if we have already created this class.
        r = registration.get_resource(new_meta.resource_name)
        if r is not None:
            return r

        # Add all attributes to the class.
        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)

        # Sort the fields
        if not new_meta.field_sorting:
            new_meta.fields = sorted(new_meta.fields, key=hash)

        # All the fields of any type declared on this model
        local_field_attnames = {f.attname for f in new_meta.fields}
        field_attnames = set(local_field_attnames)

        for base in parents:
            try:
                base_meta = getmeta(base)
            except AttributeError:
                # Things without _meta aren't functional models, so they're
                # uninteresting parents.
                continue

            # Check for clashes between locally declared fields and those
            # on the base classes (we cannot handle shadowed fields at the
            # moment).
            for field in base_meta.all_fields:
                if field.attname in local_field_attnames:
                    raise Exception('Local field %r in class %r clashes with field of similar name from '
                                    'base class %r' % (field.attname, name, base.__name__))
            for field in base_meta.fields:
                if field.attname not in field_attnames:
                    field_attnames.add(field.attname)
                    new_class.add_to_class(field.attname, copy.deepcopy(field))
            for field in base_meta.virtual_fields:
                new_class.add_to_class(field.attname, copy.deepcopy(field))

            new_meta.parents += base_meta.parents
            new_meta.parents.append(base)

        # Sort the fields
        if new_meta.field_sorting:
            if callable(new_meta.field_sorting):
                new_meta.fields = new_meta.field_sorting(new_meta.fields)
            else:
                new_meta.fields = sorted(new_meta.fields, key=hash)

        # If a key_field is defined ensure it exists
        if new_meta.key_field_names:
            for field_name in new_meta.key_field_names:
                if field_name not in new_meta.field_map:
                    raise AttributeError('Key field `{}` does not exist on this resource.'.format(field_name))

        # Give fields an opportunity to do additional operations after the
        # resource is full populated and ready.
        for field in new_meta.all_fields:
            if hasattr(field, 'on_resource_ready'):
                field.on_resource_ready()

        if abstract:
            return new_class

        # Register resource
        registration.register_resources(new_class)

        # Because of the way imports happen (recursively), we may or may not be
        # the first time this model tries to register with the framework. There
        # should only be one class for each model, so we always return the
        # registered version.
        return registration.get_resource(new_meta.resource_name)

    def add_to_class(cls, name: str, obj):
        if hasattr(obj, 'contribute_to_class'):
            obj.contribute_to_class(cls, name)
        else:
            setattr(cls, name, obj)


class ResourceBase:
    def __init__(self, *args, **kwargs) -> None:
        args_len = len(args)
        meta = getmeta(self)
        if args_len > len(meta.init_fields):
            raise TypeError('This resource takes {} positional arguments but {} where given.'.format(
                len(meta.init_fields), args_len))

        # The ordering of the zip calls matter - zip throws StopIteration
        # when an iter throws it. So if the first iter throws it, the second
        # is *not* consumed. We rely on this, so don't change the order
        # without changing the logic.
        fields_iter = iter(meta.init_fields)
        if args_len:
            if not kwargs:
                for val, field in zip(args, fields_iter):
                    setattr(self, field.attname, val)
            else:
                for val, field in zip(args, fields_iter):
                    setattr(self, field.attname, val)
                    kwargs.pop(field.name, None)

        # Now we're left with the unprocessed fields that *must* come from
        # keywords, or default.
        for field in fields_iter:
            try:
                val = kwargs.pop(field.attname)
            except KeyError:
                val = field.get_default()
            setattr(self, field.attname, val)

        if kwargs:
            raise TypeError("'{}' is an invalid keyword argument for this function".format(list(kwargs)[0]))

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self)

    def __str__(self):
        return '{} resource'.format(getmeta(self).resource_name)

    @classmethod
    def from_dict(cls, d: Dict[str, Any], full_clean: bool=False) -> 'Resource':
        """
        Create a resource instance from a dictionary.
        """
        return create_resource_from_dict(d, cls, full_clean)

    def to_dict(self, include_virtual: bool=True) -> Dict[str, Any]:
        """
        Convert this resource into a `dict` of field_name/value pairs.

        .. note::
            This method is not recursive, it only operates on this single
            resource, any sub resources are returned as is. The use case that
            prompted the creation of this method is within codecs when a
            resource must be converted into a type that can be serialised,
            these codecs then operate recursively on the returned `dict`.

        :param include_virtual: Include virtual fields when generating `dict`.

        """
        meta = getmeta(self)
        fields = meta.all_fields if include_virtual else meta.fields
        return {f.name: v for f, v in field_iter_items(self, fields)}

    # def convert_to(self, to_resource: 'Resource', context: Any=None, ignore_fields: Sequence[str]=None,
    #                **field_values: Any) -> 'Resource':
    #     """
    #     Convert this resource into a specified resource.
    #
    #     A mapping must be defined for conversion between this resource and
    #     `to_resource` or an exception will be raised.
    #
    #     """
    #     mapping = registration.get_mapping(self.__class__, to_resource)
    #     ignore_fields = ignore_fields or []
    #     ignore_fields.extend(mapping.exclude_fields)
    #     self.full_clean(ignore_fields)
    #     return mapping(self, context).convert(**field_values)
    #
    # def update_existing(self, obj, context: Any=None, ignore_fields: Sequence[str]=None, fields=None,
    #                     ignore_not_provided: bool=False) -> None:
    #     """
    #     Update the fields on an existing destination object.
    #
    #     A mapping must be defined for conversion between this resource and
    #     `obj` type or an exception will be raised.
    #
    #     """
    #     self.full_clean(ignore_fields, ignore_not_provided)
    #     mapping = registration.get_mapping(self.__class__, obj.__class__)
    #     mapping(self, context).update(obj, ignore_fields, fields, ignore_not_provided)

    def extra_attrs(self, attrs: Dict[str, Any]) -> None:
        """
        Called during de-serialisation of data if there are any extra fields
        defined in the document.

        This allows the resource to decide how to handle these fields. By
        default they are ignored.
        """

    def clean(self) -> None:
        """
        Called post :method:`Resource.clean_fields` to perform resource level
        validation.
        """

    def full_clean(self, exclude: Sequence[str]=None, ignore_not_provided: bool=False) -> None:
        """
        Cleans all fields and triggers resource level validation. A
        ``ValidationError`` exception is raised if any errors are found.
        """
        errors = {}

        try:
            self.clean_fields(exclude, ignore_not_provided)
        except ValidationError as e:
            errors = e.update_error_dict(errors)

        try:
            self.clean()
        except ValidationError as e:
            errors = e.update_error_dict(errors)

        if errors:
            raise ValidationError(errors)

    def clean_fields(self, exclude: Sequence[str]=None, ignore_not_provided: bool=False) -> None:
        """
        Clean each field. Using the fields own clean method.

        Fields can also have special validation applied by defining a method
        named `clean_FIELD_NAME`.

        :param exclude: Fields to be excluded.
        :param ignore_not_provided: Ignore any fields that are not provided.

        """
        errors = {}
        meta = getmeta(self)

        for f in meta.fields:
            if exclude and f.name in exclude:
                continue

            raw_value = f.value_from_object(self)

            if (f.null and raw_value is None) or (ignore_not_provided and raw_value is NotProvided):
                continue

            try:
                raw_value = f.clean(raw_value)
            except ValidationError as e:
                errors[f.name] = e.messages

            # Check for resource level clean methods.
            clean_method = getattr(self, "clean_" + f.attname, None)
            if callable(clean_method):
                try:
                    raw_value = clean_method(raw_value)
                except ValidationError as e:
                    errors.setdefault(f.name, []).extend(e.messages)

            if f not in meta.readonly_fields:
                f.value_to_object(self, raw_value)

        if errors:
            raise ValidationError(errors)


class Resource(ResourceBase, metaclass=ResourceType):
    pass


R = TypeVar("R", bound=ResourceBase)
ResourceUnion = Union[Type[R], Sequence[R]]


def getmeta(type_or_instance: Union[type, object]) -> ResourceOptions:
    """
    Get resource options or meta object, from Resource.
    """
    return getattr(type_or_instance, '_meta')


def field_iter(resource: R, include_virtual: bool=True) -> Generator[FieldBase, None, None]:
    """
    Return an iterator that yields fields from a resource.

    :param resource: Resource to iterate over.
    :param include_virtual: Include virtual fields.

    """
    if include_virtual:
        yield from getmeta(resource).all_fields
    else:
        yield from getmeta(resource).fields


def field_iter_items(resource: R, fields: Sequence[str]=None) -> Generator[Tuple[FieldBase, Any], None, None]:
    """
    Return an iterator that yields fields and their values from a resource.

    :param resource: Resource to iterate over.
    :param fields: Fields to use; if :const:`None` defaults to all of the
        resources fields.

    """
    fields = fields or getmeta(resource).all_fields
    for f in fields:
        yield f, f.prepare(f.value_from_object(resource))


def resolve_resource_type(resource):
    if isinstance(resource, type) and issubclass(resource, ResourceBase):
        meta = getmeta(resource)
        return meta.resource_name, meta.type_field
    else:
        return resource, DEFAULT_TYPE_FIELD


def create_resource_from_iter(i: Iterable[Any], resource: ResourceUnion, full_clean: bool=True,
                              default_to_not_provided: bool=False) -> R:
    """
    Create a resource from an iterable sequence

    :param i: Iterable of values (it is assumed the values are in field
        order)

    :param resource: A resource type, resource name or list of resources and
        names to use as the base for creating a resource.

    :param full_clean: Perform a full clean as part of the creation, this is
        useful for parsing data with known columns (eg CSV data).

    :param default_to_not_provided: If an value is not supplied keep the value
        as ``NotProvided``. This is used to support merging an updated value.

    :return: New instance of resource type specified in the *resource* param.

    """
    i = list(i)
    resource_type = resource
    fields = getmeta(resource_type).fields

    # Optimisation to allow the assumption that len(fields) == len(i)
    len_fields = len(fields)
    len_i = len(i)
    extra = None
    if len_i < len_fields:
        i += [NotProvided] * (len_fields - len_i)
    elif len_i > len_fields:
        extra = i[len_fields:]
        i = i[:len_fields]

    # Determine values and build a list of values.
    attrs = []
    errors = {}
    for f, value in zip(fields, i):
        if value is NotProvided:
            if not default_to_not_provided:
                value = f.get_default() if f.use_default_if_not_provided else None
        else:
            try:
                value = f.to_python(value)
            except ValidationError as ve:
                errors[f.name] = ve.error_messages
        attrs.append(value)

    if errors:
        raise ValidationError(errors)

    # Create and validate the resource
    new_resource = resource_type(*attrs)
    if extra:
        new_resource.extra_attrs(extra)
    if full_clean:
        new_resource.full_clean()

    return new_resource


def create_resource_from_dict(d: Dict[str, Any], resource: ResourceUnion=None, full_clean: bool=True,
                              copy_dict: bool=True, default_to_not_provided: bool=False) -> R:
    """
    Create a resource from a dict.

    :param d: dictionary of data.

    :param resource: A resource type or list of resources to use as the base
        for creating a resource. If a list is supplied the first item will be
        used if a resource type is not supplied; this could also be a
        parent(s) of any resource defined by the dict.

    :param full_clean: Perform a full clean as part of the creation.

    :param copy_dict: Use a copy of the input dictionary rather than
        destructively processing the input dict.

    :param default_to_not_provided: If an value is not supplied keep the value
        as ``NotProvided``. This is used to support merging an updated value.

    """
    if copy_dict:
        d = d.copy()

    if resource:
        resource_type = None

        # Convert to single resource then resolve document type
        if isinstance(resource, (tuple, list)):
            resources = tuple(resolve_resource_type(r) for r in resource)
        else:
            resources = resolve_resource_type(resource),

        for resource_name, type_field in resources:
            # See if the input includes a type field  and check it's registered
            document_resource_name = d.get(type_field, None)
            if document_resource_name:
                resource_type = registration.get_resource(document_resource_name)
            else:
                resource_type = registration.get_resource(resource_name)

            if not resource_type:
                raise exceptions.ResourceException("Resource `{}` is not registered.".format(document_resource_name))

            if document_resource_name:
                # Check resource types match or are inherited types
                if (resource_name == document_resource_name or
                        resource_name in getmeta(resource_type).parent_resource_names):
                    break  # We are done
            else:
                break

        if not resource_type:
            raise exceptions.ResourceException(
                "Incoming resource does not match [{}]".format(', '.join(r for r, t in resources))
            )
    else:
        # No resource specified, relay on type field
        document_resource_name = d.pop(DEFAULT_TYPE_FIELD, None)
        if not document_resource_name:
            raise exceptions.ResourceException("Resource not defined.")

        # Get an instance of a resource type
        resource_type = registration.get_resource(document_resource_name)
        if not resource_type:
            raise exceptions.ResourceException("Resource `{}` is not registered.".format(document_resource_name))

    # Build list
    attrs = []
    errors = {}
    meta = getmeta(resource_type)
    for f in meta.init_fields:
        value = d.pop(f.name, NotProvided)
        if value is NotProvided:
            if not default_to_not_provided:
                value = f.get_default() if f.use_default_if_not_provided else None
        else:
            try:
                value = f.to_python(value)
            except ValidationError as ve:
                errors[f.name] = ve.error_messages
        attrs.append(value)

    if errors:
        raise ValidationError(errors)

    # Create and validate the resource
    new_resource = resource_type(*attrs)
    if d:
        new_resource.extra_attrs(d)
    if full_clean:
        new_resource.full_clean()

    return new_resource


def build_object_graph(d: Union[Dict[str, Any], List[Dict[str, Any]], Any], resource: ResourceUnion=None,
                       full_clean: bool=True, copy_dict: bool=True,
                       default_to_not_supplied: bool=False) -> Union[R, List[R], Any]:
    """
    Generate an object graph from a dict

    :param d: Dictionary to build from

    :param resource: A resource type, resource name or list of resources and
        names to use as the base for creating a resource. If a list is
        supplied the first item will be used if a resource type is not
        supplied.

    :param full_clean: Perform a full clean once built; default is True

    :param copy_dict: Clone the dict before doing build; default is True

    :param default_to_not_supplied: If an value is not supplied keep the value
        as ``NotProvided``. This is used to support merging an updated value.

    :raises ValidationError: During building of the object graph and issues
        discovered are raised as a ValidationError.

    """
    if isinstance(d, dict):
        return create_resource_from_dict(d, resource, full_clean, copy_dict, default_to_not_supplied)

    if isinstance(d, list):
        return [build_object_graph(o, resource, full_clean, copy_dict, default_to_not_supplied) for o in d]

    return d
