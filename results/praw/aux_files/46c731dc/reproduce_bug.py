"""Minimal reproduction of objectify bug with integer lists."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

import praw
from praw.objector import Objector

# Create Reddit instance (with minimal config)
reddit = praw.Reddit(
    client_id="test",
    client_secret="test",
    user_agent="test"
)

# Create objector
objector = Objector(reddit)

# Test cases that should work but fail
test_cases = [
    [0],  # Single integer
    [1, 2, 3],  # Multiple integers
    [42],  # Another integer
    ["string", 123],  # Mixed types
]

for test in test_cases:
    try:
        result = objector.objectify(test)
        print(f"✓ {test} -> {result}")
    except TypeError as e:
        print(f"✗ {test} -> TypeError: {e}")
    except Exception as e:
        print(f"✗ {test} -> {type(e).__name__}: {e}")