#!/usr/bin/env python3
"""
Minimal reproduction of UnboundLocalError in yq.yq function.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import io
import yq

# The bug occurs when jq command is not available
# The code tries to assert jq.stdin is not None at line 211
# But if jq subprocess fails to start, jq is never assigned

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
    
    # This will fail if jq is not installed or not on PATH
    # The bug is that it will raise UnboundLocalError instead of 
    # the intended error message about jq not being installed
    
    # First let's check if jq is available
    import subprocess
    try:
        subprocess.run(["jq", "--version"], capture_output=True, check=True)
        print("jq is installed, simulating its absence...")
        
        # Simulate jq not being available by using a bad PATH
        import os
        original_path = os.environ.get('PATH', '')
        os.environ['PATH'] = '/nonexistent'
        
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
            print(f"This should have been a clean error about jq not being installed")
            return True
        finally:
            os.environ['PATH'] = original_path
            
    except subprocess.CalledProcessError:
        print("jq is not installed, trying to trigger the bug directly...")
        
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
            print(f"This should have been a clean error about jq not being installed")
            return True
        except Exception as e:
            if exit_called and "jq" in str(exit_message):
                print(f"Correct behavior: Got expected error message about jq: {exit_message}")
                return False
    
    if exit_called:
        print(f"Exit was called with: {exit_message}")
    
    return False


if __name__ == "__main__":
    print("Testing for UnboundLocalError bug in yq.yq()...")
    bug_found = reproduce_bug()
    
    if bug_found:
        print("\n✗ Bug confirmed: UnboundLocalError when jq is not available")
        print("The code references 'jq.stdin' at line 211 but 'jq' may not be defined if subprocess.Popen fails")
    else:
        print("\n✓ No bug found - error handling works correctly")