import odin
import enum

# from odin.fields.virtual import CalculatedField
# from odin.mapping.helpers import sum_fields


class Author(odin.Resource):
    name = odin.String()

    class Meta:
        name_space = None


class Publisher(odin.Resource):
    name = odin.String()

    class Meta:
        name_space = None


class LibraryBook(odin.Resource):
    class Meta:
        abstract = True
        name_space = "library"


class Book(LibraryBook):
    class Meta:
        key_field_name = 'isbn'

    title = odin.String()
    isbn = odin.String()
    num_pages = odin.Integer()
    rrp = odin.Float(default=20.4, use_default_if_not_provided=True)
    fiction = odin.Boolean(is_attribute=True)
    genre = odin.String(choices=(
        ('sci-fi', 'Science Fiction'),
        ('fantasy', 'Fantasy'),
        ('biography', 'Biography'),
        ('others', 'Others'),
        ('computers-and-tech', 'Computers & technology'),
    ))
    # published = odin.TypedArrayField(odin.DateTimeField())
    # authors = odin.ArrayOf(Author, use_container=True)
    # publisher = odin.DictAs(Publisher, null=True)

    def __eq__(self, other):
        if other:
            return vars(self) == vars(other)
        return False


book = Book()


class From(enum.Enum):
    Dumpster = 'dumpster'
    Shop = 'shop'
    Ebay = 'ebay'


class IdentifiableBook(Book):
    id = odin.UUID()
    purchased_from = odin.Enum(From)


# class BookProxy(odin.ResourceProxy):
#     class Meta:
#         resource = Book
#         include = ('title', 'isbn', 'num_pages', 'rrp')
#         readonly = ('rrp',)
#         verbose_name = 'Book Summary'
#         namespace = 'the.other.library'
#
#     @property
#     def expensive(self):
#         return self.rrp > 200


class Subscriber(odin.Resource):
    name = odin.String()
    address = odin.String()

    def __eq__(self, other):
        if other:
            return self.name == other.name and self.address == other.address


class Library(odin.Resource):
    name = odin.String()
#     books = odin.ArrayOf(LibraryBook)
#     subscribers = odin.ArrayOf(Subscriber, null=True)
    book_count = odin.Calculated(lambda o: len(o.books))
#
#     class Meta:
#         name_space = None


class OldBook(LibraryBook):
    name = odin.String(key=True)
    num_pages = odin.Integer()
    price = odin.Float()
    genre = odin.String(key=True, choices=(
        ('sci-fi', 'Science Fiction'),
        ('fantasy', 'Fantasy'),
        ('biography', 'Biography'),
        ('others', 'Others'),
        ('computers-and-tech', 'Computers & technology'),
    ))
    published = odin.DateTime()
    # author = odin.ObjectAs(Author)
    # publisher = odin.ObjectAs(Publisher)


# class OldBookToBookMapping(odin.Mapping):
#     from_obj = OldBook
#     to_obj = Book
#
#     exclude_fields = ('',)
#
#     mappings = (
#         ('name', None, 'title'),
#     )


class ChildResource(odin.Resource):
    name = odin.String()


class FromResource(odin.Resource):
    # Auto matched
    title = odin.String()
    count = odin.String()
    # child = odin.ObjectAs(ChildResource)
    # children = odin.ArrayOf(ChildResource)
    # Excluded
    excluded1 = odin.Float()
    # Mappings
    from_field1 = odin.String()
    from_field2 = odin.String()
    from_field3 = odin.Integer()
    from_field4 = odin.Integer()
    same_but_different = odin.String()
    # Custom mappings
    from_field_c1 = odin.String()
    from_field_c2 = odin.String()
    from_field_c3 = odin.String()
    from_field_c4 = odin.String()
    not_auto_c5 = odin.String()
    comma_separated_string = odin.String()
    # Virtual fields
    constant_field = odin.Constant(value=10)


class InheritedResource(FromResource):
    # Additional fields
    name = odin.String()
    # Additional virtual fields
    calculated_field = odin.Calculated(lambda obj: 11)


class MultiInheritedResource(InheritedResource, FromResource):
    pass


class ToResource(odin.Resource):
    # Auto matched
    title = odin.String()
    count = odin.Integer()
    # child = odin.ObjectAs(ChildResource)
    # children = odin.ArrayOf(ChildResource)
    # Excluded
    excluded1 = odin.Float()
    # Mappings
    to_field1 = odin.String()
    to_field2 = odin.Integer()
    to_field3 = odin.Integer()
    same_but_different = odin.String()
    # Custom mappings
    to_field_c1 = odin.String()
    to_field_c2 = odin.String()
    to_field_c3 = odin.String()
    not_auto_c5 = odin.String()
    # array_string = odin.TypedArray(odin.StringField())
    assigned_field = odin.String()


# class FromToMapping(odin.Mapping):
#     from_obj = FromResource
#     to_obj = ToResource
#
#     exclude_fields = ('excluded1',)
#
#     mappings = (
#         ('from_field1', None, 'to_field1'),
#         ('from_field2', int, 'to_field2'),
#         (('from_field3', 'from_field4'), sum_fields, 'to_field3'),
#         ('from_field1', None, 'same_but_different'),
#     )
#
#     @odin.map_field(from_field=('from_field_c1', 'from_field_c2', 'from_field_c3'), to_field='to_field_c1')
#     def multi_to_one(self, *values):
#         return '-'.join(values)
#
#     @odin.map_field(from_field='from_field_c4', to_field=('to_field_c2', 'to_field_c3'))
#     def one_to_multi(self, value):
#         return value.split('-', 1)
#
#     @odin.map_field
#     def not_auto_c5(self, value):
#         return value.upper()
#
#     @odin.map_list_field(to_field='array_string')
#     def comma_separated_string(self, value):
#         return value.split(',')
#
#     @odin.assign_field
#     def assigned_field(self):
#         return 'Foo'
