"""Simple reproduction of the double close() bug without matplotlib dependencies"""

import sys
from unittest.mock import MagicMock, patch
from collections import deque

# Setup comprehensive matplotlib mocks
mock_mpl = MagicMock()
mock_mpl.rcParams = {'toolbar': 'test'}

mock_fig = MagicMock()
mock_ax = MagicMock()
mock_line1 = MagicMock()
mock_line2 = MagicMock()
mock_hspan = MagicMock()

# Configure plot to return tuple of lines
mock_ax.plot = MagicMock(side_effect=lambda *args, **kwargs: (mock_line1,) if mock_ax.plot.call_count % 2 == 1 else (mock_line2,))
mock_ax.set_ylim = MagicMock()
mock_ax.set_xlim = MagicMock()
mock_ax.set_xlabel = MagicMock()
mock_ax.set_ylabel = MagicMock()
mock_ax.legend = MagicMock()
mock_ax.grid = MagicMock()
mock_ax.yaxis.get_offset_text = MagicMock(return_value=MagicMock())
mock_ax.figure.canvas.draw = MagicMock()
mock_ax.set_title = MagicMock()

mock_pyplot = MagicMock()
mock_pyplot.subplots = MagicMock(return_value=(mock_fig, mock_ax))
mock_pyplot.axhspan = MagicMock(return_value=mock_hspan)
mock_pyplot.isinteractive = MagicMock(return_value=False)
mock_pyplot.ion = MagicMock()
mock_pyplot.ioff = MagicMock()
mock_pyplot.pause = MagicMock()
mock_pyplot.close = MagicMock()
mock_pyplot.ticklabel_format = MagicMock()

sys.modules['matplotlib'] = mock_mpl
sys.modules['matplotlib.pyplot'] = mock_pyplot

import tqdm.gui
import tqdm.std


def reproduce_double_close_bug():
    """Reproduce the bug where calling close() twice causes KeyError"""
    
    print("Creating tqdm_gui instance...")
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        # Create instance
        pbar = tqdm.gui.tqdm_gui(total=100)
        
        print(f"Instance created, _instances has {len(pbar._instances)} items")
        print(f"Instance is in _instances: {pbar in pbar._instances}")
        
        # First close
        print("\nCalling close() first time...")
        pbar.close()
        print(f"After first close, disabled={pbar.disable}")
        print(f"Instance is in _instances: {pbar in pbar._instances}")
        
        # Second close - this should be idempotent but raises KeyError
        print("\nCalling close() second time...")
        try:
            pbar.close()
            print("✓ Second close() succeeded - no bug")
            return False
        except KeyError as e:
            print(f"✗ BUG: Second close() raised KeyError!")
            print(f"  Error: {e}")
            return True


def reproduce_del_after_close_bug():
    """Reproduce the bug where __del__ after close() causes KeyError"""
    
    print("\n" + "="*60)
    print("Testing __del__ after explicit close()...")
    
    with patch('tqdm.gui.warn'):  # Suppress experimental warning
        pbar = tqdm.gui.tqdm_gui(total=100)
        print("Created instance, calling close()...")
        pbar.close()
        print("close() completed, now deleting object (triggers __del__)...")
        
        # This will trigger __del__ which calls close() again
        # Should be safe but causes KeyError
        del pbar
        print("(Check for KeyError exception above)")


if __name__ == "__main__":
    print("Testing tqdm.gui.tqdm_gui.close() idempotency")
    print("="*60)
    
    bug_found = reproduce_double_close_bug()
    
    if bug_found:
        reproduce_del_after_close_bug()
        
        print("\n" + "="*60)
        print("CONFIRMED BUG: tqdm.gui.tqdm_gui.close() is not idempotent")
        print("Multiple calls to close() or __del__ after close() cause KeyError")
        print("This violates the expected behavior that close() should be safe to call multiple times")