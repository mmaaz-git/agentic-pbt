import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from unittest.mock import Mock, MagicMock, patch, call
import pytest

from trino.transaction import IsolationLevel, Transaction, NO_TRANSACTION
import trino.client
import trino.exceptions
import trino.constants


# Advanced IsolationLevel tests

@given(st.data())
def test_isolation_levels_and_values_correspondence(data):
    """Test that levels() and values() have same cardinality and correspond to enum members."""
    levels = IsolationLevel.levels()
    values = IsolationLevel.values()
    
    # Should have same number of elements
    assert len(levels) == len(values)
    
    # Each enum member should contribute exactly one level and one value
    for member in IsolationLevel:
        assert member.name in levels
        assert member.value in values
    
    # Reverse check: all levels should correspond to actual enum members
    for level_name in levels:
        assert hasattr(IsolationLevel, level_name)
        member = getattr(IsolationLevel, level_name)
        assert member.value in values


@given(st.integers(min_value=-1000, max_value=1000))
def test_isolation_level_value_uniqueness_property(offset):
    """Test that enum values maintain uniqueness even with offsets."""
    values = list(IsolationLevel.values())
    
    # Check that adding same offset to all values preserves uniqueness
    offset_values = [v + offset for v in values]
    assert len(set(offset_values)) == len(offset_values)


@given(st.sampled_from(list(IsolationLevel)))
def test_isolation_level_member_identity(member):
    """Test that enum members maintain identity properties."""
    # Member should be in its own class
    assert member in IsolationLevel
    
    # Member name should be in levels()
    assert member.name in IsolationLevel.levels()
    
    # Member value should be in values()
    assert member.value in IsolationLevel.values()
    
    # Check should accept the member's value
    assert IsolationLevel.check(member.value) == member.value


# Advanced Transaction tests

@given(st.integers(min_value=0, max_value=10))
def test_transaction_begin_with_multiple_next_uri(num_iterations):
    """Test begin() correctly handles multiple next_uri iterations."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    
    # First response from post
    mock_post_response = Mock()
    mock_post_response.ok = True
    mock_post_response.headers = {}
    
    # Create chain of responses with next_uri
    mock_statuses = []
    mock_get_responses = []
    
    for i in range(num_iterations):
        mock_status = Mock()
        mock_status.next_uri = f"http://example.com/query/{i}" if i < num_iterations - 1 else None
        mock_statuses.append(mock_status)
        
        if i < num_iterations - 1:
            mock_get_response = Mock()
            # Set transaction ID in the middle of iterations
            if i == num_iterations // 2:
                mock_get_response.headers = {'X-Trino-Started-Transaction-Id': f'txn_{i}'}
            else:
                mock_get_response.headers = {}
            mock_get_responses.append(mock_get_response)
    
    mock_request.post.return_value = mock_post_response
    mock_request.process.side_effect = mock_statuses
    mock_request.get.side_effect = mock_get_responses
    
    transaction = Transaction(mock_request)
    transaction.begin()
    
    # Should have called post once
    assert mock_request.post.call_count == 1
    
    # Should have called get for each next_uri
    assert mock_request.get.call_count == max(0, num_iterations - 1)
    
    # Should have processed all responses
    assert mock_request.process.call_count == num_iterations


@given(st.integers(min_value=100, max_value=599))
def test_transaction_begin_error_on_bad_status_code(status_code):
    """Test that begin() raises DatabaseError for non-OK responses."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    mock_response = Mock()
    mock_response.ok = (200 <= status_code < 300)
    mock_response.status_code = status_code
    mock_response.headers = {}
    
    mock_request.post.return_value = mock_response
    
    transaction = Transaction(mock_request)
    
    if not mock_response.ok:
        with pytest.raises(trino.exceptions.DatabaseError) as exc_info:
            transaction.begin()
        
        error_str = str(exc_info.value)
        assert "failed to start transaction" in error_str
        assert str(status_code) in error_str
    else:
        # Should succeed for OK status codes
        mock_status = Mock()
        mock_status.next_uri = None
        mock_request.process.return_value = mock_status
        
        transaction.begin()
        assert mock_request.post.called


