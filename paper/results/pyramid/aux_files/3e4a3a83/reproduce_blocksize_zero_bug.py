"""
Minimal reproduction of FileIter bug with block_size=0
"""
import sys
from io import BytesIO

sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.response import FileIter

# Create a file with content
content = b"This content should be read"
file_obj = BytesIO(content)

# Create FileIter with block_size=0
file_iter = FileIter(file_obj, block_size=0)

# Try to read the content
chunks = list(file_iter)
result = b''.join(chunks)

print(f"Original content: {repr(content)}")
print(f"FileIter result:  {repr(result)}")
print(f"Content lost: {content != result}")

# This is a bug: FileIter with block_size=0 returns empty content
# instead of reading the file
assert result == content, f"FileIter lost content! Expected {content}, got {result}"