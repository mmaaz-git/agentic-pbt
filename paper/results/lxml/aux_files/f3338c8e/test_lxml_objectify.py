import math
from hypothesis import given, strategies as st, settings, assume
import lxml.objectify as obj
from lxml import etree
import pytest


@given(st.text(min_size=1, max_size=100).filter(lambda s: not s.isspace()))
def test_string_element_round_trip(text):
    """Test that string values survive XML round-trip"""
    xml_str = f'<root><value>{text}</value></root>'
    try:
        parsed = obj.fromstring(xml_str)
        if hasattr(parsed, 'value'):
            serialized = etree.tostring(parsed, encoding='unicode')
            reparsed = obj.fromstring(serialized)
            
            if str(parsed.value) == text:
                assert str(reparsed.value) == str(parsed.value)
    except etree.XMLSyntaxError:
        pass


@given(st.integers())
def test_integer_element_round_trip(num):
    """Test that integer values survive XML round-trip"""
    xml_str = f'<root><value>{num}</value></root>'
    parsed = obj.fromstring(xml_str)
    
    serialized = etree.tostring(parsed, encoding='unicode')
    reparsed = obj.fromstring(serialized)
    
    assert int(parsed.value) == num
    assert int(reparsed.value) == int(parsed.value)


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_float_element_round_trip(num):
    """Test that float values survive XML round-trip"""
    if math.isnan(num):
        str_num = 'NaN'
    elif math.isinf(num):
        str_num = 'inf' if num > 0 else '-inf'
    else:
        str_num = str(num)
    
    xml_str = f'<root><value>{str_num}</value></root>'
    parsed = obj.fromstring(xml_str)
    
    serialized = etree.tostring(parsed, encoding='unicode')
    reparsed = obj.fromstring(serialized)
    
    if math.isnan(num):
        assert math.isnan(float(parsed.value))
        assert math.isnan(float(reparsed.value))
    else:
        assert float(parsed.value) == float(reparsed.value)


@given(st.booleans())
def test_bool_element_round_trip(value):
    """Test that boolean values survive XML round-trip"""
    str_val = 'true' if value else 'false'
    xml_str = f'<root><value>{str_val}</value></root>'
    
    parsed = obj.fromstring(xml_str)
    serialized = etree.tostring(parsed, encoding='unicode')
    reparsed = obj.fromstring(serialized)
    
    assert bool(parsed.value) == value
    assert bool(reparsed.value) == bool(parsed.value)


@given(st.builds(
    lambda tag, value: (tag, value),
    st.text(min_size=1, max_size=50).filter(lambda s: s.isidentifier()),
    st.text(min_size=0, max_size=100)
))
def test_annotate_deannotate_round_trip(tag_value):
    """Test that annotate/deannotate is reversible"""
    tag, value = tag_value
    xml_str = f'<root><{tag}>{value}</{tag}></root>'
    
    try:
        original = obj.fromstring(xml_str)
        original_str = etree.tostring(original, encoding='unicode')
        
        obj.annotate(original)
        annotated_str = etree.tostring(original, encoding='unicode')
        
        obj.deannotate(original)
        deannotated_str = etree.tostring(original, encoding='unicode')
        
        reparsed = obj.fromstring(deannotated_str)
        if hasattr(original, tag) and hasattr(reparsed, tag):
            orig_val = getattr(obj.fromstring(original_str), tag)
            final_val = getattr(reparsed, tag)
            assert str(orig_val) == str(final_val)
    except (etree.XMLSyntaxError, AttributeError):
        pass


@given(st.text(min_size=0, max_size=50))
def test_empty_value_handling(value):
    """Test handling of empty and whitespace values"""
    xml_str = f'<root><value>{value}</value></root>'
    
    try:
        parsed = obj.fromstring(xml_str)
        
        if value == '':
            assert str(parsed.value) == ''
            assert type(parsed.value).__name__ == 'StringElement'
        
        serialized = etree.tostring(parsed, encoding='unicode')
        reparsed = obj.fromstring(serialized)
        
        assert str(parsed.value) == str(reparsed.value)
    except etree.XMLSyntaxError:
        pass


@given(st.lists(st.integers(), min_size=1, max_size=10))
def test_multiple_elements_preserve_values(values):
    """Test that multiple elements preserve their values and types"""
    xml_parts = ['<root>']
    for i, val in enumerate(values):
        xml_parts.append(f'<item{i}>{val}</item{i}>')
    xml_parts.append('</root>')
    xml_str = ''.join(xml_parts)
    
    parsed = obj.fromstring(xml_str)
    
    for i, val in enumerate(values):
        item = getattr(parsed, f'item{i}')
        assert int(item) == val
    
    serialized = etree.tostring(parsed, encoding='unicode')
    reparsed = obj.fromstring(serialized)
    
    for i, val in enumerate(values):
        item = getattr(reparsed, f'item{i}')
        assert int(item) == val


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_float_precision_preservation(num):
    """Test that float precision is preserved through round-trip"""
    xml_str = f'<root><value>{num}</value></root>'
    parsed = obj.fromstring(xml_str)
    
    if '.' in str(num) or 'e' in str(num).lower():
        assert type(parsed.value).__name__ == 'FloatElement'
        serialized = etree.tostring(parsed, encoding='unicode')
        reparsed = obj.fromstring(serialized)
        
        assert math.isclose(float(parsed.value), num, rel_tol=1e-9)
        assert float(parsed.value) == float(reparsed.value)


@given(st.text(min_size=1, max_size=20).filter(lambda s: s.isidentifier()))
def test_element_maker_consistency(tag_name):
    """Test that ElementMaker creates consistent elements"""
    E = obj.E
    
    elem1 = E(tag_name, "test")
    elem2 = E(tag_name, "test")
    
    assert elem1.tag == elem2.tag == tag_name
    assert str(elem1) == str(elem2) == "test"
    
    xml1 = etree.tostring(elem1, encoding='unicode')
    xml2 = etree.tostring(elem2, encoding='unicode')
    assert xml1 == xml2


@given(st.text(min_size=0, max_size=100))
def test_pytypename_consistency(value):
    """Test pytypename returns consistent type names"""
    xml_str = f'<root><value>{value}</value></root>'
    try:
        parsed = obj.fromstring(xml_str)
        typename1 = obj.pytypename(parsed.value)
        typename2 = obj.pytypename(parsed.value)
        
        assert typename1 == typename2
        assert isinstance(typename1, str)
    except (etree.XMLSyntaxError, AttributeError):
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])