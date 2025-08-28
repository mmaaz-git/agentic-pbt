#!/usr/bin/env python3
"""Reproduce the bugs found in urllib.error module"""

import pickle
import urllib.error

print("=" * 60)
print("Bug 1: URLError sets filename=None even when not provided")
print("=" * 60)

# When filename is not provided (None), URLError still sets self.filename = None
err1 = urllib.error.URLError("Connection failed", None)
print(f"Created URLError with filename=None")
print(f"hasattr(err, 'filename'): {hasattr(err1, 'filename')}")
print(f"err.filename: {err1.filename}")
print("Expected: filename attribute should not be set when None is passed")
print("Actual: filename is set to None, making it impossible to distinguish")
print("        between 'no filename' and 'filename is None'")

print("\n" + "=" * 60)
print("Bug 2: URLError loses filename attribute when pickled")
print("=" * 60)

# URLError with a filename loses it after pickling
err2 = urllib.error.URLError("Connection failed", "http://example.com")
print(f"Original error - filename: {err2.filename}")

pickled = pickle.dumps(err2)
unpickled = pickle.loads(pickled)
print(f"After pickle - filename: {getattr(unpickled, 'filename', 'ATTRIBUTE MISSING')}")
print("Expected: filename should be preserved after pickling")
print("Actual: filename is lost during pickle/unpickle")

print("\n" + "=" * 60)
print("Bug 3: ContentTooShortError cannot be unpickled")
print("=" * 60)

# ContentTooShortError fails to unpickle
err3 = urllib.error.ContentTooShortError("Download incomplete", b"partial content")
print(f"Original error - content: {err3.content}")

try:
    pickled = pickle.dumps(err3)
    unpickled = pickle.loads(pickled)
    print(f"After pickle - content: {unpickled.content}")
except TypeError as e:
    print(f"Failed to unpickle: {e}")
    print("Expected: Should unpickle successfully")
    print("Actual: TypeError because __init__ is called without 'content' argument")