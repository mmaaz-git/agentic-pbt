"""Property-based tests for sqlalchemy.exc module."""

import pickle
from hypothesis import given, strategies as st, assume
import sqlalchemy.exc as exc


# Property 1: Pickle round-trip for exceptions with custom __reduce__
@given(
    message=st.text(min_size=1, max_size=100),
    cycles=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
    edges=st.lists(st.tuples(st.text(max_size=10), st.text(max_size=10)), max_size=5),
    code=st.one_of(st.none(), st.text(min_size=1, max_size=10))
)
def test_circular_dependency_error_pickle_roundtrip(message, cycles, edges, code):
    """CircularDependencyError should maintain state through pickle/unpickle."""
    original = exc.CircularDependencyError(message, cycles, edges, code=code)
    
    # Pickle and unpickle
    pickled = pickle.dumps(original)
    restored = pickle.loads(pickled)
    
    # Check that all attributes are preserved
    assert restored.cycles == original.cycles
    assert restored.edges == original.edges
    assert restored.code == original.code
    assert str(restored) == str(original)


@given(
    message=st.text(min_size=1, max_size=100),
    table_name=st.text(min_size=1, max_size=50)
)
def test_no_referenced_table_error_pickle_roundtrip(message, table_name):
    """NoReferencedTableError should maintain state through pickle/unpickle."""
    original = exc.NoReferencedTableError(message, table_name)
    
    # Pickle and unpickle
    pickled = pickle.dumps(original)
    restored = pickle.loads(pickled)
    
    # Check that all attributes are preserved
    assert restored.table_name == original.table_name
    assert restored.args == original.args
    assert str(restored) == str(original)


@given(
    message=st.text(min_size=1, max_size=100),
    table_name=st.text(min_size=1, max_size=50),
    column_name=st.text(min_size=1, max_size=50)
)
def test_no_referenced_column_error_pickle_roundtrip(message, table_name, column_name):
    """NoReferencedColumnError should maintain state through pickle/unpickle."""
    original = exc.NoReferencedColumnError(message, table_name, column_name)
    
    # Pickle and unpickle
    pickled = pickle.dumps(original)
    restored = pickle.loads(pickled)
    
    # Check that all attributes are preserved
    assert restored.table_name == original.table_name
    assert restored.column_name == original.column_name
    assert restored.args == original.args
    assert str(restored) == str(original)


# Property 2: HasDescriptionCode string representation behavior
@given(
    message=st.text(min_size=1, max_size=100),
    code=st.text(min_size=1, max_size=20)
)
def test_has_description_code_str_includes_code(message, code):
    """When code is set, it should appear in the string representation."""
    # Set a version token for testing
    exc._version_token = "20"
    
    error = exc.SQLAlchemyError(message, code=code)
    error_str = str(error)
    
    # The code should be included in the string representation
    assert code in error_str
    assert "sqlalche.me/e/20/" in error_str
    assert message in error_str


@given(
    message=st.text(min_size=1, max_size=100)
)
def test_has_description_code_str_without_code(message):
    """When code is not set, string representation should just be the message."""
    error = exc.SQLAlchemyError(message)
    error_str = str(error)
    
    # No code URL should be present
    assert "sqlalche.me" not in error_str
    assert error_str == message  # Should preserve exact message including whitespace


# Property 3: DBAPIError.instance() wrapping behavior
class CustomDontWrapException(Exception, exc.DontWrapMixin):
    """Custom exception that should not be wrapped."""
    pass


@given(
    exc_message=st.text(min_size=1, max_size=100),
    statement=st.one_of(st.none(), st.text(min_size=1, max_size=200)),
    params=st.one_of(st.none(), st.dictionaries(st.text(max_size=20), st.text(max_size=50), max_size=5))
)
def test_dbapi_error_dont_wrap_mixin(exc_message, statement, params):
    """DontWrapMixin exceptions should be returned directly by DBAPIError.instance()."""
    original = CustomDontWrapException(exc_message)
    
    # DBAPIError.instance should return the original exception unchanged
    result = exc.DBAPIError.instance(
        statement, 
        params, 
        original, 
        Exception,  # dbapi_base_err
        hide_parameters=False,
        connection_invalidated=False
    )
    
    # Should be the exact same object, not wrapped
    assert result is original
    assert type(result) is CustomDontWrapException


@given(
    exc_message=st.text(min_size=1, max_size=100),
    statement=st.text(min_size=1, max_size=200),
    params=st.one_of(st.none(), st.dictionaries(st.text(max_size=20), st.text(max_size=50), max_size=5))
)
def test_dbapi_error_wraps_regular_exceptions(exc_message, statement, params):
    """Regular exceptions should be wrapped by DBAPIError.instance()."""
    original = ValueError(exc_message)
    
    result = exc.DBAPIError.instance(
        statement, 
        params, 
        original, 
        Exception,  # dbapi_base_err
        hide_parameters=False,
        connection_invalidated=False
    )
    
    # Should be wrapped in a StatementError (since it's not a DBAPI error)
    assert isinstance(result, exc.StatementError)
    assert result.orig is original
    assert result.statement == statement
    assert result.params == params


# Property 4: Exception message handling
@given(
    single_arg=st.one_of(
        st.text(min_size=0, max_size=200),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none()
    )
)
def test_sqlalchemy_error_single_arg_message(single_arg):
    """SQLAlchemyError._message() should handle single arguments correctly."""
    error = exc.SQLAlchemyError(single_arg)
    message = error._message()
    
    # Message should be the string representation of the argument
    assert message == str(single_arg)


@given(
    args=st.lists(
        st.one_of(st.text(max_size=50), st.integers(), st.floats(allow_nan=False)),
        min_size=2, 
        max_size=5
    )
)
def test_sqlalchemy_error_multiple_args_message(args):
    """SQLAlchemyError._message() with multiple args should return str(args)."""
    error = exc.SQLAlchemyError(*args)
    message = error._message()
    
    # Should be the string representation of the tuple
    assert message == str(tuple(args))


@given(
    binary_data=st.binary(min_size=1, max_size=100)
)
def test_sqlalchemy_error_bytes_message(binary_data):
    """SQLAlchemyError._message() should decode bytes arguments."""
    error = exc.SQLAlchemyError(binary_data)
    message = error._message()
    
    # Should be decoded (with backslash replacement for non-decodable bytes)
    assert isinstance(message, str)
    # The message should not be the bytes repr
    assert not message.startswith("b'")


# Property 5: Exception hierarchy invariants
def test_database_error_hierarchy():
    """All specific database errors should be subclasses of DatabaseError."""
    # These are all documented as wrapping DB-API errors
    database_error_types = [
        exc.DataError,
        exc.OperationalError,
        exc.IntegrityError,
        exc.InternalError,
        exc.ProgrammingError,
        exc.NotSupportedError
    ]
    
    for error_type in database_error_types:
        # Check class hierarchy
        assert issubclass(error_type, exc.DatabaseError)
        assert issubclass(error_type, exc.DBAPIError)
        
        # Check instances
        instance = error_type("test", None, None, Exception("test"))
        assert isinstance(instance, exc.DatabaseError)
        assert isinstance(instance, exc.DBAPIError)
        
        # Each should have a unique code
        assert hasattr(error_type, 'code')
        assert error_type.code is not None