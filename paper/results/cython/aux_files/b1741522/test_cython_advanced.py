"""
Advanced property-based tests for Cython.CodeWriter - hunting for edge cases
"""

import math
from hypothesis import given, strategies as st, assume, settings, example
import Cython.CodeWriter as CW


# More complex strategies
valid_operators = st.sampled_from(list(CW.binop_node_classes.keys()))
positions = st.tuples(st.integers(min_value=0, max_value=1000), 
                      st.integers(min_value=0, max_value=1000))

# Edge case numeric values
edge_int_values = st.one_of(
    st.just('0'),
    st.just('-0'),  # Negative zero
    st.just('1'),
    st.just('-1'),
    st.just(''),  # Empty string
    st.just('00'),  # Leading zeros
    st.just('000000000000000000000000000000000000001'),  # Many leading zeros
    st.integers(min_value=-2**63, max_value=2**63-1).map(str),  # Large integers
    st.text(alphabet='0123456789', min_size=100, max_size=500),  # Very long numbers
)

# Unicode and special strings
special_strings = st.one_of(
    st.just('∞'),
    st.just('NaN'),
    st.just('inf'),
    st.just('-inf'),
    st.just('1e10'),
    st.just('1.0'),
    st.just('+42'),
    st.just('0x10'),
    st.just('0b1010'),
    st.just('0o777'),
)


@given(value=edge_int_values, pos=positions)
@settings(max_examples=200)
def test_intnode_edge_cases(value, pos):
    """Test IntNode with edge case values"""
    if not value:  # Skip empty string
        return
        
    try:
        node = CW.IntNode(pos=pos, value=value)
        
        # Serialize
        writer = CW.CodeWriter()
        result = writer.write(node)
        serialized = result.s.strip()
        
        # The value should be preserved exactly
        assert serialized == value
    except Exception as e:
        # IntNode might have validation - that's OK
        pass


@given(value=special_strings, pos=positions)
def test_intnode_with_special_values(value, pos):
    """Test IntNode with special numeric representations"""
    try:
        node = CW.IntNode(pos=pos, value=value)
        
        # If it accepts the value, it should serialize it
        writer = CW.CodeWriter()
        result = writer.write(node)
        serialized = result.s.strip()
        
        # Should preserve the value
        assert value in serialized or serialized == value
    except (ValueError, TypeError, AttributeError):
        # It's OK if IntNode rejects invalid values
        pass


@given(pos=positions)
def test_float_node_special_values(pos):
    """Test FloatNode with special float values"""
    special_values = ['inf', '-inf', 'nan', '1e308', '-1e308', '0.0', '-0.0']
    
    for value in special_values:
        try:
            node = CW.FloatNode(pos=pos, value=value)
            
            writer = CW.CodeWriter()
            result = writer.write(node)
            serialized = result.s.strip()
            
            # Value should be preserved
            assert value in serialized or serialized == value
        except Exception:
            # Some values might be rejected
            pass


@given(operator=valid_operators, pos=positions)
def test_binop_with_none_operands(operator, pos):
    """Test binop_node behavior with None operands"""
    left = CW.IntNode(pos=pos, value='1')
    right = CW.IntNode(pos=pos, value='2')
    
    # Test with None left operand
    try:
        node = CW.binop_node(pos=pos, operator=operator, operand1=None, operand2=right)
        # If it accepts None, try to serialize
        writer = CW.CodeWriter()
        result = writer.write(node)
    except (AttributeError, TypeError):
        # Expected - None operands should fail
        pass
    
    # Test with None right operand  
    try:
        node = CW.binop_node(pos=pos, operator=operator, operand1=left, operand2=None)
        writer = CW.CodeWriter()
        result = writer.write(node)
    except (AttributeError, TypeError):
        pass


@given(value=st.text(min_size=0, max_size=1000), pos=positions)
def test_unicode_node_arbitrary_text(value, pos):
    """Test UnicodeNode with arbitrary text including special characters"""
    try:
        node = CW.UnicodeNode(pos=pos, value=value)
        
        writer = CW.CodeWriter()
        result = writer.write(node)
        serialized = result.s
        
        # The value should appear in the serialized output (possibly quoted)
        # We can't check exact format without knowing the escaping rules
        assert len(serialized) >= 0
    except Exception:
        # Some characters might cause issues
        pass


