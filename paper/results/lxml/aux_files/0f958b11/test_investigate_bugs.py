"""Investigate the discovered issues in lxml.html"""

import lxml.html


# Test 1: Carriage return is converted to newline
def test_carriage_return_conversion():
    text = '0\r'
    wrapped = f'<div>{text}</div>'
    parsed = lxml.html.fromstring(wrapped)
    result = lxml.html.tostring(parsed, encoding='unicode', method='html')
    print(f"Input text: {text!r}")
    print(f"Result: {result!r}")
    print(f"Text changed: {text!r} -> {parsed.text!r}")
    return parsed.text != text


# Test 2: NULL byte handling
def test_null_byte_handling():
    text = '\x00'
    try:
        result = lxml.html.fragment_fromstring(text, create_parent=True)
        print(f"NULL byte result text: {result.text!r}")
        serialized = lxml.html.tostring(result, encoding='unicode')
        print(f"NULL byte serialized: {serialized!r}")
        return result.text != text
    except Exception as e:
        print(f"NULL byte error: {e}")
        return False


# Test 3: Control character handling
def test_control_char_handling():
    text = '\x1b'  # ESC character
    try:
        result = lxml.html.fragment_fromstring(text, create_parent=True)
        print(f"Control char succeeded: {result}")
        return False
    except ValueError as e:
        print(f"Control char error (expected): {e}")
        return True


# Test 4: Unit separator character
def test_unit_separator():
    text = '\x1f'  # Unit separator
    try:
        result = lxml.html.document_fromstring(text)
        print(f"Unit separator result: {result}")
        print(f"Result tag: {result.tag}")
        print(f"Result text: {result.text!r}")
        serialized = lxml.html.tostring(result, encoding='unicode')
        print(f"Serialized: {serialized!r}")
        return True  # It doesn't raise an error!
    except Exception as e:
        print(f"Unit separator error: {e}")
        return False


# Test 5: DEL character
def test_del_character():
    text = '\x7f'  # DEL character
    try:
        result = lxml.html.fromstring(text)
        print(f"DEL character result: {result}")
        print(f"Result tag: {result.tag}")
        print(f"Result text: {result.text!r}")
        return True  # It doesn't raise an error!
    except Exception as e:
        print(f"DEL character error: {e}")
        return False


if __name__ == "__main__":
    print("=== Issue 1: Carriage return conversion ===")
    issue1 = test_carriage_return_conversion()
    print(f"Issue found: {issue1}\n")
    
    print("=== Issue 2: NULL byte handling ===")
    issue2 = test_null_byte_handling()
    print(f"Issue found: {issue2}\n")
    
    print("=== Issue 3: Control character handling ===")
    issue3 = test_control_char_handling()
    print(f"Correctly errors: {issue3}\n")
    
    print("=== Issue 4: Unit separator handling ===")
    issue4 = test_unit_separator()
    print(f"Issue found: {issue4}\n")
    
    print("=== Issue 5: DEL character handling ===")
    issue5 = test_del_character()
    print(f"Issue found: {issue5}")