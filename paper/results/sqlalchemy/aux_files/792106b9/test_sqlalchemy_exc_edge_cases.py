"""Edge case tests for sqlalchemy.exc module - looking for bugs."""

import pickle
from hypothesis import given, strategies as st, assume
import sqlalchemy.exc as exc


# Test CircularDependencyError with special characters and edge cases
@given(
    cycles=st.lists(
        st.one_of(
            st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1),  # Unicode characters
            st.text(min_size=1).filter(lambda x: ")" in x or "(" in x),  # Parentheses that could break formatting
        ),
        min_size=1,
        max_size=5
    )
)
def test_circular_dependency_error_special_cycles(cycles):
    """Test CircularDependencyError with cycles containing special characters."""
    edges = []
    error = exc.CircularDependencyError("Test error", cycles, edges)
    
    # Should format correctly even with special characters
    error_str = str(error)
    
    # Each cycle should be repr'd and included
    for cycle in cycles:
        assert repr(cycle) in error_str
    
    # Test pickling with special characters
    pickled = pickle.dumps(error)
    restored = pickle.loads(pickled)
    assert restored.cycles == cycles


# Test DBAPIError.instance with ambiguous exception names
def test_dbapi_error_instance_name_resolution():
    """Test DBAPIError.instance with conflicting exception class names."""
    
    # Create custom exceptions with DB-API-like names
    class DataError(Exception):
        """Custom DataError that's not from DB-API."""
        pass
    
    class MySpecialDataError(DataError):
        """Subclass of custom DataError."""
        pass
    
    orig = MySpecialDataError("custom error")
    
    # DBAPIError.instance should map to SQLAlchemy's DataError based on name
    result = exc.DBAPIError.instance(
        "SELECT * FROM table",
        {"id": 1},
        orig,
        Exception,  # dbapi_base_err
    )
    
    # Should be wrapped in SQLAlchemy's DataError (not the custom one)
    assert isinstance(result, exc.DataError)
    assert isinstance(result, exc.DatabaseError)
    assert result.orig is orig


# Test StatementError with None parameters edge cases
@given(
    hide_params=st.booleans()
)
def test_statement_error_none_handling(hide_params):
    """Test StatementError handles None in various fields correctly."""
    # All None
    error = exc.StatementError(
        "message",
        None,  # statement
        None,  # params
        None,  # orig
        hide_parameters=hide_params
    )
    
    error_str = str(error)
    assert "message" in error_str
    assert "[SQL:" not in error_str  # No SQL section when statement is None
    
    # Pickle should work with None values
    pickled = pickle.dumps(error)
    restored = pickle.loads(pickled)
    assert restored.statement is None
    assert restored.params is None
    assert restored.orig is None


# Test parameter truncation in _repr_params
@given(
    num_params=st.integers(min_value=20, max_value=50),
    param_value_size=st.integers(min_value=100, max_value=500)
)
def test_statement_error_param_truncation(num_params, param_value_size):
    """Test that very large parameter dictionaries are truncated in display."""
    # Create large parameters
    params = {
        f"param_{i}": "x" * param_value_size
        for i in range(num_params)
    }
    
    error = exc.StatementError(
        "Query failed",
        "SELECT * FROM table WHERE id = :param_0",
        params,
        Exception("test")
    )
    
    error_str = str(error)
    
    # The params should be truncated (only first 10 shown by default)
    # Check that not all params are shown
    if num_params > 10:
        # Only first 10 params should be in the repr
        assert "param_15" not in error_str or "..." in error_str


# Test exceptions with circular references
def test_circular_reference_in_exception():
    """Test exceptions that have circular references in their attributes."""
    error1 = exc.SQLAlchemyError("error1")
    error2 = exc.SQLAlchemyError("error2")
    
    # Create circular reference
    error1.other = error2
    error2.other = error1
    
    # Should not cause infinite recursion in str()
    str(error1)
    str(error2)
    
    # Pickling might fail with circular references, but shouldn't crash
    try:
        pickle.dumps(error1)
    except (RecursionError, ValueError):
        # Expected - circular references can't be pickled
        pass


# Test DBAPIError with BaseException subclasses
@given(
    statement=st.text(max_size=100),
    params=st.dictionaries(st.text(max_size=10), st.text(max_size=20), max_size=3)
)
def test_dbapi_error_base_exception_handling(statement, params):
    """Test that BaseException subclasses (not Exception) are not wrapped."""
    
    class CustomBaseException(BaseException):
        """Custom BaseException subclass."""
        pass
    
    orig = CustomBaseException("system exit")
    
    # Should return the original exception without wrapping
    result = exc.DBAPIError.instance(
        statement,
        params,
        orig,
        Exception,  # dbapi_base_err
    )
    
    # Should be the exact same object
    assert result is orig
    assert type(result) is CustomBaseException


# Test exception with empty cycles list
def test_circular_dependency_empty_cycles():
    """Test CircularDependencyError with empty cycles."""
    error = exc.CircularDependencyError("Test", [], [])
    error_str = str(error)
    
    # Should handle empty cycles gracefully
    assert "Test ()" in error_str  # Empty tuple representation
    
    # Pickle should work
    pickled = pickle.dumps(error)
    restored = pickle.loads(pickled)
    assert restored.cycles == []


# Test NoReferencedColumnError with empty strings
@given(
    use_empty_message=st.booleans(),
    use_empty_table=st.booleans(), 
    use_empty_column=st.booleans()
)
def test_no_referenced_column_error_empty_strings(use_empty_message, use_empty_table, use_empty_column):
    """Test NoReferencedColumnError with empty string fields."""
    message = "" if use_empty_message else "error message"
    table_name = "" if use_empty_table else "table"
    column_name = "" if use_empty_column else "column"
    
    error = exc.NoReferencedColumnError(message, table_name, column_name)
    
    assert error.table_name == table_name
    assert error.column_name == column_name
    
    # Should pickle correctly even with empty strings
    pickled = pickle.dumps(error)
    restored = pickle.loads(pickled)
    
    assert restored.table_name == table_name
    assert restored.column_name == column_name
    assert str(restored) == str(error)