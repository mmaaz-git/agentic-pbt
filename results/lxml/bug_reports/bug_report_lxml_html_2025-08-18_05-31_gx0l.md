# Bug Report: lxml.html Malformed Comment Generation from Processing Instruction Syntax

**Target**: `lxml.html.fromstring`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The lxml HTML parser incorrectly converts incomplete processing instruction syntax (`<?`) into malformed HTML comments that include closing tags, breaking the HTML structure.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import lxml.html as html

@given(
    content=st.text(alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E), min_size=0, max_size=100)
)
def test_html_text_node_handling(content):
    html_str = f"<div>{content}</div>"
    
    try:
        parsed = html.fromstring(html_str)
        if parsed.text is None:
            assert content == ""
        else:
            assert parsed.text == content
    except etree.ParserError:
        pass
```

**Failing input**: `content='<?'`

## Reproducing the Bug

```python
import lxml.html as html

html_input = '<div><?</div>'
parsed = html.fromstring(html_input)
output = html.tostring(parsed, encoding='unicode')

print(f"Input:  {html_input}")
print(f"Output: {output}")

assert output == '<div><!--?</div--></div>'
```

## Why This Is A Bug

When the HTML parser encounters `<?` without a closing `?>`, it converts it to a comment but incorrectly includes the closing tag within the comment syntax, producing `<!--?</div-->` instead of properly closing the comment before the closing tag. This creates malformed HTML that violates comment syntax rules (comments should end with `-->`, not `</div-->`).

The correct behavior would be to either:
1. Treat `<?` as text content
2. Create a properly formed comment: `<!--?--></div>`
3. Handle it as an incomplete processing instruction

## Fix

The HTML parser's processing instruction handling logic needs to be corrected to ensure comments are properly closed before any closing tags. Here's a high-level approach:

```diff
# In the HTML parser's PI handling code (pseudo-code):
- comment_text = collect_until_end_of_element()
- create_comment(f"<!--?{comment_text}-->")
+ comment_text = collect_until_pi_end_or_tag_boundary()
+ create_comment(f"<!--?{comment_text}-->")
+ continue_parsing_from_tag_boundary()
```

The parser should recognize tag boundaries and close the comment before them, not include them within the comment.