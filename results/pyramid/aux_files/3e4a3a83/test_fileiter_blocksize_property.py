"""
Property-based test that catches the FileIter block_size=0 bug
"""
import sys
from io import BytesIO

sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
from pyramid.response import FileIter


@given(
    content=st.binary(min_size=1, max_size=10000),
    block_size=st.integers(min_value=0, max_value=1000)
)
def test_fileiter_preserves_content_any_blocksize(content, block_size):
    """FileIter should preserve file content regardless of block_size value."""
    file_obj = BytesIO(content)
    
    file_iter = FileIter(file_obj, block_size=block_size)
    chunks = list(file_iter)
    result = b''.join(chunks)
    
    assert result == content, \
        f"FileIter with block_size={block_size} lost content. " \
        f"Expected {len(content)} bytes, got {len(result)} bytes"


if __name__ == "__main__":
    # This will fail, exposing the bug
    test_fileiter_preserves_content_any_blocksize()