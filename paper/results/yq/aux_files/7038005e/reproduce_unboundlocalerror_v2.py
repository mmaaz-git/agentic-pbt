#!/usr/bin/env python3
"""
Minimal reproduction of UnboundLocalError in yq.yq function.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import io
import yq

def reproduce_bug():
    """Reproduce the UnboundLocalError when jq is not installed."""
    
    # Create a simple TOML input
    toml_input = """
    [package]
    name = "test"
    """
    
    input_stream = io.StringIO(toml_input)
    output_stream = io.StringIO()
    
    exit_called = False
    exit_message = None
    
    def capture_exit(msg):
        nonlocal exit_called, exit_message
        exit_called = True
        exit_message = msg
        # Don't actually exit, just capture the message
    
    print("Testing with jq not installed...")
    
    try:
        yq.yq(
            input_streams=[input_stream],
            output_stream=output_stream,
            input_format="toml",
            output_format="json",
            jq_args=["."],
            exit_func=capture_exit
        )
    except UnboundLocalError as e:
        print(f"BUG FOUND: UnboundLocalError occurred: {e}")
        print(f"Error location: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
        print(f"This should have been a clean error about jq not being installed")
        return True
    except Exception as e:
        print(f"Got exception: {type(e).__name__}: {e}")
        if exit_called and "jq" in str(exit_message).lower():
            print(f"Correct behavior: Got expected error message about jq")
            return False
    
    if exit_called:
        print(f"Exit was called with: {exit_message}")
        if "jq" in str(exit_message).lower():
            print("Correct behavior: Error message mentions jq")
            return False
    
    return False


if __name__ == "__main__":
    print("Testing for UnboundLocalError bug in yq.yq()...")
    bug_found = reproduce_bug()
    
    if bug_found:
        print("\n✗ Bug confirmed: UnboundLocalError when jq is not available")
        print("The code references 'jq.stdin' at line 211 but 'jq' may not be defined if subprocess.Popen fails")
        print("\nThe bug is in /root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages/yq/__init__.py")
        print("Line 211: assert jq.stdin is not None")
        print("If subprocess.Popen on line 200-206 raises an OSError, 'jq' is never assigned")
        print("but line 211 still tries to access it in the try block.")
    else:
        print("\n✓ No bug found - error handling works correctly")