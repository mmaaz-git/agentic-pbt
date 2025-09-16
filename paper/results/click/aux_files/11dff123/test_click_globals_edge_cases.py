import threading
import time
from hypothesis import given, strategies as st, assume, settings, note
from click.globals import push_context, pop_context, get_current_context, resolve_color_default, _local
from click.core import Context, Command
import pytest


# Property: Popping from empty stack behavior
@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=1000)
def test_pop_empty_stack(num_pops):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    # Try to pop from empty stack multiple times
    for i in range(num_pops):
        with pytest.raises((IndexError, AttributeError)):
            pop_context()


# Property: Context identity preservation
@given(st.data())
@settings(max_examples=1000)
def test_context_identity_preservation(data):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    cmd = Command('test')
    color = data.draw(st.one_of(st.none(), st.booleans()))
    ctx = Context(cmd, color=color)
    
    # Push the same context multiple times
    num_pushes = data.draw(st.integers(min_value=1, max_value=10))
    for _ in range(num_pushes):
        push_context(ctx)
    
    # Each get should return the same object
    retrieved = []
    for _ in range(num_pushes):
        current = get_current_context(silent=False)
        retrieved.append(current)
        assert current is ctx
        pop_context()
    
    # All retrieved contexts should be the same object
    assert all(r is ctx for r in retrieved)


# Property: Concurrent push/pop operations
@given(st.lists(st.tuples(st.sampled_from(['push', 'pop']), st.integers(0, 100)), min_size=10, max_size=50))
@settings(max_examples=100, deadline=10000)
def test_concurrent_operations(operations):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    contexts = [Context(Command(f'test{i}')) for i in range(10)]
    results = []
    errors = []
    
    def worker(op, idx):
        try:
            if op == 'push':
                ctx = contexts[idx % len(contexts)]
                push_context(ctx)
                results.append(('push', ctx))
            else:
                pop_context()
                results.append(('pop', None))
        except Exception as e:
            errors.append(e)
    
    threads = []
    push_count = 0
    
    # Track expected push/pop balance
    for op, idx in operations:
        if op == 'push':
            push_count += 1
        else:
            if push_count > 0:
                push_count -= 1
            else:
                continue  # Skip pop if would go negative
        
        t = threading.Thread(target=worker, args=(op, idx))
        threads.append(t)
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    # Thread isolation should mean each thread has its own stack
    # Main thread should still have empty stack
    assert get_current_context(silent=True) is None


# Property: Context attributes preservation after push/pop cycle
@given(st.booleans(), st.booleans(), st.booleans())
@settings(max_examples=1000)
def test_context_attributes_preserved(color, resilient_parsing, show_default):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    cmd = Command('test')
    ctx = Context(cmd, color=color, resilient_parsing=resilient_parsing, show_default=show_default)
    
    # Store original attributes
    original_color = ctx.color
    original_resilient = ctx.resilient_parsing
    original_show = ctx.show_default
    
    # Push and retrieve
    push_context(ctx)
    retrieved = get_current_context(silent=False)
    
    # Verify attributes match
    assert retrieved.color == original_color
    assert retrieved.resilient_parsing == original_resilient
    assert retrieved.show_default == original_show
    
    pop_context()


# Property: Stack manipulation doesn't affect other thread-local data
@given(st.data())
@settings(max_examples=1000)
def test_local_dict_isolation(data):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    # Set some other thread-local data
    _local.custom_data = "test_value"
    _local.number = 42
    
    # Perform push/pop operations
    num_ops = data.draw(st.integers(min_value=1, max_value=10))
    cmd = Command('test')
    
    for _ in range(num_ops):
        ctx = Context(cmd)
        push_context(ctx)
    
    # Verify other data is preserved
    assert _local.custom_data == "test_value"
    assert _local.number == 42
    
    # Clean up
    for _ in range(num_ops):
        pop_context()
    
    # Data should still be there
    assert _local.custom_data == "test_value"
    assert _local.number == 42
    
    # Clean up custom data
    del _local.custom_data
    del _local.number


# Property: resolve_color_default consistency with nested contexts
@given(st.lists(st.one_of(st.none(), st.booleans()), min_size=1, max_size=5))
@settings(max_examples=1000)
def test_resolve_color_nested_contexts(color_values):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    contexts = []
    for color in color_values:
        cmd = Command(f'test{len(contexts)}')
        ctx = Context(cmd, color=color)
        contexts.append(ctx)
        push_context(ctx)
    
    # Should resolve to the topmost context's color
    result = resolve_color_default(None)
    assert result == contexts[-1].color
    
    # Pop all contexts
    for _ in contexts:
        pop_context()


# Property: get_current_context with invalid state
@given(st.data())
@settings(max_examples=1000)
def test_get_current_context_corrupted_state(data):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    # Corrupt the stack in various ways
    corruption_type = data.draw(st.sampled_from(['no_stack', 'non_list', 'non_context']))
    
    if corruption_type == 'no_stack':
        # Remove stack attribute
        if hasattr(_local, 'stack'):
            delattr(_local, 'stack')
        
        # Should raise when not silent
        with pytest.raises(RuntimeError):
            get_current_context(silent=False)
        
        # Should return None when silent
        assert get_current_context(silent=True) is None
        
    elif corruption_type == 'non_list':
        # Set stack to non-list
        _local.stack = "not_a_list"
        
        # Should raise when not silent
        with pytest.raises(RuntimeError):
            get_current_context(silent=False)
        
        # Should return None when silent
        assert get_current_context(silent=True) is None
        
        # Clean up
        _local.stack = []
        
    elif corruption_type == 'non_context':
        # Push non-Context objects
        _local.stack = [1, 2, 3, "string", None]
        
        # Will return the last item but won't verify it's a Context
        result = get_current_context(silent=True)
        assert result is None  # The last item is None
        
        # Clean up
        _local.stack = []