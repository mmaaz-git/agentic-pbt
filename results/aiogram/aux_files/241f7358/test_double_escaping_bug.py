from hypothesis import given, strategies as st, settings
from aiogram.utils import markdown

# Property-based test that discovers the double-escaping bug
@given(st.text(alphabet='[]()*._{}`', min_size=1, max_size=10))
@settings(max_examples=100)
def test_nested_markdown_double_escaping(text):
    """Test that nesting markdown functions doesn't cause double-escaping."""
    # Apply bold formatting
    bold_text = markdown.bold(text)
    
    # Apply italic formatting to the bold text
    italic_bold_text = markdown.italic(bold_text)
    
    # The original text should still be recoverable somehow
    # In proper markdown, *_text_* should work, but due to double-escaping,
    # we get something like _\*escaped\\text\*_ which is wrong
    
    # Check if there's double-escaping (backslash before backslash)
    if '\\\\' in italic_bold_text:
        print(f"\nDouble-escaping detected!")
        print(f"Original: {text}")
        print(f"After bold: {bold_text}")
        print(f"After italic(bold): {italic_bold_text}")
        assert False, f"Double-escaping occurred: {italic_bold_text}"

if __name__ == "__main__":
    test_nested_markdown_double_escaping()