import pickle
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
import sqlalchemy.types as types
import pytest
import math


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_decimal_round_trip(value):
    """Test Float type's decimal conversion preserves value within precision."""
    # Test with asdecimal=True
    ft = types.Float(asdecimal=True, decimal_return_scale=10)
    
    class MockDialect:
        supports_native_decimal = False
        dbapi = None
        returns_native_bytes = False
    
    dialect = MockDialect()
    
    # Get processors
    bind_proc = ft.bind_processor(dialect)
    result_proc = ft.result_processor(dialect, None)
    
    # Simulate storing and retrieving
    if bind_proc:
        stored = bind_proc(value)
    else:
        stored = value
        
    if result_proc:
        retrieved = result_proc(stored)
    else:
        retrieved = stored
    
    # Check that the value is preserved within reasonable precision
    if value is not None and retrieved is not None:
        assert isinstance(retrieved, Decimal)
        # Check if values are close (accounting for float precision issues)
        assert math.isclose(float(retrieved), value, rel_tol=1e-9)


@given(st.lists(st.text(), min_size=1))
def test_enum_duplicate_values(values):
    """Test Enum with duplicate values."""
    # Create enum with potentially duplicate values
    et = types.Enum(*values)
    
    # The enum should store all values even if duplicated
    assert len(et.enums) == len(values)
    
    # All unique values should be retrievable
    for value in set(values):
        result = et._object_value_for_elem(value)
        assert result == value


@given(st.text())
def test_string_percent_escaping(text):
    """Test String type's handling of percent signs in literal processor."""
    st_type = types.String()
    
    class MockDialect:
        class IdentifierPreparer:
            _double_percents = True  # Enable percent doubling
        
        identifier_preparer = IdentifierPreparer()
        statement_compiler = lambda self, d, s: None
    
    dialect = MockDialect()
    
    literal_proc = st_type.literal_processor(dialect)
    
    if literal_proc:
        processed = literal_proc(text)
        
        # Check that both quotes and percents are escaped
        expected = text.replace("'", "''").replace("%", "%%")
        expected = f"'{expected}'"
        assert processed == expected


@given(st.integers())
def test_integer_literal_processor(value):
    """Test Integer type's literal processor."""
    it = types.Integer()
    
    class MockDialect:
        pass
    
    dialect = MockDialect()
    
    literal_proc = it.literal_processor(dialect)
    
    if literal_proc:
        processed = literal_proc(value)
        # Should convert to string representation
        assert processed == str(int(value))


@given(st.one_of(
    st.just(0),
    st.just(1),
    st.just(True),
    st.just(False),
))
def test_boolean_processor_chain(value):
    """Test Boolean type's complete processing chain."""
    bt = types.Boolean()
    
    class MockDialect:
        supports_native_boolean = False
        dbapi = None
        returns_native_bytes = False
    
    dialect = MockDialect()
    
    # Get processors
    bind_proc = bt.bind_processor(dialect)
    result_proc = bt.result_processor(dialect, None)
    
    # Process value through bind
    if bind_proc:
        bound = bind_proc(value)
    else:
        bound = value
    
    # For non-native boolean, should be converted to int
    if not dialect.supports_native_boolean and value is not None:
        assert isinstance(bound, int)
        assert bound in (0, 1)
    
    # Process back through result
    if result_proc:
        result = result_proc(bound)
    else:
        result = bound
    
    # Should get back a boolean
    if value is not None:
        assert isinstance(result, bool)
        assert result == bool(value)


@given(st.binary())
def test_pickletype_with_binary_data(data):
    """Test PickleType with binary data specifically."""
    # Binary data is a common use case for PickleType
    pt = types.PickleType()
    
    class MockDialect:
        dbapi = None
        returns_native_bytes = False
    
    dialect = MockDialect()
    
    bind_proc = pt.bind_processor(dialect)
    result_proc = pt.result_processor(dialect, None)
    
    # Process through bind
    if bind_proc:
        serialized = bind_proc(data)
    else:
        serialized = data
    
    # Process through result
    if result_proc:
        deserialized = result_proc(serialized)
    else:
        deserialized = serialized
    
    # Should get back the same binary data
    assert deserialized == data


class CustomPickler:
    """Custom pickler for testing PickleType with custom pickler."""
    @staticmethod
    def dumps(obj, protocol):
        return pickle.dumps(obj, protocol)
    
    @staticmethod
    def loads(data):
        return pickle.loads(data)


@given(st.dictionaries(st.text(), st.integers()))
def test_pickletype_custom_pickler(data):
    """Test PickleType with custom pickler."""
    custom_pickler = CustomPickler()
    pt = types.PickleType(pickler=custom_pickler)
    
    assert pt.pickler is custom_pickler
    
    class MockDialect:
        dbapi = None
        returns_native_bytes = False
    
    dialect = MockDialect()
    
    bind_proc = pt.bind_processor(dialect)
    result_proc = pt.result_processor(dialect, None)
    
    # Process through bind
    if bind_proc:
        serialized = bind_proc(data)
    else:
        serialized = data
    
    # Process through result  
    if result_proc:
        deserialized = result_proc(serialized)
    else:
        deserialized = serialized
    
    # Should get back the same data
    assert deserialized == data


@given(st.floats(min_value=0, max_value=1000))
def test_numeric_scale_and_precision(value):
    """Test Numeric type with specific scale and precision."""
    # Create Numeric with specific precision and scale
    nt = types.Numeric(precision=10, scale=2, asdecimal=True)
    
    # These parameters should be stored
    assert nt.precision == 10
    assert nt.scale == 2
    assert nt.asdecimal == True
    
    class MockDialect:
        supports_native_decimal = False
        dbapi = None
        returns_native_bytes = False
    
    dialect = MockDialect()
    
    result_proc = nt.result_processor(dialect, None)
    
    if result_proc and value is not None:
        result = result_proc(value)
        assert isinstance(result, Decimal)