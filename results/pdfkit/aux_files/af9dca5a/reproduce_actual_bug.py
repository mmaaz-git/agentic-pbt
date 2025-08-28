#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.source import Source

print("=== BUG: TypeError when passing non-string/non-filelike object with type='file' ===")
print("\nThe Source class accepts any object as source, but checkFiles() assumes")
print("it's either a string path, a list of paths, or has a 'read' method.")
print("\nWhen given an arbitrary object without 'read' method, it crashes:\n")

class CustomObject:
    def __str__(self):
        return "CustomObject"

obj = CustomObject()
print(f"Creating Source with object: {obj}")
print("Source(obj, 'file')")

try:
    s = Source(obj, 'file')
    print("SUCCESS: Source created")
except TypeError as e:
    print(f"\n*** BUG FOUND ***")
    print(f"TypeError: {e}")
    print("\nThis happens in checkFiles() at line 39:")
    print("  if not hasattr(self.source, 'read') and not os.path.exists(self.source):")
    print("                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    print("os.path.exists() cannot handle arbitrary objects!")
    print("\nExpected behavior: Should raise a more meaningful error like:")
    print("  'Invalid source type for file: expected string path or file-like object'")

print("\n" + "="*70)
print("\n=== ADDITIONAL ISSUE: Poor error message for empty string ===")
print("\nWhen an empty string is passed as a file path:")
try:
    s = Source("", "file")
except IOError as e:
    print(f"Error message: '{e}'")
    print("\nThe error 'No such file: ' (with nothing after colon) is confusing.")
    print("A better message would be: 'No such file: <empty string>' or")
    print("'Invalid file path: empty string provided'")