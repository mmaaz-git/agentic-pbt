import threading
from hypothesis import given, strategies as st, assume, settings
from click.globals import push_context, pop_context, get_current_context, resolve_color_default
from click.core import Context, Command
import pytest


# Strategy for creating valid Context objects
@st.composite
def contexts(draw):
    cmd = Command('test')
    color = draw(st.one_of(st.none(), st.booleans()))
    ctx = Context(cmd, color=color)
    return ctx


# Property 1: Push/pop invariant - after push and pop, context stack should return to original state
@given(st.lists(contexts(), min_size=1, max_size=10))
@settings(max_examples=1000)
def test_push_pop_invariant(contexts_list):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    initial_context = get_current_context(silent=True)
    
    # Push all contexts
    for ctx in contexts_list:
        push_context(ctx)
    
    # Pop all contexts
    for _ in contexts_list:
        pop_context()
    
    # Should return to initial state
    final_context = get_current_context(silent=True)
    assert initial_context == final_context


# Property 2: Last-in-first-out (LIFO) property
@given(st.lists(contexts(), min_size=1, max_size=10))
@settings(max_examples=1000)
def test_lifo_property(contexts_list):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    # Push contexts and verify LIFO
    for ctx in contexts_list:
        push_context(ctx)
        current = get_current_context(silent=False)
        assert current is ctx
    
    # Pop and verify in reverse order
    for ctx in reversed(contexts_list):
        current = get_current_context(silent=False)
        assert current is ctx
        pop_context()


# Property 3: resolve_color_default preserves non-None values
@given(st.one_of(st.none(), st.booleans()))
@settings(max_examples=1000)
def test_resolve_color_preserves_non_none(color):
    if color is not None:
        assert resolve_color_default(color) == color


# Property 4: resolve_color_default with context
@given(st.booleans(), st.one_of(st.none(), st.booleans()))
@settings(max_examples=1000)
def test_resolve_color_with_context(ctx_color, passed_color):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    cmd = Command('test')
    ctx = Context(cmd, color=ctx_color)
    push_context(ctx)
    
    result = resolve_color_default(passed_color)
    
    if passed_color is not None:
        assert result == passed_color
    else:
        assert result == ctx_color
    
    pop_context()


# Property 5: get_current_context silent mode never raises
@given(st.booleans())
@settings(max_examples=1000)
def test_get_current_context_silent_never_raises(has_context):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    if has_context:
        cmd = Command('test')
        ctx = Context(cmd)
        push_context(ctx)
    
    # This should never raise
    result = get_current_context(silent=True)
    
    if has_context:
        assert result is not None
        pop_context()
    else:
        assert result is None


# Property 6: Multiple push without pop should not corrupt stack
@given(st.lists(contexts(), min_size=1, max_size=100))
@settings(max_examples=1000)
def test_multiple_push_maintains_stack_integrity(contexts_list):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    pushed = []
    for ctx in contexts_list:
        push_context(ctx)
        pushed.append(ctx)
        current = get_current_context(silent=False)
        assert current is ctx
    
    # Verify we can pop all contexts we pushed
    for _ in pushed:
        current = get_current_context(silent=False)
        assert current is not None
        pop_context()
    
    # Stack should be empty now
    assert get_current_context(silent=True) is None


# Property 7: Thread isolation - contexts should be thread-local
@given(st.lists(contexts(), min_size=2, max_size=5))
@settings(max_examples=100, deadline=10000)
def test_thread_isolation(contexts_list):
    if len(contexts_list) < 2:
        return
    
    # Clear main thread context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    results = {'thread1': None, 'thread2': None}
    
    def thread1_work():
        push_context(contexts_list[0])
        results['thread1'] = get_current_context(silent=True)
        pop_context()
    
    def thread2_work():
        push_context(contexts_list[1])
        results['thread2'] = get_current_context(silent=True)
        pop_context()
    
    t1 = threading.Thread(target=thread1_work)
    t2 = threading.Thread(target=thread2_work)
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # Each thread should have gotten its own context
    assert results['thread1'] is contexts_list[0]
    assert results['thread2'] is contexts_list[1]
    
    # Main thread should still have no context
    assert get_current_context(silent=True) is None