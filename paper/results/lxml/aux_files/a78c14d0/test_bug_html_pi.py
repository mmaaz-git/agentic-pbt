import lxml.html as html
import lxml.etree as etree

def test_html_processing_instruction_bug():
    """Test that HTML parser incorrectly handles '<?' as comment and produces malformed output"""
    
    # Simple case: just <?
    html_input = '<div><?</div>'
    parsed = html.fromstring(html_input)
    output = html.tostring(parsed, encoding='unicode')
    
    print(f"Input:  {html_input!r}")
    print(f"Output: {output!r}")
    
    # The output contains a malformed comment
    assert '<!--?</div-->' in output, "Expected malformed comment in output"
    
    # More complex case with text
    html_input2 = '<div>text <? more text</div>'
    parsed2 = html.fromstring(html_input2)
    output2 = html.tostring(parsed2, encoding='unicode')
    
    print(f"\nInput:  {html_input2!r}")
    print(f"Output: {output2!r}")
    
    # Check that it creates malformed comment
    assert '<!--? more text</div-->' in output2
    
    # Verify the comment is actually malformed (ends with </div--> instead of -->)
    # This is clearly incorrect HTML
    print("\nThe bug: '<?' is converted to a comment that includes the closing tag!")
    print("Expected: '<!--?--></div>' or similar")
    print("Actual:   '<!--?</div-->'")
    
    return True

if __name__ == "__main__":
    test_html_processing_instruction_bug()