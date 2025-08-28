import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from unittest.mock import Mock, MagicMock, patch
import pytest

from trino.transaction import IsolationLevel, Transaction, NO_TRANSACTION
import trino.client
import trino.exceptions


# Test IsolationLevel enum properties

@given(st.data())
def test_isolation_level_levels_are_unique_strings(data):
    """Test that levels() returns a set of unique non-empty strings."""
    levels = IsolationLevel.levels()
    
    # Should be a set (inherently unique)
    assert isinstance(levels, set)
    
    # All items should be strings
    assert all(isinstance(level, str) for level in levels)
    
    # All strings should be non-empty
    assert all(len(level) > 0 for level in levels)
    
    # Set size should match enum member count
    assert len(levels) == len(IsolationLevel)


@given(st.data())
def test_isolation_level_values_are_unique_integers(data):
    """Test that values() returns a set of unique integers."""
    values = IsolationLevel.values()
    
    # Should be a set (inherently unique)
    assert isinstance(values, set)
    
    # All items should be integers
    assert all(isinstance(value, int) for value in values)
    
    # Set size should match enum member count
    assert len(values) == len(IsolationLevel)


@given(st.integers())
def test_isolation_level_check_validates_correctly(value):
    """Test that check() accepts valid values and rejects invalid ones."""
    valid_values = IsolationLevel.values()
    
    if value in valid_values:
        # Should return the same value for valid inputs
        result = IsolationLevel.check(value)
        assert result == value
    else:
        # Should raise ValueError for invalid inputs
        with pytest.raises(ValueError) as exc_info:
            IsolationLevel.check(value)
        assert "invalid isolation level" in str(exc_info.value)
        assert str(value) in str(exc_info.value)


@given(st.data())
def test_isolation_level_enum_members_are_unique(data):
    """Test that all enum members have unique values (enforced by @unique decorator)."""
    values = [member.value for member in IsolationLevel]
    names = [member.name for member in IsolationLevel]
    
    # All values should be unique
    assert len(values) == len(set(values))
    
    # All names should be unique
    assert len(names) == len(set(names))


@given(st.data())
def test_isolation_level_standard_values(data):
    """Test that IsolationLevel contains standard SQL isolation levels."""
    # These are standard SQL isolation levels that should exist
    expected_levels = {
        "AUTOCOMMIT",
        "READ_UNCOMMITTED", 
        "READ_COMMITTED",
        "REPEATABLE_READ",
        "SERIALIZABLE"
    }
    
    actual_levels = IsolationLevel.levels()
    assert expected_levels == actual_levels


# Test Transaction class properties

@given(st.data())
def test_transaction_initial_state(data):
    """Test that a new transaction starts with NO_TRANSACTION id."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    transaction = Transaction(mock_request)
    
    assert transaction.id == NO_TRANSACTION
    assert transaction.request is mock_request


@given(st.text(min_size=1).filter(lambda x: x != NO_TRANSACTION))
def test_transaction_begin_changes_id(transaction_id):
    """Test that begin() changes transaction ID from NO_TRANSACTION."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    mock_response = Mock()
    mock_response.ok = True
    mock_response.headers = {'X-Trino-Started-Transaction-Id': transaction_id}
    
    mock_status = Mock()
    mock_status.next_uri = None
    
    mock_request.post.return_value = mock_response
    mock_request.process.return_value = mock_status
    
    transaction = Transaction(mock_request)
    assert transaction.id == NO_TRANSACTION
    
    transaction.begin()
    
    assert transaction.id == transaction_id
    assert transaction.id != NO_TRANSACTION
    assert mock_request.transaction_id == transaction_id


