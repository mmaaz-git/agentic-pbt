#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.codetools import Info, Extent, use_info

# Test multi-line extraction with Unicode
lines = ['def test():', '    emoji = "🦄"', '    print(emoji)', '    return emoji']

info = Info(
    filename="test.py",
    module_name="test",
    source="\n".join(lines),
    lines=lines
)

with use_info(
    filename="test.py",
    module_name="test",
    source="\n".join(lines),
    lines=lines
):
    # Extract from middle of line 2 to middle of line 3
    ext = Extent(
        lineno=2,
        col_offset=14,  # After the emoji
        end_lineno=3,
        end_col_offset=10
    )
    
    try:
        result = info.get_segment(ext)
        print(f"Multi-line extraction result: {repr(result)}")
    except UnicodeDecodeError as e:
        print(f"BUG in multi-line case too! Error: {e}")
        
    # Try another case - extracting from middle of emoji
    ext2 = Extent(
        lineno=2,
        col_offset=13,  # In the middle of the emoji bytes
        end_lineno=3,
        end_col_offset=10
    )
    
    try:
        result2 = info.get_segment(ext2)
        print(f"Result 2: {repr(result2)}")
    except UnicodeDecodeError as e:
        print(f"BUG confirmed in multi-line case! Error: {e}")
        print("The same bug affects multi-line segment extraction")