import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.custom_descriptions as custom_descriptions
import fire.formatting as formatting

# Investigate why space=5 also loses content for GetStringTypeSummary
text = "hello world"
available_space = 5
line_length = 80

print(f"Investigating GetStringTypeSummary('{text}', {available_space}, {line_length})")
print("-" * 50)

# Step through GetStringTypeSummary logic
TWO_DOUBLE_QUOTES = '""'
print(f"len(text) = {len(text)}")
print(f"len(TWO_DOUBLE_QUOTES) = {len(TWO_DOUBLE_QUOTES)}")
print(f"len(text) + len(TWO_DOUBLE_QUOTES) = {len(text) + len(TWO_DOUBLE_QUOTES)}")
print(f"available_space = {available_space}")

if len(text) + len(TWO_DOUBLE_QUOTES) <= available_space:
    print("Branch: Text fits with quotes")
    content = text
else:
    print("Branch: Text doesn't fit, need to truncate")
    additional_len_needed = len(TWO_DOUBLE_QUOTES) + len(formatting.ELLIPSIS)
    print(f"additional_len_needed = {additional_len_needed}")
    
    if available_space < additional_len_needed:
        print(f"available_space ({available_space}) < additional_len_needed ({additional_len_needed})")
        print(f"Setting available_space to line_length: {line_length}")
        available_space = line_length
    
    # This is the truncation call
    truncate_space = available_space - len(TWO_DOUBLE_QUOTES)
    print(f"Calling EllipsisTruncate('{text}', {truncate_space}, {line_length})")
    content = formatting.EllipsisTruncate(text, truncate_space, line_length)
    print(f"Truncated content: '{content}'")

result = formatting.DoubleQuote(content)
print(f"Final result: {result}")

print("\n" + "=" * 50 + "\n")

# The bug occurs when available_space=5
print("Why available_space=5 causes the bug:")
print("-" * 40)
print("1. Text 'hello world' (11 chars) + quotes (2 chars) = 13 > 5, so needs truncation")
print("2. additional_len_needed = len('\"\"') + len('...') = 2 + 3 = 5")
print("3. available_space (5) is NOT less than additional_len_needed (5), so no fallback to line_length")
print("4. Calls EllipsisTruncate(text, 5-2, 80) = EllipsisTruncate(text, 3, 80)")
print("5. EllipsisTruncate with available_space=3 has the bug: returns just '...'")
print("6. Final result: '\"...\"' - all content lost!")

print("\nThis is a cascading bug: GetStringTypeSummary passes available_space=3 to EllipsisTruncate")