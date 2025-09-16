"""
Property-based tests for Cython.CodeWriter module
"""

import math
from hypothesis import given, strategies as st, assume, settings
import Cython.CodeWriter as CW


# Strategy for valid operators
valid_operators = st.sampled_from(list(CW.binop_node_classes.keys()))

# Strategy for valid integer values as strings
int_values = st.integers(min_value=-10000, max_value=10000).map(str)

# Strategy for simple positions
positions = st.tuples(st.integers(min_value=0, max_value=1000), 
                      st.integers(min_value=0, max_value=1000))


@given(operator=valid_operators, pos=positions)
def test_binop_node_returns_correct_type(operator, pos):
    """Test that binop_node returns the correct node type for each operator"""
    # Create simple integer operands
    left = CW.IntNode(pos=pos, value='1')
    right = CW.IntNode(pos=pos, value='2')
    
    # Create binop node
    node = CW.binop_node(pos=pos, operator=operator, operand1=left, operand2=right)
    
    # Check that the returned node is of the expected type
    expected_type = CW.binop_node_classes[operator]
    assert isinstance(node, expected_type), f"Expected {expected_type.__name__}, got {type(node).__name__}"
    
    # Check that the operator is preserved
    assert node.operator == operator
    
    # Check that operands are preserved
    assert node.operand1 is left
    assert node.operand2 is right


@given(operator=valid_operators, left_val=int_values, right_val=int_values, pos=positions)
def test_binop_serialization_preserves_operator(operator, left_val, right_val, pos):
    """Test that serializing a binop node preserves the operator in the output"""
    # Create integer operands
    left = CW.IntNode(pos=pos, value=left_val)
    right = CW.IntNode(pos=pos, value=right_val)
    
    # Create binop node
    node = CW.binop_node(pos=pos, operator=operator, operand1=left, operand2=right)
    
    # Serialize it
    writer = CW.CodeWriter()
    result = writer.write(node)
    
    # Check that the serialized string contains the operator
    serialized = result.s
    assert operator in serialized, f"Operator '{operator}' not found in serialized output: {serialized}"
    
    # Check that operand values are in the output
    assert left_val in serialized, f"Left operand '{left_val}' not in output: {serialized}"
    assert right_val in serialized, f"Right operand '{right_val}' not in output: {serialized}"


@given(operator=valid_operators, pos=positions)
def test_binop_with_inplace_flag(operator, pos):
    """Test that binop_node handles the inplace flag correctly"""
    left = CW.IntNode(pos=pos, value='10')
    right = CW.IntNode(pos=pos, value='20')
    
    # Create both regular and inplace versions
    regular_node = CW.binop_node(pos=pos, operator=operator, operand1=left, operand2=right, inplace=False)
    inplace_node = CW.binop_node(pos=pos, operator=operator, operand1=left, operand2=right, inplace=True)
    
    # Both should be of the same type
    assert type(regular_node) == type(inplace_node)
    
    # The inplace flag should be preserved
    assert regular_node.inplace == False
    assert inplace_node.inplace == True


@given(value=int_values, pos=positions)
def test_intnode_preserves_value(value, pos):
    """Test that IntNode preserves its value correctly"""
    node = CW.IntNode(pos=pos, value=value)
    
    # Value should be preserved
    assert node.value == value
    
    # Serialization should preserve the value
    writer = CW.CodeWriter()
    result = writer.write(node)
    serialized = result.s
    
    # The serialized form should be the value itself
    assert serialized.strip() == value


@given(left_val=int_values, right_val=int_values, pos=positions)
def test_nested_binop_serialization(left_val, right_val, pos):
    """Test serialization of nested binary operations"""
    # Create a nested expression: (a + b) * c
    a = CW.IntNode(pos=pos, value=left_val)
    b = CW.IntNode(pos=pos, value=right_val)
    c = CW.IntNode(pos=pos, value='3')
    
    # Create nested binop
    add_node = CW.binop_node(pos=pos, operator='+', operand1=a, operand2=b)
    mul_node = CW.binop_node(pos=pos, operator='*', operand1=add_node, operand2=c)
    
    # Serialize
    writer = CW.CodeWriter()
    result = writer.write(mul_node)
    serialized = result.s
    
    # Check that both operators appear
    assert '+' in serialized
    assert '*' in serialized
    
    # Check that all values appear
    assert left_val in serialized
    assert right_val in serialized
    assert '3' in serialized


@given(operators=st.lists(valid_operators, min_size=2, max_size=5))
def test_all_operators_handled(operators):
    """Test that all operators can be used without errors"""
    pos = (0, 0)
    
    for op in operators:
        left = CW.IntNode(pos=pos, value='1')
        right = CW.IntNode(pos=pos, value='2')
        
        # Should not raise an exception
        node = CW.binop_node(pos=pos, operator=op, operand1=left, operand2=right)
        
        # Should be serializable
        writer = CW.CodeWriter()
        result = writer.write(node)
        serialized = result.s
        
        # Basic sanity check
        assert len(serialized) > 0


@given(value=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() and x.isdigit()), pos=positions)
def test_intnode_with_large_numbers(value, pos):
    """Test IntNode with various numeric strings"""
    assume(value.isdigit())  # Only test valid integer strings
    
    node = CW.IntNode(pos=pos, value=value)
    
    # Serialize
    writer = CW.CodeWriter()
    result = writer.write(node)
    serialized = result.s.strip()
    
    # The serialized form should be the same as the input
    assert serialized == value


@given(pos=positions)
def test_codewriter_visitor_pattern(pos):
    """Test that CodeWriter correctly implements the visitor pattern"""
    # Create various node types
    int_node = CW.IntNode(pos=pos, value='42')
    float_node = CW.FloatNode(pos=pos, value='3.14')
    
    writer = CW.CodeWriter()
    
    # Visit should work for different node types
    int_result = writer.write(int_node)
    assert int_result.s.strip() == '42'
    
    # Create new writer for float (to avoid state issues)
    writer2 = CW.CodeWriter()
    float_result = writer2.write(float_node)
    assert '3.14' in float_result.s


@given(operator=valid_operators)
def test_binop_node_classes_mapping_consistency(operator):
    """Test that binop_node_classes mapping is consistent"""
    # The operator should map to a class
    node_class = CW.binop_node_classes[operator]
    
    # The class should be a subclass of some base node type
    assert issubclass(node_class, CW.Node)
    
    # Creating a node with this operator should return an instance of this class
    pos = (0, 0)
    left = CW.IntNode(pos=pos, value='1')
    right = CW.IntNode(pos=pos, value='2')
    node = CW.binop_node(pos=pos, operator=operator, operand1=left, operand2=right)
    
    assert isinstance(node, node_class)


@given(values=st.lists(int_values, min_size=2, max_size=10), pos=positions)
def test_complex_expression_tree(values, pos):
    """Test building and serializing a complex expression tree"""
    if len(values) < 2:
        return
    
    # Build a left-associative expression tree with + operators
    nodes = [CW.IntNode(pos=pos, value=v) for v in values]
    
    result = nodes[0]
    for node in nodes[1:]:
        result = CW.binop_node(pos=pos, operator='+', operand1=result, operand2=node)
    
    # Serialize
    writer = CW.CodeWriter()
    output = writer.write(result)
    serialized = output.s
    
    # All values should appear in the serialized output
    for value in values:
        assert value in serialized
    
    # There should be len(values)-1 plus operators
    assert serialized.count('+') == len(values) - 1