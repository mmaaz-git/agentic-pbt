"""Test which control characters cause fragment_fromstring to fail"""

import lxml.html


def test_fragment_control_chars():
    """Test all control characters with fragment_fromstring"""
    
    failures = []
    successes = []
    
    for i in range(0x20):
        if i == 0x09 or i == 0x0A or i == 0x0D:  # tab, newline, CR
            continue  # Skip whitespace chars
        
        char = chr(i)
        try:
            # Test without create_parent
            result = lxml.html.fragment_fromstring(char)
            successes.append((i, 'no_parent', result.text))
        except Exception as e:
            failures.append((i, 'no_parent', str(e)[:60]))
        
        try:
            # Test with create_parent
            result = lxml.html.fragment_fromstring(char, create_parent=True)
            successes.append((i, 'with_parent', result.text))
        except Exception as e:
            failures.append((i, 'with_parent', str(e)[:60]))
    
    return successes, failures


def test_fragment_with_embedded_control():
    """Test control characters embedded in HTML"""
    results = []
    
    for i in [0x00, 0x01, 0x1B, 0x7F]:
        char = chr(i)
        html = f'<div>text{char}here</div>'
        
        try:
            result = lxml.html.fragment_fromstring(html)
            text = result.text if result.text else '(None)'
            results.append((i, 'success', text))
        except Exception as e:
            results.append((i, 'error', str(e)[:60]))
    
    return results


if __name__ == "__main__":
    print("=== fragment_fromstring Control Character Tests ===\n")
    
    successes, failures = test_fragment_control_chars()
    
    print("Control characters that succeed:")
    for code, mode, text in successes:
        print(f"  0x{code:02X} ({mode}): text={text!r}")
    
    print("\nControl characters that fail:")
    for code, mode, error in failures:
        print(f"  0x{code:02X} ({mode}): {error}")
    
    print("\n=== Embedded Control Characters in HTML ===\n")
    
    results = test_fragment_with_embedded_control()
    for code, status, info in results:
        if status == 'success':
            print(f"  0x{code:02X}: Success - text={info!r}")
        else:
            print(f"  0x{code:02X}: Error - {info}")