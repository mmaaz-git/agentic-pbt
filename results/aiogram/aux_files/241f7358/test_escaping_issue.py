from aiogram.utils import markdown

# Test potential issues with escaping

print("=== Testing Potential Double-Escaping Issues ===\n")

# Test 1: What happens if we nest markdown functions?
text = "Hello[World]"
bold_text = markdown.bold(text)
print(f"Step 1 - bold('{text}') = '{bold_text}'")

# What if we try to make it italic too?
italic_bold = markdown.italic(bold_text)
print(f"Step 2 - italic(bold_text) = '{italic_bold}'")
print(f"  Notice: The asterisks from bold got escaped!")

# Test 2: What if the user already has escaped characters?
already_escaped = r"Hello\[World\]"
result = markdown.bold(already_escaped)
print(f"\nPre-escaped input: bold('{already_escaped}') = '{result}'")
print(f"  Notice: Double escaping occurred!")

# Test 3: Round-trip issue
text = "test."
markdown_text = markdown.code(text)
print(f"\nOriginal: '{text}'")
print(f"After code(): '{markdown_text}'")
# If we try to extract the content back:
# We'd expect to get 'test.' but we get 'test\.'

# Test 4: Real-world example - code blocks with regex
regex_pattern = r"\d+\.\d+"
code_block = markdown.code(regex_pattern)
print(f"\nRegex pattern: '{regex_pattern}'")
print(f"In code block: '{code_block}'")
print("  The regex pattern is now altered with extra backslashes!")

# Test 5: URL encoding in links
url = "https://example.com/path?key=value&other=test"
link = markdown.link("Click here", url)
print(f"\nURL: '{url}'")
print(f"Link: '{link}'")

# Test 6: Multiple special characters
complex_text = "Price: $9.99 (was $14.99) - Save 33%!"
bold_complex = markdown.bold(complex_text)
print(f"\nComplex text: '{complex_text}'")
print(f"Bold version: '{bold_complex}'")

print("\n=== Analysis ===")
print("The escaping behavior appears to be overly aggressive.")
print("It escapes characters that don't always need escaping in their contexts.")
print("For example, '.' doesn't need escaping inside backticks in standard Markdown.")
print("This could lead to issues when the markdown is rendered or processed.")