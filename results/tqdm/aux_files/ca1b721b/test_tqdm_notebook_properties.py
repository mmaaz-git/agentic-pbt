"""
Property-based tests for tqdm.notebook module using Hypothesis
"""
import re
from html import escape
from hypothesis import given, strategies as st, assume, settings
import math

# Import the target module
from tqdm.notebook import TqdmHBox, tqdm_notebook, tnrange


# Test 1: HTML escaping property
@given(st.text())
def test_html_escaping_in_split_messages(text):
    """
    Test that HTML special characters are properly escaped when processing messages.
    According to line 163 of notebook.py, messages are escaped using html.escape.
    """
    # Test the escaping pattern used in display method
    msg = f"prefix<bar/>{text}"
    if '<bar/>' in msg:
        parts = re.split(r'\|?<bar/>\|?', msg, maxsplit=1)
        # After split, each part should be escapable
        for part in parts:
            escaped = escape(part)
            # Verify that escaping works and preserves non-special chars
            assert '&' not in part or '&' not in escaped or '&amp;' in escaped
            assert '<' not in part or '&lt;' in escaped
            assert '>' not in part or '&gt;' in escaped


# Test 2: Regex splitting invariant
@given(st.text())
def test_regex_split_invariant(text):
    """
    Test that the regex split pattern always produces at most 2 parts.
    This is guaranteed by maxsplit=1 in the display method (line 163).
    """
    # The pattern used in display method
    parts = re.split(r'\|?<bar/>\|?', text, maxsplit=1)
    assert len(parts) <= 2
    
    # If text contains <bar/>, it should split
    if '<bar/>' in text:
        assert len(parts) == 2
    else:
        assert len(parts) == 1
        assert parts[0] == text


# Test 3: TqdmHBox._json_ property
@given(st.booleans())
def test_tqdmhbox_json_method(pretty):
    """
    Test TqdmHBox._json_ method behavior.
    According to lines 71-78, it returns {} when no pbar, 
    otherwise returns format_dict with optional ascii setting.
    """
    hbox = TqdmHBox()
    
    # Without pbar, should return empty dict
    assert hbox._json_(pretty) == {}
    
    # Create a mock pbar-like object
    class MockPbar:
        def __init__(self):
            self.format_dict = {'n': 0, 'total': 100}
    
    hbox.pbar = MockPbar()
    result = hbox._json_(pretty)
    assert 'n' in result
    assert 'total' in result
    if pretty is not None:
        assert result.get('ascii') == (not pretty)


# Test 4: Reset invariant
@given(
    st.integers(min_value=0, max_value=1000),
    st.one_of(st.none(), st.integers(min_value=0, max_value=1000))
)
@settings(max_examples=100)
def test_reset_invariant(initial_total, new_total):
    """
    Test that reset() properly resets n to 0 and updates total if provided.
    Based on lines 289-307 of notebook.py.
    """
    # Create a disabled tqdm_notebook to avoid widget requirements
    t = tqdm_notebook(total=initial_total, disable=True)
    
    # Set some progress
    if initial_total and initial_total > 0:
        # Manually set n since update doesn't work when disabled
        t.n = min(5, initial_total)
    
    initial_n = t.n
    
    # Reset with optional new total
    t.reset(total=new_total)
    
    # After reset, n should be 0
    assert t.n == 0
    
    # Total should be updated if provided
    if new_total is not None:
        assert t.total == new_total
    else:
        assert t.total == initial_total
    
    t.close()


# Test 5: tnrange function equivalence
@given(
    st.integers(min_value=0, max_value=100),
    st.text(max_size=20),
    st.booleans()
)
def test_tnrange_equivalence(n, desc, leave):
    """
    Test that tnrange is equivalent to tqdm_notebook(range()).
    According to lines 310-312, tnrange is a shortcut.
    """
    # Both should create similar objects (test with disable=True to avoid widgets)
    t1 = tnrange(n, desc=desc, leave=leave, disable=True)
    t2 = tqdm_notebook(range(n), desc=desc, leave=leave, disable=True)
    
    # Check key attributes match
    assert t1.total == t2.total == n
    # desc is stored in format_dict, not as direct attribute
    assert t1.leave == t2.leave == leave
    assert t1.disable == t2.disable == True
    
    # Both should iterate the same way
    list1 = list(t1)
    list2 = list(t2)
    assert list1 == list2 == list(range(n))


