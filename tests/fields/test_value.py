import pytest
import datetime
import uuid

from copy import deepcopy

from odin import NotProvided
from odin.fields import *
from odin.utils.datetimeutil import utc, FixedTimezone
# from odin.fields.virtual import VirtualField
from odin.validators import MinValueValidator, MaxValueValidator, MaxLengthValidator, RegexValidator
from odin.exceptions import ValidationError


class ObjectValue(object):
    pass


class ValidatorTest(object):
    message = 'Default message'
    code = 'test_code'

    def __init__(self, fail, *params):
        self.fail = fail
        self.params = params

    def __call__(self, value):
        if self.fail:
            raise ValidationError(code=self.code, message=self.message, params=self.params)


class FieldTest(ValueField):
    def to_python(self, value):
        return value


class DynamicTypeNameFieldTest(IntegerField):
    @staticmethod
    def data_type_name(instance):
        return "Foo"


class TestField(object):
    def test_error_messages_no_overrides(self):
        target = FieldTest()

        assert {
            'invalid_choice': 'Value {!r} is not a valid choice.',
            'null': 'This field cannot be null.',
            'required': 'This field is required.',
        } == target.error_messages

    def test_error_messages_override_add(self):
        target = FieldTest(error_messages={
            'null': 'Override',
            'other': 'Other Value',
        })

        assert {
            'invalid_choice': 'Value {!r} is not a valid choice.',
            'null': 'Override',
            'required': 'This field is required.',
            'other': 'Other Value',
        } == target.error_messages

    def test_set_attributes_from_name(self):
        target = FieldTest()
        target.set_attributes_from_name("test_name")

        assert "test_name" == target.name
        assert "test_name" == target.attname
        assert "test name" == target.verbose_name
        assert "test names" == target.verbose_name_plural

    def test_set_attributes_from_name__with_name(self):
        target = FieldTest(name="init_name")
        target.set_attributes_from_name("test_name")

        assert "init_name" == target.name
        assert "test_name" == target.attname
        assert "init name" == target.verbose_name
        assert "init names" == target.verbose_name_plural

    def test_set_attributes_from_name_with__verbose_name(self):
        target = FieldTest(verbose_name="init Verbose Name")
        target.set_attributes_from_name("test_name")

        assert "test_name" == target.name
        assert "test_name" == target.attname
        assert "init Verbose Name" == target.verbose_name
        assert "init Verbose Names" == target.verbose_name_plural

    def test_has_default(self):
        target = FieldTest()

        assert not target.has_default

    def test_has_default_supplied(self):
        target = FieldTest(default="123")

        assert target.has_default

    def test_get_default(self):
        target = FieldTest()

        assert target.get_default() is None

    def test_get_default_supplied(self):
        target = FieldTest(default="123")

        assert "123" == target.get_default()

    def test_get_default_callable(self):
        target = FieldTest(default=lambda: "321")

        assert "321" == target.get_default()

    def test_value_from_object(self):
        target = FieldTest()
        target.set_attributes_from_name("test_name")

        an_obj = ObjectValue()
        setattr(an_obj, "test_name", "test_value")

        actual = target.value_from_object(an_obj)
        assert "test_value" == actual

    def test__repr(self):
        target = FieldTest()
        assert "<tests.fields.test_value.FieldTest>" == repr(target)
        target.set_attributes_from_name("eek")
        assert "<tests.fields.test_value.FieldTest: name='eek'>" == repr(target)

    def test__deep_copy(self):
        field = FieldTest(name="Test")
        target_copy = deepcopy(field)
        target_assign = field
        assert field is target_assign
        assert field is not target_copy
        assert field.name == target_copy.name

    def test_run_validators_and_override_validator_message(self):
        target = FieldTest(error_messages={'test_code': 'Override message'}, validators=[ValidatorTest(True)])

        with pytest.raises(ValidationError) as v:
            target.run_validators("Placeholder")

        assert v.value.messages[0] == 'Override message'

    def test_run_validators_and_override_validator_message_with_params(self):
        target = FieldTest(error_messages={'test_code': 'Override message: {}'},
                           validators=[ValidatorTest(True, "123")])

        with pytest.raises(ValidationError) as v:
            target.run_validators("Placeholder")

        assert v.value.messages[0] == 'Override message: 123'

    def test_clean_uses_default_if_value_is_not_provided_is_true(self):
        target = FieldTest(use_default_if_not_provided=True, default='foo')
        actual = target.clean(NotProvided)
        assert 'foo' == actual

    def test_clean_uses_default_if_value_is_not_provided_is_false(self):
        # Need to allow None as the if use_default_if_not_provided is false NOT_PROVIDED evaluates to None.
        target = FieldTest(use_default_if_not_provided=False, default='foo', null=True)
        actual = target.clean(NotProvided)
        assert actual is None