@given(st.text(min_size=1).filter(lambda x: x != NO_TRANSACTION))
def test_transaction_commit_resets_id(transaction_id):
    """Test that commit() resets transaction ID to NO_TRANSACTION."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    
    with patch('trino.client.TrinoQuery') as mock_query_class:
        mock_query = Mock()
        mock_query.execute.return_value = []
        mock_query_class.return_value = mock_query
        
        transaction = Transaction(mock_request)
        # Simulate that begin() was called and ID was set
        transaction._id = transaction_id
        mock_request.transaction_id = transaction_id
        
        transaction.commit()
        
        assert transaction.id == NO_TRANSACTION
        assert mock_request.transaction_id == NO_TRANSACTION


@given(st.text(min_size=1).filter(lambda x: x != NO_TRANSACTION))
def test_transaction_rollback_resets_id(transaction_id):
    """Test that rollback() resets transaction ID to NO_TRANSACTION."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    
    with patch('trino.client.TrinoQuery') as mock_query_class:
        mock_query = Mock()
        mock_query.execute.return_value = []
        mock_query_class.return_value = mock_query
        
        transaction = Transaction(mock_request)
        # Simulate that begin() was called and ID was set
        transaction._id = transaction_id
        mock_request.transaction_id = transaction_id
        
        transaction.rollback()
        
        assert transaction.id == NO_TRANSACTION
        assert mock_request.transaction_id == NO_TRANSACTION


@given(st.text(min_size=1).filter(lambda x: x != NO_TRANSACTION), 
       st.text(min_size=1))
def test_transaction_commit_error_format(transaction_id, error_msg):
    """Test that commit() raises DatabaseError with correct format on failure."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    
    with patch('trino.client.TrinoQuery') as mock_query_class:
        mock_query = Mock()
        mock_query.execute.side_effect = Exception(error_msg)
        mock_query_class.return_value = mock_query
        
        transaction = Transaction(mock_request)
        transaction._id = transaction_id
        
        with pytest.raises(trino.exceptions.DatabaseError) as exc_info:
            transaction.commit()
        
        error_str = str(exc_info.value)
        assert "failed to commit transaction" in error_str
        assert transaction_id in error_str
        assert error_msg in error_str


@given(st.text(min_size=1).filter(lambda x: x != NO_TRANSACTION),
       st.text(min_size=1))
def test_transaction_rollback_error_format(transaction_id, error_msg):
    """Test that rollback() raises DatabaseError with correct format on failure."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    
    with patch('trino.client.TrinoQuery') as mock_query_class:
        mock_query = Mock()
        mock_query.execute.side_effect = Exception(error_msg)
        mock_query_class.return_value = mock_query
        
        transaction = Transaction(mock_request)
        transaction._id = transaction_id
        
        with pytest.raises(trino.exceptions.DatabaseError) as exc_info:
            transaction.rollback()
        
        error_str = str(exc_info.value)
        assert "failed to rollback transaction" in error_str
        assert transaction_id in error_str
        assert error_msg in error_str


@given(st.data())
def test_transaction_begin_without_transaction_header(data):
    """Test begin() behavior when no transaction ID is in response headers."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    mock_response = Mock()
    mock_response.ok = True
    mock_response.headers = {}  # No transaction ID header
    
    mock_status = Mock()
    mock_status.next_uri = None
    
    mock_request.post.return_value = mock_response
    mock_request.process.return_value = mock_status
    
    transaction = Transaction(mock_request)
    transaction.begin()
    
    # Should remain NO_TRANSACTION if no header provided
    assert transaction.id == NO_TRANSACTION
    assert mock_request.transaction_id == NO_TRANSACTION


@given(st.data())
def test_transaction_begin_with_none_header(data):
    """Test begin() behavior when transaction header value is NO_TRANSACTION."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    mock_response = Mock()
    mock_response.ok = True
    mock_response.headers = {'X-Trino-Started-Transaction-Id': NO_TRANSACTION}
    
    mock_status = Mock()
    mock_status.next_uri = None
    
    mock_request.post.return_value = mock_response
    mock_request.process.return_value = mock_status
    
    transaction = Transaction(mock_request)
    transaction.begin()
    
    # Should remain NO_TRANSACTION
    assert transaction.id == NO_TRANSACTION
    assert mock_request.transaction_id == NO_TRANSACTION