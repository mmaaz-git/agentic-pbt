import pickle
import enum
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
import sqlalchemy.types as types
import pytest


@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.binary(),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(), st.integers(), max_size=5),
    st.tuples(st.integers(), st.text()),
))
def test_pickletype_round_trip(value):
    """Test that PickleType correctly serializes and deserializes values."""
    pt = types.PickleType()
    
    # Create a mock dialect that doesn't have native processors
    class MockDialect:
        dbapi = None
        returns_native_bytes = False
    
    dialect = MockDialect()
    
    # Get the bind processor (serializes)
    bind_proc = pt.bind_processor(dialect)
    
    # Get the result processor (deserializes)  
    result_proc = pt.result_processor(dialect, None)
    
    # Perform round-trip
    if bind_proc:
        serialized = bind_proc(value)
    else:
        serialized = value
        
    if result_proc:
        deserialized = result_proc(serialized)
    else:
        deserialized = serialized
    
    # The round-trip should preserve the value
    if value is None:
        assert deserialized is None
    else:
        assert deserialized == value


@given(st.one_of(
    st.just(None),
    st.just(True),
    st.just(False),
    st.just(0),
    st.just(1),
    st.integers(min_value=2),
    st.integers(max_value=-1),
    st.floats(),
    st.text(),
))
def test_boolean_strict_validation(value):
    """Test that Boolean type enforces strict validation rules."""
    bt = types.Boolean()
    
    # The _strict_as_bool method should only accept None, True, False, 0, 1
    valid_values = {None, True, False, 0, 1}
    
    if value in valid_values:
        # Should not raise
        result = bt._strict_as_bool(value)
        assert result == value
    else:
        # Should raise TypeError or ValueError
        with pytest.raises((TypeError, ValueError)):
            bt._strict_as_bool(value)


@given(st.text())
def test_enum_validation(value):
    """Test that Enum type validates values against defined enums."""
    # Create an enum with specific values
    enum_values = ['red', 'green', 'blue']
    et = types.Enum(*enum_values)
    
    # The _object_value_for_elem should validate values
    if value in enum_values:
        result = et._object_value_for_elem(value)
        assert result == value
    else:
        with pytest.raises(LookupError):
            et._object_value_for_elem(value)


@given(st.text())
def test_string_literal_escaping(value):
    """Test that String type correctly escapes quotes in literal processor."""
    st_type = types.String()
    
    # Create a mock dialect
    class MockDialect:
        class IdentifierPreparer:
            _double_percents = False
        
        identifier_preparer = IdentifierPreparer()
        statement_compiler = lambda self, d, s: None
    
    dialect = MockDialect()
    
    # Get the literal processor
    literal_proc = st_type.literal_processor(dialect)
    
    if literal_proc:
        processed = literal_proc(value)
        
        # Check that single quotes are escaped by doubling
        expected = "'" + value.replace("'", "''") + "'"
        assert processed == expected


class MyEnum(enum.Enum):
    """Test enum for Enum type with Python enum class."""
    FIRST = 'first'
    SECOND = 'second'
    THIRD = 'third'


@given(st.sampled_from(list(MyEnum)))
def test_enum_with_class_round_trip(enum_value):
    """Test that Enum type with Python enum class preserves enum identity."""
    et = types.Enum(MyEnum)
    
    # The bind processor should convert to string
    # The result processor should convert back to enum
    
    # Simulate bind processing (enum -> string for DB)
    db_value = et._db_value_for_elem(enum_value)
    assert isinstance(db_value, str)
    assert db_value == enum_value.name
    
    # Simulate result processing (string from DB -> enum)
    result = et._object_value_for_elem(db_value)
    assert result is enum_value


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.decimals(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
))
def test_numeric_decimal_conversion(value):
    """Test Numeric type's decimal conversion properties."""
    # Test with asdecimal=True (returns Decimal)
    nt_decimal = types.Numeric(asdecimal=True)
    
    # Test with asdecimal=False (returns float)
    nt_float = types.Numeric(asdecimal=False)
    
    class MockDialect:
        supports_native_decimal = False
    
    dialect = MockDialect()
    
    # Get result processors
    decimal_proc = nt_decimal.result_processor(dialect, None)
    float_proc = nt_float.result_processor(dialect, None)
    
    if isinstance(value, float):
        # When we have a float input
        if decimal_proc:
            result = decimal_proc(value)
            assert isinstance(result, Decimal)
        
        if float_proc:
            result = float_proc(value)  
            if result is not None:
                assert isinstance(result, float)


@given(st.lists(st.text()))
def test_enum_multiple_values_uniqueness(values):
    """Test that Enum correctly handles duplicate values."""
    assume(len(values) > 0)
    
    # Create enum with potentially duplicate values
    et = types.Enum(*values)
    
    # The enums property should contain the values
    # Note: Enum might deduplicate or preserve all values
    assert et.enums is not None
    assert len(et.enums) == len(values)
    
    # Each value in the enum should be accessible
    for value in et.enums:
        result = et._object_value_for_elem(value)
        assert result == value


@given(st.integers(min_value=0, max_value=10))
def test_pickletype_protocol_setting(protocol):
    """Test that PickleType respects the protocol parameter."""
    assume(protocol <= pickle.HIGHEST_PROTOCOL)
    
    pt = types.PickleType(protocol=protocol)
    assert pt.protocol == protocol
    
    class MockDialect:
        dbapi = None
        returns_native_bytes = False
    
    dialect = MockDialect()
    bind_proc = pt.bind_processor(dialect)
    
    # Test that the processor uses the specified protocol
    test_value = {'test': 'data'}
    if bind_proc:
        serialized = bind_proc(test_value)
        # Should be able to unpickle it
        deserialized = pickle.loads(serialized)
        assert deserialized == test_value