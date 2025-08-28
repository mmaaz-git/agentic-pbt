"""Minimal test to reproduce the close() bug in tqdm.gui"""

import sys
from unittest.mock import MagicMock, patch

# Create a proper mock for matplotlib
mock_mpl = MagicMock()
mock_mpl.rcParams = {'toolbar': 'test_toolbar'}
mock_pyplot = MagicMock()

# Mock figure and axes properly
mock_fig = MagicMock()
mock_ax = MagicMock()
mock_line = MagicMock()
mock_ax.plot.return_value = [mock_line]  # Return a list with one line object
mock_ax.axhspan = MagicMock(return_value=MagicMock())
mock_pyplot.subplots = MagicMock(return_value=(mock_fig, mock_ax))
mock_pyplot.isinteractive = MagicMock(return_value=False)
mock_pyplot.axhspan = MagicMock(return_value=MagicMock())
mock_pyplot.ioff = MagicMock()
mock_pyplot.ion = MagicMock()
mock_pyplot.pause = MagicMock()
mock_pyplot.close = MagicMock()

sys.modules['matplotlib'] = mock_mpl
sys.modules['matplotlib.pyplot'] = mock_pyplot

import tqdm.gui


def test_double_close_causes_keyerror():
    """Test that calling close() twice causes a KeyError"""
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        # Create a tqdm_gui instance
        pbar = tqdm.gui.tqdm_gui(total=100)
        
        # First close should work fine
        pbar.close()
        
        # Second close should NOT raise KeyError, but it does
        # This is the bug - close() is not idempotent
        try:
            pbar.close()
            print("✓ Second close() succeeded without error")
        except KeyError as e:
            print(f"✗ BUG FOUND: Second close() raised KeyError: {e}")
            return True
    
    return False


def test_del_after_close():
    """Test that __del__ after explicit close() causes issues"""
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        # Create a tqdm_gui instance
        pbar = tqdm.gui.tqdm_gui(total=100)
        
        # Explicitly close
        pbar.close()
        
        # Now when the object is deleted, __del__ will call close() again
        # This should not cause an error, but it does
        del pbar  # This triggers __del__ which calls close() again
        
        print("Testing __del__ after close - check for KeyError above")


if __name__ == "__main__":
    print("Testing tqdm.gui close() idempotency...\n")
    
    bug_found = test_double_close_causes_keyerror()
    
    if bug_found:
        print("\n" + "="*60)
        print("CONFIRMED BUG: tqdm.gui.tqdm_gui.close() is not idempotent")
        print("Calling close() multiple times raises KeyError")
        print("="*60)