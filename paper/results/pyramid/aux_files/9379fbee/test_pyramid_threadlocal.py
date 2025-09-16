import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

from hypothesis import assume, given, strategies as st, settings

from pyramid.threadlocal import ThreadLocalManager, RequestContext, get_current_request, get_current_registry, manager


@given(st.lists(st.dictionaries(st.text(), st.text())))
def test_threadlocal_push_pop_lifo(items):
    """Test that ThreadLocalManager maintains LIFO order for push/pop operations."""
    tlm = ThreadLocalManager(default=lambda: None)
    
    # Push all items
    for item in items:
        tlm.push(item)
    
    # Pop all items and verify LIFO order
    popped = []
    for _ in range(len(items)):
        popped_item = tlm.pop()
        popped.append(popped_item)
    
    assert popped == list(reversed(items))
    
    # After popping all, next pop should return None
    assert tlm.pop() is None


@given(st.lists(st.dictionaries(st.text(), st.text())))  
def test_threadlocal_get_returns_last_pushed(items):
    """Test that get() always returns the last pushed item."""
    tlm = ThreadLocalManager(default=lambda: {"default": "value"})
    
    if not items:
        # Empty stack should return default
        assert tlm.get() == {"default": "value"}
    else:
        for item in items:
            tlm.push(item)
            assert tlm.get() == item


@given(st.lists(st.dictionaries(st.text(), st.text())))
def test_threadlocal_clear_empties_stack(items):
    """Test that clear() empties the stack completely."""
    tlm = ThreadLocalManager(default=lambda: {"default": "value"})
    
    # Push items
    for item in items:
        tlm.push(item)
    
    # Clear should empty the stack
    tlm.clear()
    
    # After clear, get should return default
    assert tlm.get() == {"default": "value"}
    
    # Pop should return None
    assert tlm.pop() is None


@given(
    st.lists(st.dictionaries(st.text(), st.text()), min_size=1, max_size=10),
    st.lists(st.dictionaries(st.text(), st.text()), min_size=1, max_size=10)
)
def test_threadlocal_thread_isolation(items1, items2):
    """Test that each thread has its own independent stack."""
    tlm = ThreadLocalManager(default=lambda: None)
    results = {}
    
    def thread_work(thread_id, items):
        # Each thread pushes its items
        for item in items:
            tlm.push(item)
        
        # Each thread should see only its own last item
        results[thread_id] = tlm.get()
        
        # Clean up
        for _ in range(len(items)):
            tlm.pop()
    
    # Run in separate threads
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(thread_work, "thread1", items1)
        future2 = executor.submit(thread_work, "thread2", items2)
        future1.result()
        future2.result()
    
    # Each thread should have seen its own last item
    assert results["thread1"] == items1[-1]
    assert results["thread2"] == items2[-1]


@given(st.dictionaries(st.text(), st.text()))
def test_request_context_manager_state_restoration(request_data):
    """Test that RequestContext properly manages stack state."""
    # Create a mock request with registry
    mock_request = Mock()
    mock_request.registry = {"test_registry": request_data}
    
    # Get initial state
    initial_state = manager.get()
    
    # Use RequestContext
    with RequestContext(mock_request) as req:
        # Inside context, should have the request
        assert req is mock_request
        current = manager.get()
        assert current['request'] is mock_request
        assert current['registry'] == {"test_registry": request_data}
    
    # After context, state should be restored
    final_state = manager.get()
    assert final_state == initial_state


@given(st.lists(st.dictionaries(st.text(), st.text()), min_size=2))
def test_nested_request_contexts(request_data_list):
    """Test that nested RequestContexts properly maintain stack."""
    # Create mock requests
    mock_requests = []
    for data in request_data_list:
        mock_req = Mock()
        mock_req.registry = data
        mock_requests.append(mock_req)
    
    # Clear manager to start fresh
    manager.clear()
    
    # Nested contexts
    def verify_nested(requests, depth=0):
        if depth >= len(requests):
            return
        
        with RequestContext(requests[depth]):
            # Verify current request is correct
            assert get_current_request() is requests[depth]
            assert get_current_registry() == requests[depth].registry
            
            # Go deeper
            verify_nested(requests, depth + 1)
            
            # After returning, should still be at this level
            assert get_current_request() is requests[depth]
    
    verify_nested(mock_requests)
    
    # After all contexts, should be back to default
    assert get_current_request() is None


@given(st.integers(min_value=0, max_value=100))
def test_push_pop_symmetry(n):
    """Test that n pushes followed by n pops leaves stack in original state."""
    tlm = ThreadLocalManager(default=lambda: {"default": "value"})
    
    # Get initial state
    initial = tlm.get()
    
    # Push n items
    for i in range(n):
        tlm.push({"item": i})
    
    # Pop n items
    for _ in range(n):
        tlm.pop()
    
    # Should be back to initial state
    assert tlm.get() == initial


@given(st.lists(st.text()))
def test_set_is_alias_for_push(items):
    """Test that set() is an alias for push() (backward compatibility)."""
    tlm1 = ThreadLocalManager(default=lambda: None)
    tlm2 = ThreadLocalManager(default=lambda: None)
    
    for item in items:
        tlm1.push(item)
        tlm2.set(item)  # Should be equivalent
    
    # Both should have same state
    for _ in range(len(items)):
        assert tlm1.pop() == tlm2.pop()