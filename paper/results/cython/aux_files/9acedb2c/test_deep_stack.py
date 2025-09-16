import io
import sys
from contextlib import redirect_stdout, redirect_stderr
import Cython.Debugging


def recursive_call(depth, max_depth):
    """Create a deep call stack."""
    if depth >= max_depth:
        f_out = io.StringIO()
        f_err = io.StringIO()
        with redirect_stdout(f_out), redirect_stderr(f_err):
            Cython.Debugging.print_call_chain("deep", depth)
        return f_out.getvalue()
    else:
        return recursive_call(depth + 1, max_depth)


# Test with various stack depths
for depth in [10, 100, 500, 1000]:
    try:
        output = recursive_call(0, depth)
        # Count how many "Called from" lines we get
        called_from_count = output.count("Called from:")
        print(f"Depth {depth}: Got {called_from_count} stack frames in output")
        if called_from_count < depth:
            print(f"  Warning: Expected at least {depth} frames, got {called_from_count}")
    except RecursionError as e:
        print(f"Depth {depth}: RecursionError - {e}")
    except Exception as e:
        print(f"Depth {depth}: Unexpected error - {type(e).__name__}: {e}")