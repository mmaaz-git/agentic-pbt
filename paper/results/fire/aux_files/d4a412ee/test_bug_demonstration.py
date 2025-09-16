import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.formatting as formatting
import fire.custom_descriptions as custom_descriptions

print("=== Bug Demonstration: EllipsisTruncate with available_space=3 ===\n")

# Direct test of EllipsisTruncate
print("Direct EllipsisTruncate tests:")
print("-" * 40)

test_cases = [
    ("hello", 3, 80),
    ("test", 3, 80),
    ("abc", 3, 80),
    ("ab", 3, 80),
]

for text, space, line_len in test_cases:
    result = formatting.EllipsisTruncate(text, space, line_len)
    print(f"EllipsisTruncate('{text}', {space}, {line_len}) = '{result}'")
    if len(text) > space and result == "...":
        print(f"  ⚠️  BUG: Lost all content! Original was '{text}', got just '...'")

print("\n" + "=" * 50 + "\n")

# How this affects GetStringTypeSummary
print("Impact on GetStringTypeSummary:")
print("-" * 40)

# When available_space is very small, GetStringTypeSummary can produce meaningless output
test_strings = ["hello world", "important data", "user input"]

for text in test_strings:
    for available_space in [3, 4, 5]:
        summary = custom_descriptions.GetStringTypeSummary(text, available_space, 80)
        print(f"GetStringTypeSummary('{text}', space={available_space}) = {summary}")
        
        # Check if we lost all content
        content = summary[1:-1]  # Remove quotes
        if content == "..." and len(text) > 0:
            print(f"  ⚠️  BUG: Lost all string content!")

print("\n" + "=" * 50 + "\n")

# The issue: when available_space=3, text[:available_space-3] = text[:0] = ""
print("Root cause analysis:")
print("-" * 40)
print("In EllipsisTruncate, when available_space=3:")
print("  - The check 'if available_space < len(ELLIPSIS)' is False (3 < 3 is False)")
print("  - So it doesn't fall back to line_length")
print("  - When truncating: text[:available_space - len(ELLIPSIS)] = text[:3-3] = text[:0] = ''")
print("  - Result: '' + '...' = '...'")
print("\nThis means ALL content is lost when available_space equals 3!")

print("\n" + "=" * 50 + "\n")

# Minimal reproduction
print("Minimal reproduction:")
print("-" * 40)
print("```python")
print("import fire.formatting as formatting")
print("")
print("# Bug: loses all content when available_space=3")
print("result = formatting.EllipsisTruncate('hello', 3, 80)")
print("assert result == '...'  # Expected something like 'h...' or fallback to line_length")
print("```")