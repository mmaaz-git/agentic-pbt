from aiogram.utils import markdown

# Minimal reproduction of the double-escaping bug
text = "["
print(f"Original text: '{text}'")

# Apply bold formatting
bold_text = markdown.bold(text)
print(f"After bold(): '{bold_text}'")

# Apply italic formatting to the already bold text
italic_bold_text = markdown.italic(bold_text)
print(f"After italic(bold()): '{italic_bold_text}'")

print("\nExpected: '_*\\[*_' (italic wrapper around bold markdown)")
print(f"Actual:   '{italic_bold_text}'")
print("\nThe issue: The backslash from bold() gets escaped again by italic(),")
print("resulting in '\\\\[' instead of '\\[', which produces invalid markdown.")