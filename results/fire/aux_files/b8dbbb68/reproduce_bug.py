"""Reproduce the EllipsisMiddleTruncate bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import formatting

# Bug 1: When available_space < 3, it doesn't handle correctly
print("Bug 1: available_space < 3")
text = "abcdefgh"
result = formatting.EllipsisMiddleTruncate(text, 3, 80)
print(f"Input: '{text}', available_space=3")
print(f"Expected: '...' (just ellipsis)")
print(f"Actual: '{result}'")
print(f"Length: {len(result)}")
print()

# Bug with available_space = 2
result = formatting.EllipsisMiddleTruncate(text, 2, 80)
print(f"Input: '{text}', available_space=2")
print(f"Expected: fallback to line_length or handle gracefully")
print(f"Actual: '{result}'")
print(f"Length: {len(result)}")
print()

# Bug 2: Asymmetric truncation
print("Bug 2: Asymmetric truncation")
text = '00.00000000'
result = formatting.EllipsisMiddleTruncate(text, 10, 80)
print(f"Input: '{text}', available_space=10")
print(f"Result: '{result}'")
print(f"Length: {len(result)}")

# Find ellipsis position
ellipsis_pos = result.index("...")
before = ellipsis_pos
after = len(result) - ellipsis_pos - 3
print(f"Characters before ellipsis: {before}")
print(f"Characters after ellipsis: {after}")
print(f"Expected: roughly equal (3-4 each for available_space=10)")
print()

# Let's check the actual implementation
print("Let's trace through the logic:")
text = '00.00000000'
available_space = 10
line_length = 80

print(f"Text length: {len(text)} = 11")
print(f"Available space: {available_space}")
print(f"Text length >= available_space? {len(text) >= available_space}")

if available_space < len('...'):
    available_space = line_length
    print(f"Adjusted available_space to line_length: {available_space}")

if len(text) < available_space:
    print("Would return text as-is")
else:
    available_string_len = available_space - len('...')
    print(f"Available for actual text: {available_string_len}")
    
    first_half_len = int(available_string_len / 2)
    print(f"First half length: {first_half_len}")
    
    second_half_len = available_string_len - first_half_len
    print(f"Second half length: {second_half_len}")
    
    result_manual = text[:first_half_len] + '...' + text[-second_half_len:]
    print(f"Manual calculation: '{result_manual}'")
    print(f"Actual result: '{result}'")