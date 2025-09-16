from aiogram.utils import markdown

# Test cases from the failures
test_cases = [
    ("0{", "bold"),
    ("0.", "code"),
    ("0.", "link_title"),
    ("0=", "bold"),
    ("0<", "hbold"),
    ("[[", "bold"),
    ("0.", "pre"),
]

print("=== Investigating Markdown Escaping Behavior ===\n")

# Test 1: Bold with special chars
text = "0{"
result = markdown.bold(text)
print(f"markdown.bold('{text}') = '{result}'")
print(f"  Expected '{text}' to be in result, but got escaped version")

# Test 2: Code with special chars
text = "0."
result = markdown.code(text)
print(f"\nmarkdown.code('{text}') = '{result}'")
print(f"  Expected '{text}' to be in result, but got escaped version")

# Test 3: Link with special chars
title = "0."
url = "https://example.com"
result = markdown.link(title, url)
print(f"\nmarkdown.link('{title}', '{url}') = '{result}'")
print(f"  Expected '{title}' to be in result, but got escaped version")

# Test 4: HTML bold with special chars
text = "0<"
result = markdown.hbold(text)
print(f"\nmarkdown.hbold('{text}') = '{result}'")
print(f"  Expected '{text}' to be in result, but got HTML entity encoding")

# Test 5: Pre with special chars
text = "0."
result = markdown.pre(text)
print(f"\nmarkdown.pre('{text}') = '{result}'")
print(f"  Expected '{text}' to be in result, but got escaped version")

# Test more edge cases
print("\n=== Additional Tests ===\n")

# Characters that need escaping in Markdown
special_chars = ['*', '_', '`', '[', ']', '(', ')', '\\', '.', '{', '}', '=', '<', '>', '&']
for char in special_chars:
    text = f"test{char}test"
    bold_result = markdown.bold(text)
    code_result = markdown.code(text)
    hbold_result = markdown.hbold(text)
    
    if text not in bold_result:
        print(f"Bold escapes '{char}': input='{text}', output='{bold_result}'")
    if text not in code_result:
        print(f"Code escapes '{char}': input='{text}', output='{code_result}'")
    if text not in hbold_result:
        print(f"HTML bold escapes '{char}': input='{text}', output='{hbold_result}'")

print("\n=== Checking if this is documented behavior ===")
print("Bold docstring:", markdown.bold.__doc__)
print("Code docstring:", markdown.code.__doc__)
print("HBold docstring:", markdown.hbold.__doc__)