@given(st.lists(st.text(min_size=1).filter(lambda x: x != NO_TRANSACTION), min_size=1, max_size=5))
def test_transaction_id_updates_from_headers(transaction_ids):
    """Test that transaction ID is properly updated from response headers."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    
    # First response
    mock_post_response = Mock()
    mock_post_response.ok = True
    mock_post_response.headers = {'X-Trino-Started-Transaction-Id': transaction_ids[0]}
    
    # Subsequent responses
    mock_statuses = []
    mock_get_responses = []
    
    for i, txn_id in enumerate(transaction_ids):
        mock_status = Mock()
        mock_status.next_uri = f"http://example.com/{i}" if i < len(transaction_ids) - 1 else None
        mock_statuses.append(mock_status)
        
        if i > 0:
            mock_get_response = Mock()
            mock_get_response.headers = {'X-Trino-Started-Transaction-Id': txn_id}
            mock_get_responses.append(mock_get_response)
    
    mock_request.post.return_value = mock_post_response
    mock_request.process.side_effect = mock_statuses
    mock_request.get.side_effect = mock_get_responses
    
    transaction = Transaction(mock_request)
    transaction.begin()
    
    # Should have the last non-NO_TRANSACTION ID
    assert transaction.id == transaction_ids[-1]
    assert mock_request.transaction_id == transaction_ids[-1]


@given(st.text(min_size=1).filter(lambda x: x != NO_TRANSACTION))
def test_transaction_commit_without_begin(transaction_id):
    """Test commit behavior when transaction was not properly begun."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    
    with patch('trino.client.TrinoQuery') as mock_query_class:
        mock_query = Mock()
        mock_query.execute.return_value = []
        mock_query_class.return_value = mock_query
        
        transaction = Transaction(mock_request)
        
        # Manually set ID without calling begin()
        transaction._id = transaction_id
        
        # Should still work and reset ID
        transaction.commit()
        
        assert transaction.id == NO_TRANSACTION
        assert mock_query_class.called
        assert mock_query.execute.called


@given(st.text(min_size=1).filter(lambda x: x != NO_TRANSACTION))
def test_transaction_rollback_without_begin(transaction_id):
    """Test rollback behavior when transaction was not properly begun."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    
    with patch('trino.client.TrinoQuery') as mock_query_class:
        mock_query = Mock()
        mock_query.execute.return_value = []
        mock_query_class.return_value = mock_query
        
        transaction = Transaction(mock_request)
        
        # Manually set ID without calling begin()
        transaction._id = transaction_id
        
        # Should still work and reset ID
        transaction.rollback()
        
        assert transaction.id == NO_TRANSACTION
        assert mock_query_class.called
        assert mock_query.execute.called


@given(st.data())
def test_transaction_properties_are_read_only(data):
    """Test that transaction properties (id, request) are read-only."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    transaction = Transaction(mock_request)
    
    # id property should be read-only (no setter defined)
    with pytest.raises(AttributeError):
        transaction.id = "new_id"
    
    # request property should be read-only (no setter defined)
    with pytest.raises(AttributeError):
        transaction.request = Mock()


@given(st.lists(st.sampled_from([None, NO_TRANSACTION, "txn_123", ""]), min_size=1, max_size=5))
def test_transaction_begin_header_precedence(header_values):
    """Test that begin() correctly prioritizes valid transaction IDs from headers."""
    mock_request = Mock(spec=trino.client.TrinoRequest)
    
    # First response
    mock_post_response = Mock()
    mock_post_response.ok = True
    first_header = header_values[0]
    mock_post_response.headers = {'X-Trino-Started-Transaction-Id': first_header} if first_header else {}
    
    # Create responses
    mock_statuses = []
    mock_get_responses = []
    
    for i, header_value in enumerate(header_values):
        mock_status = Mock()
        mock_status.next_uri = f"http://example.com/{i}" if i < len(header_values) - 1 else None
        mock_statuses.append(mock_status)
        
        if i > 0:
            mock_get_response = Mock()
            if header_value:
                mock_get_response.headers = {'X-Trino-Started-Transaction-Id': header_value}
            else:
                mock_get_response.headers = {}
            mock_get_responses.append(mock_get_response)
    
    mock_request.post.return_value = mock_post_response
    mock_request.process.side_effect = mock_statuses
    mock_request.get.side_effect = mock_get_responses
    
    transaction = Transaction(mock_request)
    transaction.begin()
    
    # Find the last valid transaction ID (not None, not NO_TRANSACTION, not empty)
    expected_id = NO_TRANSACTION
    for header in reversed(header_values):
        if header and header != NO_TRANSACTION:
            expected_id = header
            break
    
    assert transaction.id == expected_id


# Edge case tests

@given(st.data())
def test_isolation_level_check_preserves_type(data):
    """Test that check() preserves the type of valid input values."""
    for member in IsolationLevel:
        result = IsolationLevel.check(member.value)
        assert type(result) == type(member.value)
        assert result == member.value


@given(st.one_of(st.floats(), st.text(), st.none(), st.lists(st.integers())))
def test_isolation_level_check_with_non_integer_types(value):
    """Test that check() properly handles non-integer types."""
    if not isinstance(value, int):
        with pytest.raises((ValueError, TypeError)):
            IsolationLevel.check(value)