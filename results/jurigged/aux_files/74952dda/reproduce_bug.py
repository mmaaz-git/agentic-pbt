#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.codetools import Info, Extent, use_info

# Minimal reproduction of the bug
lines = ['0', '\x80', '0', '0', '0']
line_idx = 1
start_col = 0
end_col = 1

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
    ext = Extent(
        lineno=line_idx + 1,  # 1-based
        col_offset=start_col,
        end_lineno=line_idx + 1,
        end_col_offset=end_col
    )
    
    try:
        result = info.get_segment(ext)
        print(f"Result: {repr(result)}")
    except UnicodeDecodeError as e:
        print(f"Bug confirmed! UnicodeDecodeError: {e}")
        print(f"This happens when trying to extract a segment from line: {repr(lines[line_idx])}")
        print(f"The line contains a non-ASCII character that gets split incorrectly")
        
        # Show what's happening
        line = lines[line_idx]
        print(f"\nLine content: {repr(line)}")
        print(f"Line encoded: {line.encode()}")
        print(f"Trying to slice bytes [{start_col}:{end_col}]: {line.encode()[start_col:end_col]}")
        print("This slice splits a multi-byte UTF-8 character, causing decode to fail")