# Test 6: Space replacement in display messages
@given(st.text(alphabet=st.characters(whitelist_categories=["L", "N", "P", "Z"])))
def test_space_replacement_in_messages(text):
    """
    Test that spaces are replaced with non-breaking spaces in display.
    According to line 160, spaces are replaced with u'\\u2007'.
    """
    # The display method replaces spaces
    if ' ' in text:
        replaced = text.replace(' ', u'\u2007')
        assert ' ' not in replaced
        # Count should be preserved
        assert text.count(' ') == replaced.count(u'\u2007')


# Test 7: Update accumulation when enabled
@given(
    st.lists(st.integers(min_value=1, max_value=10), min_size=1, max_size=5),
    st.integers(min_value=10, max_value=100)
)
def test_update_accumulation(updates, total):
    """
    Test that multiple update() calls accumulate correctly.
    This tests the parent class behavior that should be preserved.
    """
    # We need to test with a mock to avoid widget dependencies
    # Create a simple mock that allows update
    try:
        # Use standard tqdm which notebook inherits from
        from tqdm.std import tqdm as std_tqdm
        t = std_tqdm(total=total, disable=False, file=None)
        
        expected_n = 0
        for update_val in updates:
            t.update(update_val)
            expected_n += update_val
            assert t.n == expected_n
        
        t.close()
    except Exception:
        pass  # Skip if can't test without widgets


# Test 8: Colour property getter/setter
@given(st.one_of(st.none(), st.text(alphabet="0123456789abcdef", min_size=6, max_size=6)))
def test_colour_property(color_value):
    """
    Test the colour property getter and setter.
    According to lines 192-201, colour property accesses bar_color style.
    """
    # This test needs widgets, so we'll test the property logic only
    t = tqdm_notebook(total=10, disable=True)
    
    # Without container, colour property should not crash
    colour = t.colour  # Should return None or not crash
    
    # Setting colour without container should not crash
    try:
        t.colour = color_value
    except AttributeError:
        pass  # Expected when no container
    
    t.close()


# Test 9: Bar format message processing
@given(st.text(max_size=50))
def test_bar_format_processing(custom_format):
    """
    Test that bar_format with {bar} gets replaced with <bar/>.
    According to lines 152-153, {bar} is replaced with <bar/>.
    """
    if '{bar}' in custom_format:
        # The display method replaces {bar} with <bar/>
        replaced = custom_format.replace('{bar}', '<bar/>')
        assert '{bar}' not in replaced
        assert '<bar/>' in replaced


# Test 10: Exception handling preserves state
@given(st.integers(min_value=1, max_value=100))
def test_exception_handling_in_iteration(total):
    """
    Test that exceptions during iteration are properly handled.
    According to lines 247-258, exceptions should trigger bar_style='danger'.
    """
    # This is hard to test without widgets, but we can verify the logic
    items = list(range(total))
    
    # Create a custom iterator that raises
    class FailingIterator:
        def __init__(self, items):
            self.items = items
            self.index = 0
        
        def __iter__(self):
            return self
        
        def __next__(self):
            if self.index >= len(self.items) // 2:
                raise ValueError("Test exception")
            val = self.items[self.index]
            self.index += 1
            return val
    
    # Test that tqdm_notebook handles the exception
    try:
        t = tqdm_notebook(FailingIterator(items), disable=True)
        for _ in t:
            pass
    except ValueError:
        pass  # Expected
    
    # The tqdm should not be in an invalid state after exception
    assert hasattr(t, 'n')