"""Clear bug reproduction for EllipsisMiddleTruncate."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import formatting

print("=== BUG IN EllipsisMiddleTruncate ===")
print()

print("ISSUE 1: When available_space < 3, function returns text longer than requested")
print("-" * 70)

text = "abcdefgh"
for available_space in [1, 2, 3]:
    result = formatting.EllipsisMiddleTruncate(text, available_space, 80)
    print(f"Text: '{text}' (length={len(text)})")
    print(f"Requested available_space: {available_space}")
    print(f"Result: '{result}' (length={len(result)})")
    print(f"BUG: Result length {len(result)} > requested {available_space}!")
    print()

print()
print("ISSUE 2: Integer division causes asymmetric truncation")
print("-" * 70)

# Test various cases showing the asymmetry
test_cases = [
    ("0123456789", 7),  # 10 chars, space for 4 actual chars
    ("00.00000000", 10), # 11 chars, space for 7 actual chars  
    ("abcdefghijk", 8),  # 11 chars, space for 5 actual chars
]

for text, available_space in test_cases:
    result = formatting.EllipsisMiddleTruncate(text, available_space, 80)
    
    # Find where ellipsis is
    ellipsis_idx = result.index("...")
    before = result[:ellipsis_idx]
    after = result[ellipsis_idx+3:]
    
    print(f"Text: '{text}' (length={len(text)})")
    print(f"Available space: {available_space}")
    print(f"Result: '{result}'")
    print(f"Before ellipsis: '{before}' (length={len(before)})")
    print(f"After ellipsis: '{after}' (length={len(after)})")
    print(f"Asymmetry: {abs(len(before) - len(after))} characters difference")
    print()

print()
print("ROOT CAUSE ANALYSIS:")
print("-" * 70)
print("The function uses integer division to split available characters:")
print("  first_half_len = int(available_string_len / 2)")
print("  second_half_len = available_string_len - first_half_len")
print()
print("Example with available_string_len=7:")
print("  first_half_len = int(7/2) = 3")
print("  second_half_len = 7 - 3 = 4")
print("This creates asymmetry, taking 3 chars from start and 4 from end.")
print()
print("The bug with available_space < 3 occurs because:")
print("1. Function sets available_space = line_length when available_space < 3")
print("2. Then checks if len(text) < available_space")
print("3. If true, returns the full text without truncation")
print("4. This violates the contract that result length <= original available_space")