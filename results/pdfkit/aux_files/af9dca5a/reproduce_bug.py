#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.source import Source

# Bug 1: checkFiles() is called even for non-file types
print("Testing Bug 1: checkFiles() called for 'string' type")
try:
    s = Source("nonexistent_file.txt", "string")
    print(f"  SUCCESS: Created Source with type='string', source={s.source}")
    print(f"  isString() = {s.isString()}")
    print(f"  isFile() = {s.isFile()}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\nTesting Bug 1: checkFiles() called for 'url' type")
try:
    s = Source("http://example.com", "url")
    print(f"  SUCCESS: Created Source with type='url', source={s.source}")
    print(f"  isUrl() = {s.isUrl()}")
    print(f"  isFile() = {s.isFile()}")
except Exception as e:
    print(f"  ERROR: {e}")

# Bug 2: TypeError when non-string object without 'read' method is passed with type='file'
print("\nTesting Bug 2: TypeError with non-string object")
class CustomObject:
    pass

try:
    obj = CustomObject()
    s = Source(obj, "file")
    print(f"  SUCCESS: Created Source with custom object")
except TypeError as e:
    print(f"  TypeError: {e}")
except IOError as e:
    print(f"  IOError: {e}")

# Bug 3: Checking the actual implementation bug
print("\nAnalyzing the implementation:")
print("  The bug is in __init__ method lines 19-20:")
print("  if self.type == 'file':")
print("      self.checkFiles()")
print("\n  But checkFiles() method (lines 33-40) doesn't check type again!")
print("  It directly calls os.path.exists() on self.source")
print("  This causes failures for 'string' and 'url' types with non-existent paths")