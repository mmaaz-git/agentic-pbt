import argcomplete.io
import os

# Track opened files
original_open = open
opened_devnull = None

def tracking_open(*args, **kwargs):
    global opened_devnull
    f = original_open(*args, **kwargs)
    if args and args[0] == os.devnull:
        opened_devnull = f
    return f

import builtins
builtins.open = tracking_open

# Use mute_stdout
with argcomplete.io.mute_stdout():
    print("test")

# Check if file was closed
print(f"mute_stdout - File closed: {opened_devnull.closed}")  # False (BUG!)

# Reset and test mute_stderr for comparison
opened_devnull = None
with argcomplete.io.mute_stderr():
    print("test", file=__import__('sys').stderr)

print(f"mute_stderr - File closed: {opened_devnull.closed}")  # True (correct!)