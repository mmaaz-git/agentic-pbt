"""Reproduce UnboundLocalError bug in yq function."""

import sys
import io
import os

sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')
import yq

print("Reproducing UnboundLocalError bug in yq.yq()")
print("=" * 60)
print()

# Temporarily rename jq executable to simulate it not being found
print("Test 1: When jq executable is not found")
print("-" * 40)

# Create test input
test_yaml = "key: value"
input_stream = io.StringIO(test_yaml)
output_stream = io.StringIO()

# Mock the PATH to not include jq
original_path = os.environ.get('PATH', '')
os.environ['PATH'] = '/nonexistent'

exit_message = None
def capture_exit(msg):
    global exit_message
    exit_message = msg

try:
    yq.yq(
        input_streams=[input_stream],
        output_stream=output_stream,
        input_format="yaml",
        output_format="json",
        jq_args=["."],
        exit_func=capture_exit
    )
    print("No error occurred (unexpected)")
except UnboundLocalError as e:
    print(f"UnboundLocalError caught: {e}")
    print("This is a BUG - variable 'jq' accessed before assignment")
except Exception as e:
    print(f"Other error: {type(e).__name__}: {e}")
finally:
    # Restore PATH
    os.environ['PATH'] = original_path

print()
print("Analysis:")
print("-" * 40)
print("Looking at yq/__init__.py lines 196-211:")
print()
print("try:")
print("    jq = subprocess.Popen(...)")  
print("except OSError as e:")
print("    exit_func(msg.format(...))")
print("")
print("assert jq.stdin is not None  # Line 211 - BUG HERE!")
print()
print("The bug occurs because:")
print("1. If subprocess.Popen raises OSError, 'jq' is never assigned")
print("2. The exit_func is called but doesn't necessarily exit")
print("3. Line 211 tries to access 'jq.stdin' causing UnboundLocalError")
print()
print("This happens when jq is not installed or not on PATH")