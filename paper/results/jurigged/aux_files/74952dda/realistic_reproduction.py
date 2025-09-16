#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.codetools import Info, Extent, use_info

# More realistic example with emoji or non-ASCII characters
print("=== Realistic scenario with emoji ===")
lines = ['def hello():', '    print("Hello 🦄 World")', '    return True']
line_idx = 1
start_col = 18  # Position in the middle of the emoji
end_col = 20

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
        lineno=line_idx + 1,
        col_offset=start_col,
        end_lineno=line_idx + 1,
        end_col_offset=end_col
    )
    
    try:
        result = info.get_segment(ext)
        print(f"Result: {repr(result)}")
    except UnicodeDecodeError as e:
        print(f"BUG: UnicodeDecodeError when extracting segment from code with emoji!")
        print(f"Error: {e}")
        print(f"Line: {lines[line_idx]}")
        print(f"This would fail for any Python code containing emojis or non-ASCII characters")

print("\n=== Another realistic case with accented characters ===")
lines = ['# Café implementation', 'def café_method():', '    pass']
line_idx = 0
start_col = 4  # Should extract "é implementation"
end_col = 20

info2 = Info(
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
    ext2 = Extent(
        lineno=1,
        col_offset=start_col,
        end_lineno=1,
        end_col_offset=end_col
    )
    
    try:
        result = info2.get_segment(ext2)
        print(f"Result: {repr(result)}")
    except UnicodeDecodeError as e:
        print(f"BUG: UnicodeDecodeError with accented characters!")
        print(f"Error: {e}")
        print(f"Line: {lines[0]}")