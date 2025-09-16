"""Test the boundary of control character handling in lxml.html"""

import lxml.html


def test_all_control_chars():
    """Test all control characters from 0x00 to 0x1F and 0x7F"""
    results = []
    
    # Test with fromstring
    for i in range(0x20):  # 0x00 to 0x1F
        char = chr(i)
        try:
            result = lxml.html.fromstring(char)
            results.append((i, char, 'fromstring', 'success', result.tag))
        except Exception as e:
            results.append((i, char, 'fromstring', 'error', str(e)[:50]))
    
    # Test 0x7F (DEL)
    char = chr(0x7F)
    try:
        result = lxml.html.fromstring(char)
        results.append((0x7F, char, 'fromstring', 'success', result.tag))
    except Exception as e:
        results.append((0x7F, char, 'fromstring', 'error', str(e)[:50]))
    
    # Test with fragment_fromstring(create_parent=True)
    for i in range(0x20):
        char = chr(i)
        try:
            result = lxml.html.fragment_fromstring(char, create_parent=True)
            text = result.text if result.text else '(empty)'
            results.append((i, char, 'fragment_create', 'success', text))
        except Exception as e:
            results.append((i, char, 'fragment_create', 'error', str(e)[:50]))
    
    return results


def test_roundtrip_preservation():
    """Test which characters are preserved in roundtrips"""
    preserved = []
    changed = []
    
    for i in range(0x20):
        if i == 0x09 or i == 0x0A or i == 0x0D:  # tab, newline, carriage return
            char = chr(i)
            html = f'<div>a{char}b</div>'
            try:
                parsed = lxml.html.fromstring(html)
                result = lxml.html.tostring(parsed, encoding='unicode')
                if f'a{char}b' in result:
                    preserved.append((i, f'0x{i:02X}', repr(char)))
                else:
                    # Check what it changed to
                    if parsed.text:
                        changed.append((i, f'0x{i:02X}', repr(char), repr(parsed.text)))
            except:
                pass
    
    return preserved, changed


if __name__ == "__main__":
    print("=== Control Character Handling Boundary ===\n")
    
    results = test_all_control_chars()
    
    print("Characters that parse successfully with fromstring:")
    for i, char, method, status, info in results:
        if method == 'fromstring' and status == 'success':
            print(f"  0x{i:02X} ({repr(char)}): creates <{info}> element")
    
    print("\nCharacters that fail with fromstring:")
    for i, char, method, status, info in results:
        if method == 'fromstring' and status == 'error':
            print(f"  0x{i:02X} ({repr(char)}): {info}")
    
    print("\nCharacters that fail with fragment_fromstring(create_parent=True):")
    for i, char, method, status, info in results:
        if method == 'fragment_create' and status == 'error':
            print(f"  0x{i:02X} ({repr(char)}): {info}")
    
    print("\n=== Roundtrip Preservation ===\n")
    preserved, changed = test_roundtrip_preservation()
    
    if preserved:
        print("Characters preserved in roundtrip:")
        for i, hex_val, char in preserved:
            print(f"  {hex_val} ({char})")
    
    if changed:
        print("\nCharacters changed in roundtrip:")
        for i, hex_val, char, new_text in changed:
            print(f"  {hex_val} ({char}) -> {new_text}")