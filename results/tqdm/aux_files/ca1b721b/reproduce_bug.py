"""
Minimal reproduction of tqdm.notebook bug
"""
from tqdm.notebook import tqdm_notebook

# This triggers the bug when IProgress widget is not available
try:
    # Create tqdm_notebook with gui=False, disable=False
    # This will fail during initialization if ipywidgets is not available
    t = tqdm_notebook(range(10), gui=False, disable=False)
    t.close()
except ImportError as e:
    print(f"ImportError during initialization: {e}")
    # The tqdm object was partially created and will be garbage collected
    # This triggers __del__ which calls close() which tries to call self.disp
    # But disp was never set because initialization failed after line 224