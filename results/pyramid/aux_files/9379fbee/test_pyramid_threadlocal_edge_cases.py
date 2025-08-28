import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock
import random

from hypothesis import assume, given, strategies as st, settings, example

from pyramid.threadlocal import ThreadLocalManager, RequestContext, get_current_request, get_current_registry, manager


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=1000)
def test_concurrent_push_pop_race_conditions(n_operations):
    """Test for race conditions in concurrent push/pop operations."""
    tlm = ThreadLocalManager(default=lambda: None)
    errors = []
    
    def worker(thread_id, ops):
        try:
            local_stack = []
            for i in range(ops):
                if random.random() < 0.5:
                    # Push
                    item = {"thread": thread_id, "op": i}
                    tlm.push(item)
                    local_stack.append(item)
                elif local_stack:
                    # Pop and verify
                    expected = local_stack.pop()
                    actual = tlm.pop()
                    if actual != expected:
                        errors.append(f"Thread {thread_id}: Expected {expected}, got {actual}")
        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i, n_operations) for i in range(10)]
        for future in as_completed(futures):
            future.result()
    
    assert not errors, f"Race condition detected: {errors}"


@given(st.data())
def test_default_function_called_only_when_needed(data):
    """Test that default function is only called when stack is empty."""
    call_count = [0]
    
    def counting_default():
        call_count[0] += 1
        return {"default": "value"}
    
    tlm = ThreadLocalManager(default=counting_default)
    
    # First get should call default
    result1 = tlm.get()
    assert call_count[0] == 1
    assert result1 == {"default": "value"}
    
    # Push some items
    n_items = data.draw(st.integers(min_value=1, max_value=10))
    for i in range(n_items):
        tlm.push({"item": i})
        # Get should not call default when stack has items
        prev_count = call_count[0]
        tlm.get()
        assert call_count[0] == prev_count
    
    # Pop all items
    for _ in range(n_items):
        tlm.pop()
    
    # Now get should call default again
    prev_count = call_count[0]
    tlm.get()
    assert call_count[0] == prev_count + 1


@given(st.lists(st.none() | st.dictionaries(st.text(), st.text())))
def test_none_values_handled_correctly(items):
    """Test that None values can be pushed and retrieved correctly."""
    tlm = ThreadLocalManager(default=lambda: {"default": "value"})
    
    for item in items:
        tlm.push(item)
        assert tlm.get() == item  # Should work even for None
    
    # Pop all and verify
    for item in reversed(items):
        assert tlm.pop() == item


def test_manager_singleton_thread_isolation():
    """Test that the global manager maintains thread isolation."""
    results = {}
    barrier = threading.Barrier(3)
    
    def worker(thread_id):
        # Synchronize start
        barrier.wait()
        
        # Clear any existing state
        manager.clear()
        
        # Push thread-specific data
        manager.push({"thread_id": thread_id, "data": f"data_{thread_id}"})
        
        # Small delay to increase chance of race conditions
        time.sleep(0.001)
        
        # Get and verify we see our own data
        result = manager.get()
        results[thread_id] = result
        
        # Clean up
        manager.pop()
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Each thread should have seen its own data
    for thread_id in range(3):
        assert results[thread_id]["thread_id"] == thread_id
        assert results[thread_id]["data"] == f"data_{thread_id}"


@given(st.lists(st.text(), min_size=1))
def test_exception_in_context_manager_cleans_up_properly(items):
    """Test that exceptions in RequestContext still clean up the stack."""
    mock_request = Mock()
    mock_request.registry = {"test": "registry"}
    
    # Push some initial items
    for item in items:
        manager.push({"item": item})
    
    initial_depth = len(manager.stack)
    
    try:
        with RequestContext(mock_request):
            # Stack should have grown
            assert len(manager.stack) == initial_depth + 1
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # Stack should be restored even after exception
    assert len(manager.stack) == initial_depth


@given(st.integers(min_value=0, max_value=1000))
def test_large_stack_operations(n):
    """Test that large stacks work correctly."""
    tlm = ThreadLocalManager(default=lambda: None)
    
    # Push many items
    items = [{"index": i, "data": f"item_{i}"} for i in range(n)]
    for item in items:
        tlm.push(item)
    
    # Verify we can get the last item
    if items:
        assert tlm.get() == items[-1]
    
    # Clear should work even with large stack
    tlm.clear()
    assert tlm.pop() is None


@given(st.lists(st.dictionaries(st.text(), st.text()), min_size=1))
def test_request_context_begin_end_explicit(items):
    """Test explicit begin/end methods of RequestContext."""
    mock_request = Mock()
    mock_request.registry = items[0]
    
    ctx = RequestContext(mock_request)
    
    # Begin should push and return request
    returned_request = ctx.begin()
    assert returned_request is mock_request
    assert get_current_request() is mock_request
    
    # End should pop
    ctx.end()
    
    # Should be back to None
    assert get_current_request() is None
    
    # Multiple begin/end cycles
    for item in items:
        mock_request.registry = item
        ctx.begin()
        assert get_current_registry() == item
        ctx.end()


def test_default_none_instead_of_callable():
    """Test behavior when default is None instead of a callable."""
    tlm = ThreadLocalManager(default=None)
    
    # This should raise an error when trying to call None
    try:
        result = tlm.get()
        # If we get here, it means get() didn't try to call default
        assert False, f"Expected TypeError, got {result}"
    except TypeError as e:
        # This is expected - default=None is not callable
        assert "'NoneType' object is not callable" in str(e)


@given(st.dictionaries(st.text(), st.text()))
def test_get_current_registry_with_context_parameter(data):
    """Test that get_current_registry ignores the context parameter."""
    mock_request = Mock()
    mock_request.registry = data
    
    with RequestContext(mock_request):
        # The context parameter should be ignored
        assert get_current_registry(context="ignored") == data
        assert get_current_registry(context=None) == data
        assert get_current_registry() == data