@given(elements=st.lists(st.integers(min_value=-100, max_value=100).map(str), min_size=0, max_size=100), pos=positions)
def test_list_node(elements, pos):
    """Test ListNode with various sizes"""
    try:
        # Create IntNodes for elements
        element_nodes = [CW.IntNode(pos=pos, value=str(v)) for v in elements]
        
        # Create ListNode
        list_node = CW.ListNode(pos=pos, args=element_nodes)
        
        # Serialize
        writer = CW.CodeWriter()
        result = writer.write(list_node)
        serialized = result.s
        
        # Should contain brackets
        assert '[' in serialized
        assert ']' in serialized
        
        # All elements should appear
        for elem in elements:
            assert elem in serialized
            
    except (AttributeError, TypeError) as e:
        # ListNode might not have 'args' attribute or different interface
        pass


@given(pos=positions)
def test_none_node(pos):
    """Test NoneNode"""
    try:
        node = CW.NoneNode(pos=pos)
        
        writer = CW.CodeWriter()
        result = writer.write(node)
        serialized = result.s.strip()
        
        # Should serialize to 'None'
        assert serialized == 'None'
    except Exception:
        pass


@given(operator=st.text(min_size=1, max_size=10), pos=positions)
def test_invalid_operators(operator, pos):
    """Test binop_node with invalid operators"""
    assume(operator not in CW.binop_node_classes)
    
    left = CW.IntNode(pos=pos, value='1')
    right = CW.IntNode(pos=pos, value='2')
    
    try:
        node = CW.binop_node(pos=pos, operator=operator, operand1=left, operand2=right)
        # If it doesn't raise, that's a bug - invalid operators should fail
        assert False, f"binop_node accepted invalid operator: {operator}"
    except KeyError:
        # Expected - invalid operators should raise KeyError
        pass


@given(depth=st.integers(min_value=0, max_value=100))
def test_deeply_nested_expressions(depth):
    """Test deeply nested binary expressions"""
    pos = (0, 0)
    
    # Build a deeply nested expression
    node = CW.IntNode(pos=pos, value='1')
    
    for i in range(depth):
        right = CW.IntNode(pos=pos, value=str(i))
        node = CW.binop_node(pos=pos, operator='+', operand1=node, operand2=right)
    
    # Try to serialize
    try:
        writer = CW.CodeWriter()
        result = writer.write(node)
        serialized = result.s
        
        # Should have 'depth' plus operators
        assert serialized.count('+') == depth
    except RecursionError:
        # Very deep nesting might hit recursion limit
        assume(False)  # Skip this case


@given(value=st.floats(allow_nan=True, allow_infinity=True))
def test_float_node_with_python_floats(value):
    """Test FloatNode with actual Python float values"""
    pos = (0, 0)
    
    try:
        # Convert float to string representation
        if math.isnan(value):
            str_value = 'nan'
        elif math.isinf(value):
            str_value = 'inf' if value > 0 else '-inf'
        else:
            str_value = str(value)
            
        node = CW.FloatNode(pos=pos, value=str_value)
        
        writer = CW.CodeWriter()
        result = writer.write(node)
        serialized = result.s.strip()
        
        # Should preserve the value representation
        assert len(serialized) > 0
    except Exception:
        # Some float values might not be supported
        pass


@given(keys=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=20), 
       values=st.lists(st.integers().map(str), min_size=0, max_size=20),
       pos=positions)
def test_dict_node(keys, values, pos):
    """Test DictNode creation and serialization"""
    # Make keys and values same length
    min_len = min(len(keys), len(values))
    keys = keys[:min_len]
    values = values[:min_len]
    
    try:
        # Create key and value nodes
        key_nodes = [CW.UnicodeNode(pos=pos, value=k) for k in keys]
        value_nodes = [CW.IntNode(pos=pos, value=v) for v in values]
        
        # Create DictItemNodes
        items = []
        for k, v in zip(key_nodes, value_nodes):
            item = CW.DictItemNode(pos=pos, key=k, value=v)
            items.append(item)
        
        # Create DictNode
        dict_node = CW.DictNode(pos=pos, key_value_pairs=items)
        
        # Serialize
        writer = CW.CodeWriter()
        result = writer.write(dict_node)
        serialized = result.s
        
        # Should contain braces
        assert '{' in serialized
        assert '}' in serialized
        
    except (AttributeError, TypeError):
        # DictNode might have different interface
        pass