from hypothesis import given, strategies as st
import lxml.objectify as obj
from lxml import etree


@given(st.just(''))
def test_empty_value_type_inconsistency(value):
    """Empty string elements have inconsistent type conversion behavior"""
    xml_str = f'<root><value>{value}</value></root>'
    parsed = obj.fromstring(xml_str)
    
    # Empty string is correctly parsed as StringElement
    assert str(parsed.value) == ''
    assert type(parsed.value).__name__ == 'StringElement'
    
    # But when annotated with type information
    obj.annotate(parsed, empty_pytype='NoneElement')
    serialized = etree.tostring(parsed, encoding='unicode')
    reparsed = obj.fromstring(serialized)
    
    # The type changes after round-trip with annotation
    print(f"Original type: {type(parsed.value).__name__}")
    print(f"After annotation: {type(reparsed.value).__name__}")
    print(f"Value comparison: {repr(str(parsed.value))} vs {repr(str(reparsed.value))}")
    
    # This reveals inconsistent behavior
    assert type(reparsed.value).__name__ != type(parsed.value).__name__


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])