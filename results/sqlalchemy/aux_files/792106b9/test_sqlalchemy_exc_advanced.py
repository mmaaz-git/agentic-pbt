"""Advanced property-based tests for sqlalchemy.exc module."""

import pickle
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import sqlalchemy.exc as exc


# Test edge cases in _code_str when version_token is None
@given(
    message=st.text(min_size=1, max_size=100),
    code=st.text(min_size=1, max_size=20)
)
def test_code_str_with_none_version_token(message, code):
    """Test _code_str behavior when _version_token is None."""
    # Save original and set to None
    original_token = exc._version_token
    exc._version_token = None
    
    try:
        error = exc.SQLAlchemyError(message, code=code)
        error_str = str(error)
        
        # Should still include the code URL, with None as the version
        assert f"sqlalche.me/e/None/{code}" in error_str
        assert message in error_str
    finally:
        # Restore original
        exc._version_token = original_token


# Test StatementError with detail messages
@given(
    main_message=st.text(min_size=1, max_size=50),
    statement=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    params=st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.text(max_size=20), max_size=3)),
    detail_messages=st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=3),
    hide_params=st.booleans()
)
def test_statement_error_with_details(main_message, statement, params, detail_messages, hide_params):
    """Test StatementError formatting with detail messages."""
    orig_exc = Exception("original")
    error = exc.StatementError(main_message, statement, params, orig_exc, hide_parameters=hide_params)
    
    # Add detail messages
    for detail in detail_messages:
        error.add_detail(detail)
    
    error_str = error._sql_message()
    
    # Check that all details are in the output
    for detail in detail_messages:
        assert f"({detail})" in error_str
    
    # Check main message is included
    assert main_message in error_str
    
    if statement:
        assert "[SQL:" in error_str
        assert statement in error_str
        
        if params and hide_params:
            assert "hidden due to hide_parameters=True" in error_str
        elif params:
            assert "[parameters:" in error_str


# Test pickling of StatementError with all fields
@given(
    message=st.text(min_size=1, max_size=50),
    statement=st.one_of(st.none(), st.text(max_size=100)),
    params=st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.text(max_size=20), max_size=3)),
    hide_params=st.booleans(),
    code=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    detail_messages=st.lists(st.text(max_size=30), max_size=2),
    ismulti=st.one_of(st.none(), st.booleans())
)
def test_statement_error_pickle_roundtrip(message, statement, params, hide_params, code, detail_messages, ismulti):
    """StatementError should maintain all state through pickle/unpickle."""
    orig_exc = ValueError("test error")
    original = exc.StatementError(
        message, statement, params, orig_exc, 
        hide_parameters=hide_params, code=code, ismulti=ismulti
    )
    
    # Add detail messages
    for detail in detail_messages:
        original.add_detail(detail)
    
    # Pickle and unpickle
    pickled = pickle.dumps(original)
    restored = pickle.loads(pickled)
    
    # Check all attributes are preserved
    assert restored.statement == original.statement
    assert restored.params == original.params
    assert restored.hide_parameters == original.hide_parameters
    assert restored.code == original.code
    assert restored.ismulti == original.ismulti
    assert restored.detail == original.detail
    # Note: orig exception won't be identical after pickling
    assert type(restored.orig) == type(original.orig)
    assert str(restored.orig) == str(original.orig)


# Test DBAPIError.instance with complex exception hierarchies
class CustomDBAPIError(Exception):
    """Simulates a DBAPI exception."""
    pass


class CustomIntegrityError(CustomDBAPIError):
    """Simulates a DBAPI IntegrityError."""
    pass


@given(
    statement=st.text(min_size=1, max_size=100),
    params=st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.text(max_size=20), max_size=3))
)
def test_dbapi_error_instance_maps_to_correct_subclass(statement, params):
    """DBAPIError.instance should map DBAPI errors to correct SQLAlchemy exception classes."""
    # Create a custom exception that has 'IntegrityError' in its name
    class IntegrityError(Exception):
        pass
    
    orig = IntegrityError("constraint violation")
    
    result = exc.DBAPIError.instance(
        statement, params, orig, 
        Exception,  # dbapi_base_err
        hide_parameters=False
    )
    
    # Should be wrapped in SQLAlchemy's IntegrityError
    assert isinstance(result, exc.IntegrityError)
    assert result.orig is orig
    assert result.statement == statement
    

# Test edge case: exception with non-string __str__
class BrokenStrException(Exception):
    """Exception with broken __str__ method."""
    def __str__(self):
        raise RuntimeError("Cannot convert to string!")


@given(
    statement=st.one_of(st.none(), st.text(max_size=100)),
    params=st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.text(max_size=20), max_size=3))
)
def test_dbapi_error_with_broken_str(statement, params):
    """DBAPIError should handle exceptions with broken __str__ methods."""
    orig = BrokenStrException("test")
    
    error = exc.DBAPIError(statement, params, orig)
    
    # Should handle the broken __str__ gracefully
    error_str = str(error)
    assert "Error in str() of DB-API-generated exception" in error_str
    assert "Cannot convert to string!" in error_str  # The error message from broken __str__


# Test ObjectNotExecutableError pickling
@given(
    target_obj=st.one_of(
        st.text(max_size=50),
        st.integers(),
        st.lists(st.integers(), max_size=3),
        st.dictionaries(st.text(max_size=5), st.integers(), max_size=2)
    )
)
def test_object_not_executable_error_pickle(target_obj):
    """ObjectNotExecutableError should pickle/unpickle correctly with various target types."""
    original = exc.ObjectNotExecutableError(target_obj)
    
    pickled = pickle.dumps(original)
    restored = pickle.loads(pickled)
    
    assert restored.target == original.target
    assert str(restored) == str(original)
    

# Test that UnsupportedCompilationError preserves all attributes
class MockCompiler:
    def __repr__(self):
        return "<MockCompiler>"

    
class MockElement:
    pass


@given(
    message=st.one_of(st.none(), st.text(max_size=100))
)
def test_unsupported_compilation_error_pickle(message):
    """UnsupportedCompilationError should pickle correctly."""
    compiler = MockCompiler()
    element_type = MockElement
    
    original = exc.UnsupportedCompilationError(compiler, element_type, message)
    
    pickled = pickle.dumps(original)
    restored = pickle.loads(pickled)
    
    # Check attributes
    assert type(restored.compiler).__name__ == type(original.compiler).__name__
    assert restored.element_type == original.element_type
    assert restored.message == original.message
    assert str(restored) == str(original)


# Test with moderately large messages and parameters
@given(
    message=st.text(min_size=100, max_size=500),
    statement=st.text(min_size=50, max_size=200),
    num_params=st.integers(min_value=10, max_value=30)
)
def test_statement_error_with_large_data(message, statement, num_params):
    """Test StatementError with large messages and many parameters."""
    # Generate many parameters
    params = {f"param_{i}": f"value_{i}" for i in range(num_params)}
    
    orig = Exception("original")
    error = exc.StatementError(message, statement, params, orig)
    
    # Should handle large data without issues
    error_str = str(error)
    
    # The message should be included
    assert len(error_str) > 0
    assert message in error_str
    
    # Test pickling with large data
    pickled = pickle.dumps(error)
    restored = pickle.loads(pickled)
    
    assert restored.statement == statement
    assert restored.params == params
    assert str(restored) == str(error)