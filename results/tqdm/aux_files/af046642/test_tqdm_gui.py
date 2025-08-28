"""Property-based tests for tqdm.gui module"""

import math
import sys
from collections import deque
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings, assume

# Mock matplotlib to avoid GUI dependencies
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()

import tqdm.gui


# Strategy for valid tqdm parameters
@st.composite
def tqdm_params(draw):
    """Generate valid parameters for tqdm_gui initialization"""
    total = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=10000)))
    desc = draw(st.one_of(st.none(), st.text(max_size=100)))
    mininterval = draw(st.floats(min_value=0, max_value=10, allow_nan=False))
    maxinterval = draw(st.floats(min_value=mininterval, max_value=100, allow_nan=False))
    disable = draw(st.booleans())
    unit = draw(st.one_of(st.none(), st.text(min_size=1, max_size=10)))
    unit_scale = draw(st.booleans())
    leave = draw(st.booleans())
    colour = draw(st.sampled_from(['r', 'g', 'b', 'c', 'm', 'y', 'k']))
    
    return {
        'total': total,
        'desc': desc,
        'mininterval': mininterval,
        'maxinterval': maxinterval,
        'disable': disable,
        'unit': unit,
        'unit_scale': unit_scale,
        'leave': leave,
        'colour': colour
    }


@given(params=tqdm_params())
@settings(max_examples=100)
def test_mininterval_constraint(params):
    """Test that mininterval is always at least 0.5 after initialization (unless disabled)"""
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        pbar = tqdm.gui.tqdm_gui(**params)
        
        if not pbar.disable:
            # The code explicitly sets: self.mininterval = max(self.mininterval, 0.5)
            assert pbar.mininterval >= 0.5, f"mininterval {pbar.mininterval} should be >= 0.5"
        
        pbar.close()


@given(params=tqdm_params())
@settings(max_examples=100)
def test_data_structure_types(params):
    """Test that xdata/ydata/zdata are correct types based on total"""
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        pbar = tqdm.gui.tqdm_gui(**params)
        
        if not pbar.disable:
            if params['total'] is not None:
                # When total is known, should use lists
                assert isinstance(pbar.xdata, list), "xdata should be list when total is known"
                assert isinstance(pbar.ydata, list), "ydata should be list when total is known"
                assert isinstance(pbar.zdata, list), "zdata should be list when total is known"
            else:
                # When total is unknown, should use deques
                assert isinstance(pbar.xdata, deque), "xdata should be deque when total is unknown"
                assert isinstance(pbar.ydata, deque), "ydata should be deque when total is unknown"
                assert isinstance(pbar.zdata, deque), "zdata should be deque when total is unknown"
        
        pbar.close()


@given(params=tqdm_params())
@settings(max_examples=100)
def test_gui_elements_creation(params):
    """Test that GUI elements are created when not disabled"""
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        pbar = tqdm.gui.tqdm_gui(**params)
        
        if not pbar.disable:
            # These attributes should be set when GUI is active
            assert hasattr(pbar, 'fig'), "Should have matplotlib figure"
            assert hasattr(pbar, 'ax'), "Should have matplotlib axes"
            assert hasattr(pbar, 'line1'), "Should have line1 for current rate"
            assert hasattr(pbar, 'line2'), "Should have line2 for average rate"
            assert hasattr(pbar, 'toolbar'), "Should store original toolbar setting"
            assert hasattr(pbar, 'wasion'), "Should store original interactive mode"
            
            if params['total'] is not None:
                assert hasattr(pbar, 'hspan'), "Should have progress bar span when total is known"
        
        pbar.close()


@given(params=tqdm_params())
@settings(max_examples=100)
def test_close_disables_instance(params):
    """Test that close() properly disables the instance"""
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        pbar = tqdm.gui.tqdm_gui(**params)
        original_disabled = pbar.disable
        
        pbar.close()
        
        # After close, should be disabled
        assert pbar.disable is True, "Instance should be disabled after close()"


@given(n=st.integers(min_value=0, max_value=100))
@settings(max_examples=50)
def test_tgrange_equivalence(n):
    """Test that tgrange(n) is equivalent to tqdm_gui(range(n))"""
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        # Create using tgrange
        pbar1 = tqdm.gui.tgrange(n)
        
        # Create using tqdm_gui(range())
        pbar2 = tqdm.gui.tqdm_gui(range(n))
        
        # They should have the same total
        assert pbar1.total == pbar2.total == n
        
        # Clean up
        pbar1.close()
        pbar2.close()


@given(
    params=tqdm_params(),
    updates=st.lists(st.integers(min_value=1, max_value=100), min_size=0, max_size=10)
)
@settings(max_examples=50)
def test_display_data_accumulation(params, updates):
    """Test that display() accumulates data points correctly"""
    
    # Only test with known total for predictable behavior
    params['total'] = 100
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        pbar = tqdm.gui.tqdm_gui(**params)
        
        if not pbar.disable:
            initial_data_len = len(pbar.xdata)
            
            # Perform updates and display
            for delta in updates:
                pbar.update(delta)
                pbar.display()
            
            # Data should have grown by the number of display calls
            expected_len = initial_data_len + len(updates)
            assert len(pbar.xdata) == expected_len, f"Expected {expected_len} data points, got {len(pbar.xdata)}"
            assert len(pbar.ydata) == expected_len, f"Expected {expected_len} data points, got {len(pbar.ydata)}"
            assert len(pbar.zdata) == expected_len, f"Expected {expected_len} data points, got {len(pbar.zdata)}"
        
        pbar.close()


@given(
    iterable_size=st.integers(min_value=0, max_value=100),
    chunk_sizes=st.lists(st.integers(min_value=1, max_value=10), min_size=0, max_size=20)
)
@settings(max_examples=50)
def test_iteration_consistency(iterable_size, chunk_sizes):
    """Test that iterating with tqdm_gui maintains consistency"""
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        items = list(range(iterable_size))
        pbar = tqdm.gui.tqdm_gui(items)
        
        if not pbar.disable:
            # Initial state
            assert pbar.n == 0, "Should start at 0"
            assert pbar.total == iterable_size, f"Total should be {iterable_size}"
            
            # Simulate iteration by updating in chunks
            total_updated = 0
            for chunk_size in chunk_sizes:
                if total_updated + chunk_size <= iterable_size:
                    pbar.update(chunk_size)
                    total_updated += chunk_size
                    assert pbar.n == total_updated, f"n should be {total_updated}, got {pbar.n}"
        
        pbar.close()


@given(desc=st.text(max_size=200))
@settings(max_examples=50)
def test_clear_method_is_noop(desc):
    """Test that clear() method is a no-op (as implemented)"""
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        pbar = tqdm.gui.tqdm_gui(total=100, desc=desc)
        
        if not pbar.disable:
            # Store initial state
            initial_xdata = pbar.xdata.copy() if hasattr(pbar, 'xdata') else None
            initial_ydata = pbar.ydata.copy() if hasattr(pbar, 'ydata') else None
            initial_zdata = pbar.zdata.copy() if hasattr(pbar, 'zdata') else None
            
            # Call clear (which should do nothing)
            pbar.clear()
            pbar.clear("ignored", "args", also="ignored")
            
            # Data should be unchanged
            if initial_xdata is not None:
                assert pbar.xdata == initial_xdata, "xdata should not change after clear()"
                assert pbar.ydata == initial_ydata, "ydata should not change after clear()"
                assert pbar.zdata == initial_zdata, "zdata should not change after clear()"
        
        pbar.close()