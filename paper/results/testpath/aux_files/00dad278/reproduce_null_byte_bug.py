"""Minimal reproducer for null byte bug in testpath.commands.prepend_to_path"""

import os
import testpath.commands as commands

# Save original PATH
original_path = os.environ.get('PATH', '')

try:
    # This should handle null bytes gracefully, but it crashes
    commands.prepend_to_path('\x00')
    print("Bug not reproduced - prepend_to_path accepted null byte")
except ValueError as e:
    print(f"Bug reproduced! ValueError: {e}")
    print("prepend_to_path crashes when given a null byte in the directory name")
finally:
    # Restore PATH
    os.environ['PATH'] = original_path