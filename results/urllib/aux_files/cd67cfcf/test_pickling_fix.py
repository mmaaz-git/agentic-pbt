#!/usr/bin/env python3
"""Test that the proposed pickling fix would work"""

import pickle
import urllib.error
import io

# Monkey-patch the fixes to test them

# Fix for URLError
def urlerror_reduce(self):
    args = (self.reason,)
    if hasattr(self, 'filename') and self.filename is not None:
        args = (self.reason, self.filename)
    return (self.__class__, args)

urllib.error.URLError.__reduce__ = urlerror_reduce

# Fix for HTTPError
def httperror_reduce(self):
    return (self.__class__, (self.url, self.code, self.msg, self.hdrs, self.fp))

urllib.error.HTTPError.__reduce__ = httperror_reduce

# Fix for ContentTooShortError
def content_too_short_reduce(self):
    return (self.__class__, (self.reason, self.content))

urllib.error.ContentTooShortError.__reduce__ = content_too_short_reduce

# Now test that pickling works

print("Testing URLError pickling with fix:")
err1 = urllib.error.URLError("Connection failed", "http://example.com")
print(f"  Before: filename={err1.filename}")
pickled1 = pickle.dumps(err1)
unpickled1 = pickle.loads(pickled1)
print(f"  After: filename={unpickled1.filename}")
print(f"  Success: {err1.filename == unpickled1.filename}")

print("\nTesting HTTPError pickling with fix:")
err2 = urllib.error.HTTPError("http://example.com", 404, "Not Found", {'Content-Type': 'text/html'}, None)
print(f"  Before: code={err2.code}, msg={err2.msg}")
pickled2 = pickle.dumps(err2)
unpickled2 = pickle.loads(pickled2)
print(f"  After: code={unpickled2.code}, msg={unpickled2.msg}")
print(f"  Success: {err2.code == unpickled2.code and err2.msg == unpickled2.msg}")

print("\nTesting ContentTooShortError pickling with fix:")
err3 = urllib.error.ContentTooShortError("Download incomplete", b"partial content")
print(f"  Before: content={err3.content}")
pickled3 = pickle.dumps(err3)
unpickled3 = pickle.loads(pickled3)
print(f"  After: content={unpickled3.content}")
print(f"  Success: {err3.content == unpickled3.content}")