class TestFields:
    @staticmethod
    def assert_validator_in(validator_class, validators):
        """
        Assert that the specified validator is in the validation list.
        :param validator_class:
        :param validators:
        """
        for v in validators:
            if isinstance(v, validator_class):
                return
        raise AssertionError("Validator %r was not found in list of validators." % validator_class)

    @staticmethod
    def assert_validator_not_in(validator_class, validators):
        """
        Assert that the specified validator is not in the validation list.
        :param validator_class:
        :param validators:
        """
        for v in validators:
            if isinstance(v, validator_class):
                raise AssertionError("Validator %r was found in list of validators." % validator_class)

    # String ########################################################

    def test_string(self):
        f = String()
        assert f.max_length is None
        self.assert_validator_not_in(MaxLengthValidator, f.validators)

        f = String(max_length=10)
        assert f.max_length == 10
        self.assert_validator_in(MaxLengthValidator, f.validators)

    @pytest.mark.parametrize('field, value, expected', (
        (String(), '1', '1'),
        (String(), 'eek', 'eek'),
        (String(null=True), '1', '1'),
        (String(null=True), None, None),
        (String(null=True), '', ''),
        (String(null=True, empty=True), '', ''),
        (String(empty=True), '', ''),
        (String(max_length=10), '123456', '123456'),
    ))
    def test_string__success(self, field, value, expected):
        assert field.clean(value) == expected

    @pytest.mark.parametrize('field, value', (
        (String(), None),
        (String(), ''),
        (String(null=True, empty=False), ''),
        (String(empty=False), ''),
        (String(max_length=10), '1234567890a'),
    ))
    def test_string__failure(self, field, value):
        with pytest.raises(ValidationError):
            field.clean(value)

    @pytest.mark.parametrize('field, empty_value', (
        (String(), False),
        (String(null=True), True),
        (String(null=False), False),
        (String(null=True, empty=True), True),
        (String(null=False, empty=True), True),
        (String(null=True, empty=False), False),
        (String(null=False, empty=False), False),
    ))
    def test_string__handling_of_null_empty(self, field, empty_value):
        assert field.empty == empty_value

    # Boolean #######################################################

    @pytest.mark.parametrize(('field', 'value', 'expected'), (
        (Boolean(), True, True),
        (Boolean(), 1, True),
        (Boolean(), 'Yes', True),
        (Boolean(), 'true', True),
        (Boolean(), 'T', True),
        (Boolean(), '1', True),
        (Boolean(), 'TRUE', True),
        (Boolean(), False, False),
        (Boolean(), 0, False),
        (Boolean(), 'No', False),
        (Boolean(), 'false', False),
        (Boolean(), 'FALSE', False),
        (Boolean(), 'F', False),
        (Boolean(), '0', False),
        (Boolean(null=True), None, None),
    ))
    def test_boolean__success(self, field, value, expected):
        assert field.clean(value) == expected

    @pytest.mark.parametrize(('field', 'value'), (
        (Boolean(), None),
        (Boolean(), ''),
        (Boolean(), 'Awesome!'),
    ))
    def test_boolean__failure(self, field, value):
        with pytest.raises(ValidationError):
            field.clean(value)

    # Integer #######################################################

    @pytest.mark.parametrize('field, value, expected', (
        (Integer(), 123, 123),
        (Integer(), '123', 123),
        (Integer(), 123.5, 123),
        (Integer(null=True), 123, 123),
        (Integer(null=True), None, None),
    ))
    def test_integer__valid(self, field, value, expected):
        assert field.clean(value) == expected

    @pytest.mark.parametrize('field, value', (
        (Integer(), None),
        (Integer(), 'abc'),
        (Integer(min_value=50), 42),
        (Integer(max_value=50), 69),
    ))
    def test_integer__invalid(self, field, value):
        with pytest.raises(ValidationError):
            field.clean(value)

    def test_integer__validators(self):
        f = Integer()
        self.assert_validator_not_in(MinValueValidator, f.validators)
        self.assert_validator_not_in(MaxValueValidator, f.validators)

        f = Integer(min_value=42)
        self.assert_validator_in(MinValueValidator, f.validators)
        self.assert_validator_not_in(MaxValueValidator, f.validators)

        f = Integer(max_value=69)
        self.assert_validator_not_in(MinValueValidator, f.validators)
        self.assert_validator_in(MaxValueValidator, f.validators)

        f = Integer(min_value=42, max_value=69)
        self.assert_validator_in(MinValueValidator, f.validators)
        self.assert_validator_in(MaxValueValidator, f.validators)

    # Float #########################################################

    @pytest.mark.parametrize('field, value, expected', (
        (Float(), 123, 123),
        (Float(), 123.4, 123.4),
        (Float(), '123.4', 123.4),
        (Float(), 123, 123.0),
        (Float(null=True), 123.4, 123.4),
        (Float(null=True), None, None),
    ))
    def test_float__valid(self, field, value, expected):
        assert field.clean(value) == expected

    @pytest.mark.parametrize('field, value', (
        (Float(), None),
        (Float(), 'abc'),
        (Float(min_value=50.1), 42.1),
        (Float(max_value=50.1), 69.2),
    ))
    def test_float__invalid(self, field, value):
        with pytest.raises(ValidationError):
            field.clean(value)

    def test_float__validators(self):
        f = Float()
        self.assert_validator_not_in(MinValueValidator, f.validators)
        self.assert_validator_not_in(MaxValueValidator, f.validators)

        f = Float(min_value=42.1)
        self.assert_validator_in(MinValueValidator, f.validators)
        self.assert_validator_not_in(MaxValueValidator, f.validators)

        f = Float(max_value=69.2)
        self.assert_validator_not_in(MinValueValidator, f.validators)
        self.assert_validator_in(MaxValueValidator, f.validators)

        f = Float(min_value=42.1, max_value=69.2)
        self.assert_validator_in(MinValueValidator, f.validators)
        self.assert_validator_in(MaxValueValidator, f.validators)

    # Date/Time Fields ##############################################

    @pytest.mark.parametrize('field,value,expected', (
        (Date(), '2013-11-24', datetime.date(2013, 11, 24)),
        (Date(), datetime.date(2013, 11, 24), datetime.date(2013, 11, 24)),
        (Date(), datetime.datetime(2013, 11, 24, 1, 14), datetime.date(2013, 11, 24)),
        (Date(null=True), None, None),

        (Time(), '18:43:00.000Z', datetime.time(18, 43, tzinfo=utc)),
        (Time(), datetime.time(18, 43, tzinfo=utc), datetime.time(18, 43, tzinfo=utc)),
        (Time(null=True), None, None),

        (DateTime(), '2013-11-24T18:43:00.000Z', datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),
        (DateTime(), '2013-11-24 18:43:00.000Z', datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),
        (DateTime(), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),
        (DateTime(null=True), None, None),
    ))
    def test_date_time__success(self, field, value, expected):
        assert field.clean(value) == expected

    @pytest.mark.parametrize('field,value', (
        (Date(), None),
        (Date(), 'abc'),
        (Date(), 123),

        (Time(), None),
        (Time(), 'abc'),
        (Time(), 123),

        (DateTime(), None),
        (DateTime(), 'abc'),
        (DateTime(), 123),
    ))
    def test_date_time__failure(self, field, value):
        pytest.raises(ValidationError, field.clean, value)

    @pytest.mark.parametrize('field, value ,expected', (
        (Date(), datetime.date(2013, 11, 24), '2013-11-24'),

        (Time(), datetime.time(12, 44, 12, 12), '12:44:12.000012'),
        (Time(), datetime.time(12, 44, 12, 12, utc), '12:44:12.000012+00:00'),

        (DateTime(), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=FixedTimezone.from_hours_minutes(10)), '2013-11-24T18:43:00+10:00'),
        (DateTime(), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc), '2013-11-24T18:43:00+00:00'),
    ))
    def test_date_time__as_string(self, field, value, expected):
        assert field.as_string(value) == expected

    # Naive Date/Time Fields ########################################

    @pytest.mark.parametrize('target, value, expected', (
        (NaiveTime(ignore_timezone=False), '18:43:00.000Z', datetime.time(18, 43, tzinfo=utc)),
        (NaiveTime(ignore_timezone=False), '18:43:00.000Z', datetime.time(18, 43, tzinfo=utc)),
        (NaiveTime(ignore_timezone=False), datetime.time(18, 43, tzinfo=utc), datetime.time(18, 43, tzinfo=utc)),

        (NaiveTime(ignore_timezone=False, null=True), None, None),
        (NaiveTime(ignore_timezone=False, null=True), '18:43:00.000Z', datetime.time(18, 43, tzinfo=utc)),
        (NaiveTime(ignore_timezone=False, null=True), '18:43:00.000Z', datetime.time(18, 43, tzinfo=utc)),
        (NaiveTime(ignore_timezone=False, null=True), datetime.time(18, 43, tzinfo=utc), datetime.time(18, 43, tzinfo=utc)),

        (NaiveTime(ignore_timezone=True), '18:43:00.000Z', datetime.time(18, 43)),
        (NaiveTime(ignore_timezone=True), '18:43:00.000Z', datetime.time(18, 43)),
        (NaiveTime(ignore_timezone=True), datetime.time(18, 43, tzinfo=utc), datetime.time(18, 43)),

        (NaiveDateTime(ignore_timezone=False), '2013-11-24T18:43:00.000Z', datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),
        (NaiveDateTime(ignore_timezone=False), '2013-11-24 18:43:00.000Z', datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),
        (NaiveDateTime(ignore_timezone=False), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),

        (NaiveDateTime(ignore_timezone=False, null=True), None, None),
        (NaiveDateTime(ignore_timezone=False, null=True), '2013-11-24T18:43:00.000Z', datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),
        (NaiveDateTime(ignore_timezone=False, null=True), '2013-11-24 18:43:00.000Z', datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),
        (NaiveDateTime(ignore_timezone=False, null=True), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),

        (NaiveDateTime(ignore_timezone=True), '2013-11-24T18:43:00.000Z', datetime.datetime(2013, 11, 24, 18, 43)),
        (NaiveDateTime(ignore_timezone=True), '2013-11-24 18:43:00.000Z', datetime.datetime(2013, 11, 24, 18, 43)),
        (NaiveDateTime(ignore_timezone=True), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc), datetime.datetime(2013, 11, 24, 18, 43)),
    ))
    def test_naive_date_time__success(self, target, value, expected):
        assert target.clean(value) == expected

    @pytest.mark.parametrize('target, value', (
        (NaiveTime(ignore_timezone=False), None),
        (NaiveTime(ignore_timezone=False), 'abc'),
        (NaiveTime(ignore_timezone=False), 123),

        (NaiveTime(ignore_timezone=False, null=True), 'abc'),
        (NaiveTime(ignore_timezone=False, null=True), 123),

        (NaiveTime(ignore_timezone=True), None),
        (NaiveTime(ignore_timezone=True), 'abc'),
        (NaiveTime(ignore_timezone=True), 123),

        (NaiveDateTime(ignore_timezone=False), None),
        (NaiveDateTime(ignore_timezone=False), 'abc'),
        (NaiveDateTime(ignore_timezone=False), 123),

        (NaiveDateTime(ignore_timezone=False, null=True), 'abc'),
        (NaiveDateTime(ignore_timezone=False, null=True), 123),

        (NaiveDateTime(ignore_timezone=True), None),
        (NaiveDateTime(ignore_timezone=True), 'abc'),
        (NaiveDateTime(ignore_timezone=True), 123),

    ))
    def test_naive_date_time__failure(self, target, value):
        pytest.raises(ValidationError, target.clean, value)

    @pytest.mark.parametrize(('target', 'value', 'expected'), (
        (NaiveTime(ignore_timezone=False), datetime.time(18, 43, tzinfo=utc), datetime.time(18, 43, tzinfo=utc)),
        (NaiveTime(ignore_timezone=True), datetime.time(18, 43, tzinfo=utc), datetime.time(18, 43)),

        (NaiveDateTime(ignore_timezone=False), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc)),
        (NaiveDateTime(ignore_timezone=True), datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc), datetime.datetime(2013, 11, 24, 18, 43)),
    ))
    def test_naivetimefield__prepare(self, target, value, expected):
        assert target.prepare(value) == expected

    # HttpDateTime ##################################################

    def test_httpdatetimefield_1(self):
        f = HttpDateTime()
        pytest.raises(ValidationError, f.clean, None)
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert datetime.datetime(2012, 8, 29, 17, 12, 58, tzinfo=utc) == f.clean('Wed Aug 29 17:12:58 +0000 2012')
        assert datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc) == f.clean(
            datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc))

    def test_httpdatetimefield_2(self):
        f = HttpDateTime(null=True)
        assert f.clean(None) is None
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert datetime.datetime(2012, 8, 29, 17, 12, 58, tzinfo=utc) == f.clean('Wed Aug 29 17:12:58 +0000 2012')
        assert datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc) == f.clean(
            datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc))

    # TimeStamp #####################################################

    def test_timestampfield_1(self):
        f = TimeStamp()
        pytest.raises(ValidationError, f.clean, None)
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 'Wed Aug 29 17:12:58 +0000 2012')
        assert datetime.datetime(1970, 1, 1, 0, 2, 3, tzinfo=utc) == f.clean(123)
        assert datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc) == f.clean(
            datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc))

    def test_timestampfield_2(self):
        f = TimeStamp(null=True)
        assert f.clean(None) is None
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 'Wed Aug 29 17:12:58 +0000 2012')
        assert datetime.datetime(1970, 1, 1, 0, 2, 3, tzinfo=utc) == f.clean(123)
        assert datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc) == f.clean(
            datetime.datetime(2013, 11, 24, 18, 43, tzinfo=utc))

    def test_timestampfield_3(self):
        f = TimeStamp()
        assert f.prepare(None) is None
        assert 123 == f.prepare(datetime.datetime(1970, 1, 1, 0, 2, 3, tzinfo=utc))
        assert 123 == f.prepare(123)
        assert 123 == f.prepare(
            datetime.datetime(1970, 1, 1, 10, 2, 3, tzinfo=FixedTimezone.from_hours_minutes(10)))

    # Dict ##########################################################

    def test_dictfield_1(self):
        f = Dict()
        pytest.raises(ValidationError, f.clean, None)
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert {} == f.clean({})
        assert {'foo': 'bar'} == f.clean({'foo': 'bar'})
        assert f.default == dict

    def test_dictfield_2(self):
        f = Dict(null=True)
        assert None == f.clean(None)
        assert {} == f.clean({})
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert {'foo': 'bar'} == f.clean({'foo': 'bar'})

    # List ##########################################################

    def test_arrayfield_1(self):
        f = List()
        pytest.raises(ValidationError, f.clean, None)
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert [] == f.clean([])
        assert ['foo', 'bar'], f.clean(['foo' == 'bar'])
        assert ['foo', 'bar', '$', 'eek'], f.clean(['foo', 'bar', '$' == 'eek'])
        assert f.default == list

    def test_arrayfield_2(self):
        f = List(null=True)
        assert None == f.clean(None)
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert [] == f.clean([])
        assert ['foo', 'bar'], f.clean(['foo' == 'bar'])
        assert ['foo', 'bar', '$', 'eek'], f.clean(['foo', 'bar', '$' == 'eek'])

    # TypedList #####################################################

    def test_typedlistfield_1(self):
        f = TypedList(Integer())
        assert "List<Integer>" == f.data_type_name(f)
        pytest.raises(ValidationError, f.clean, None)
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert [] == f.clean([])
        pytest.raises(ValidationError, f.clean, ['foo', 'bar'])
        assert [1, 2, 3], f.clean([1, 2 == 3])
        assert f.default == list

    def test_typedlistfield_2(self):
        f = TypedList(Integer(), null=True)
        assert "List<Integer>" == f.data_type_name(f)
        assert None == f.clean(None)
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert [] == f.clean([])
        pytest.raises(ValidationError, f.clean, ['foo', 'bar'])
        assert [1, 2, 3], f.clean([1, 2 == 3])

    def test_typed_list_field_dynamic_type_name(self):
        f = TypedList(DynamicTypeNameFieldTest(), null=True)
        assert "List<Foo>" == f.data_type_name(f)

    # TypedDict #####################################################

    def test_typeddictfield_1(self):
        f = TypedDict(Integer())
        assert "Dict<String, Integer>" == f.data_type_name(f)
        pytest.raises(ValidationError, f.clean, None)
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert {} == f.clean({})
        pytest.raises(ValidationError, f.clean, {'foo': 'bar'})
        assert {'foo': 1} == f.clean({'foo': 1})

    def test_typeddictfield_2(self):
        f = TypedDict(Integer(), null=True)
        assert "Dict<String, Integer>" == f.data_type_name(f)
        assert None == f.clean(None)
        pytest.raises(ValidationError, f.clean, 'abc')
        pytest.raises(ValidationError, f.clean, 123)
        assert {} == f.clean({})
        pytest.raises(ValidationError, f.clean, {'foo': 'bar'})
        assert {'foo': 1} == f.clean({'foo': 1})

    def test_typeddictfield_3(self):
        f = TypedDict(String(), Integer(), null=True)
        assert "Dict<Integer, String>" == f.data_type_name(f)
        pytest.raises(ValidationError, f.clean, {'foo': 'bar'})
        assert {1: 'foo'} == f.clean({1: 'foo'})

    def test_typeddictfield_nested_typed_array(self):
        f = TypedDict(TypedList(String()))
        assert "Dict<String, List<String>>" == f.data_type_name(f)
        assert {} == f.clean({})
        pytest.raises(ValidationError, f.clean, {'foo': 'bar'})
        assert {'foo': ['bar', 'eek']}, f.clean({'foo': ['bar' == 'eek']})

    def test_typeddictfield_validate(self):
        f = TypedDict(
            Integer(min_value=5),
            String(max_length=5, choices=[
                ('foo', 'Foo'),
                ('bad_value', 'Bad Value'),
            ])
        )
        assert "Dict<String, Integer>" == f.data_type_name(f)
        pytest.raises(ValidationError, f.clean, {None: 6})
        pytest.raises(ValidationError, f.clean, {'bad_value': 6})
        pytest.raises(ValidationError, f.clean, {'bar': 6})
        pytest.raises(ValidationError, f.clean, {'foo': None})
        pytest.raises(ValidationError, f.clean, {'foo': 2})

    def test_typed_dict_field_dynamic_type_name(self):
        f = TypedDict(
            DynamicTypeNameFieldTest(),
            DynamicTypeNameFieldTest(),
        )
        assert "Dict<Foo, Foo>" == f.data_type_name(f)

    # Formatted String Fields #######################################

    @pytest.mark.parametrize('field, value, expected', (
        (Email(), 'foo@example.company', 'foo@example.company'),
        (Email(null=True), None, None),

        (Url(), 'http://www.github.com', 'http://www.github.com'),
        (Url(null=True), None, None),

        (IPv4(), '127.0.0.1', '127.0.0.1'),
        (IPv4(null=True), None, None),

        (IPv6(), '::1', '::1'),
        (IPv6(), '1:2:3:4:5:6:7:8', '1:2:3:4:5:6:7:8'),
        (IPv6(null=True), None, None),

        (IPv46(), '127.0.0.1', '127.0.0.1'),
        (IPv46(), '::1', '::1'),
        (IPv46(), '1:2:3:4:5:6:7:8', '1:2:3:4:5:6:7:8'),
        (IPv46(null=True), None, None),

        (UUID(null=True), None, None),
    ))
    def test_formatted_strings__success(self, field, value, expected):
        assert field.clean(value) == expected

    @pytest.mark.parametrize('field, value', (
        (Email(), None),
        (Email(), 'fooexample.com'),
        (Email(), 'foo@example.com.'),

        (Url(), None),
        (Url(), 'github.com.'),

        (IPv4(), None),
        (IPv4(), 'abc'),
        (IPv4(), '192.16..1'),

        (IPv6(), None),
        (IPv6(), 'abc'),

        (IPv46(), None),
        (IPv46(), 'abc'),

        (UUID(), None),
        (UUID(), -1),
        (UUID(), b'\254'),
        (UUID(), b'\255'),
        (UUID(), (1, 2, 3, 4, 5)),
        (UUID(), [1, 2, 3, 4, 5]),
        (UUID(), (-1, 2, 2, 2, 2, 2)),
        (UUID(), [-1, 2, 2, 2, 2, 2]),
        (UUID(), (2, -1, 2, 2, 2, 2)),
        (UUID(), [2, -1, 2, 2, 2, 2]),
        (UUID(), "sometext"),
        (UUID(), "01010101-0101-0101-0101-01010101010"),
    ))
    def test_formatted_strings__failure(self, field, value):
        with pytest.raises(ValidationError):
            field.clean(value)

    # UUID ##########################################################

    @pytest.mark.parametrize('value', (
        uuid.uuid1(),
        uuid.uuid3(uuid.uuid4(), 'name'),
        uuid.uuid4(),
        uuid.uuid5(uuid.uuid4(), 'name'),
    ))
    def test_uuid_field_with_uuid_objects(self, value):
        assert UUID().clean(value) == value

    @pytest.mark.parametrize('value', (
        uuid.uuid1().bytes,
        uuid.uuid3(uuid.uuid4(), 'name').bytes,
        uuid.uuid4().bytes,
        uuid.uuid5(uuid.uuid4(), 'name').bytes,
    ), ids=('bytes-uuid1', 'bytes-uuid3', 'bytes-uuid4', 'bytes-uuid5',))
    def test_uuid_field_with_16_bytes_sequence(self, value):
        assert UUID().clean(value) == uuid.UUID(bytes=value)

    @pytest.mark.parametrize('value', (
        str(uuid.uuid1()).encode('utf-8'),
        str(uuid.uuid3(uuid.uuid4(), 'name')).encode('utf-8'),
        str(uuid.uuid4()).encode('utf-8'),
        str(uuid.uuid5(uuid.uuid4(), 'name')).encode('utf-8'),
    ))
    def test_uuid_field_with_bytes(self, value):
        assert UUID().clean(value) == uuid.UUID(value.decode('utf-8'))

    @pytest.mark.parametrize('value', (
        str(uuid.uuid1()),
        str(uuid.uuid3(uuid.uuid4(), 'name')),
        str(uuid.uuid4()),
        str(uuid.uuid5(uuid.uuid4(), 'name')),
    ))
    def test_uuid_field_with_string(self, value):
        assert UUID().clean(value) == uuid.UUID(value)

    @pytest.mark.parametrize('value', range(4))
    def test_uuid_field_with_int(self, value):
        assert UUID().clean(value) == uuid.UUID(int=value)

    def test_uuid_field_non_str_value(self):
        some_uuid = uuid.uuid4()

        class SomeObject:
            def __str__(self):
                return str(some_uuid)

        assert UUID().clean(SomeObject()) == some_uuid

    def test_uuid_field_invalid_non_str_value(self):
        class SomeObject(object):
            def __str__(self):
                return "sometext"

        with pytest.raises(ValidationError):
            UUID().clean(SomeObject())

    def test_uuid_field__none(self):
        f = UUID(null=True)
        assert f.clean(None) is None
