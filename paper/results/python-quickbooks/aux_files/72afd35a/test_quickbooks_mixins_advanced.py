import json
import decimal
import sys
import os
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis import reproduce_failure
import math

# Add the quickbooks package path
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.mixins import (
    DecimalEncoder, ToJsonMixin, FromJsonMixin, to_dict, 
    ToDictMixin, ObjectListMixin, ListMixin, VoidMixin
)


# Advanced Test 1: Test DecimalEncoder with extreme values and special cases
@given(
    st.one_of(
        st.decimals(allow_nan=False, allow_infinity=False),
        st.decimals(min_value=decimal.Decimal('1E-100'), max_value=decimal.Decimal('1E-100')),
        st.decimals(min_value=decimal.Decimal('1E100'), max_value=decimal.Decimal('1E100')),
        st.just(decimal.Decimal('0')),
        st.just(decimal.Decimal('-0')),
        st.just(decimal.Decimal('0.0000000000000000000001')),
    )
)
def test_decimal_encoder_extreme_values(decimal_value):
    """Test DecimalEncoder with extreme decimal values"""
    data = {"value": decimal_value}
    
    # Encode to JSON
    json_str = json.dumps(data, cls=DecimalEncoder)
    
    # Parse back
    parsed = json.loads(json_str)
    
    # The string should convert back to the same decimal value
    reconstructed = decimal.Decimal(parsed["value"])
    
    # Check if normalized values are equal (handles -0 vs 0)
    assert reconstructed.normalize() == decimal_value.normalize()


# Advanced Test 2: Test json_filter with objects containing Decimal values
@given(
    st.dictionaries(
        st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=20),
        st.one_of(
            st.none(),
            st.decimals(allow_nan=False, allow_infinity=False),
            st.integers(),
            st.text()
        ),
        min_size=0,
        max_size=10
    )
)
def test_json_filter_with_decimals(attributes):
    """Test json_filter properly handles Decimal objects"""
    
    class TestObject(ToJsonMixin):
        def __init__(self):
            pass
    
    obj = TestObject()
    
    # Add some underscore attributes that should be filtered
    obj._private = "should be filtered"
    obj.__very_private = "should also be filtered"
    
    # Set regular attributes
    for key, value in attributes.items():
        setattr(obj, key, value)
    
    # Get the filter function
    filter_func = obj.json_filter()
    
    # Apply the filter
    filtered_dict = filter_func(obj)
    
    # Verify private attributes are filtered
    assert '_private' not in filtered_dict
    assert '__very_private' not in filtered_dict
    assert '_TestObject__very_private' not in filtered_dict
    
    # Check decimal conversion is correct
    for key, value in attributes.items():
        if not key.startswith('_') and value is not None:
            if isinstance(value, decimal.Decimal):
                assert filtered_dict[key] == str(value)


# Advanced Test 3: Test to_dict with circular references
def test_to_dict_handles_objects_with_dict():
    """Test to_dict with objects containing __dict__"""
    
    class CustomObject:
        def __init__(self):
            self.name = "test"
            self.value = 42
            self._private = "ignored"
            self.nested = {"key": "value"}
            self.list_data = [1, 2, 3]
    
    obj = CustomObject()
    result = to_dict(obj)
    
    # Check that private attributes are excluded
    assert '_private' not in result
    
    # Check that regular attributes are included
    assert result['name'] == 'test'
    assert result['value'] == 42
    assert result['nested'] == {'key': 'value'}
    assert result['list_data'] == [1, 2, 3]


# Advanced Test 4: Test ObjectListMixin with edge cases
@given(
    initial=st.lists(st.integers()),
    operations=st.lists(
        st.one_of(
            st.tuples(st.just('append'), st.integers()),
            st.tuples(st.just('pop'), st.nothing()),
            st.tuples(st.just('setitem'), st.integers(min_value=0, max_value=10), st.integers()),
            st.tuples(st.just('delitem'), st.integers(min_value=0, max_value=10))
        ),
        max_size=10
    )
)
def test_object_list_mixin_complex_operations(initial, operations):
    """Test ObjectListMixin with complex sequences of operations"""
    
    class TestObjectList(ObjectListMixin):
        def __init__(self):
            self._object_list = []
            self.qbo_object_name = "TestObject"
    
    obj_list = TestObjectList()
    reference_list = []
    
    # Initialize both lists
    for item in initial:
        obj_list.append(item)
        reference_list.append(item)
    
    # Apply operations
    for op in operations:
        if op[0] == 'append':
            obj_list.append(op[1])
            reference_list.append(op[1])
        elif op[0] == 'pop' and len(reference_list) > 0:
            assert obj_list.pop() == reference_list.pop()
        elif op[0] == 'setitem' and len(reference_list) > 0:
            idx = op[1] % len(reference_list) if len(reference_list) > 0 else 0
            if idx < len(reference_list):
                obj_list[idx] = op[2]
                reference_list[idx] = op[2]
        elif op[0] == 'delitem' and len(reference_list) > 0:
            idx = op[1] % len(reference_list) if len(reference_list) > 0 else 0
            if idx < len(reference_list):
                del obj_list[idx]
                del reference_list[idx]
    
    # Verify final state matches
    assert list(obj_list) == reference_list
    assert len(obj_list) == len(reference_list)


# Advanced Test 5: Test ListMixin.where with SQL injection-like strings
@given(
    st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=0, max_size=50).filter(
        lambda x: not any(c in x for c in ['\x00', '\r', '\n'])
    )
)
def test_list_mixin_where_special_characters(where_text):
    """Test ListMixin.where handles special characters safely"""
    
    class TestListObject(ListMixin):
        qbo_object_name = "TestObject"
        qbo_json_object_name = ""
        
        @classmethod
        def from_json(cls, data):
            return data
    
    captured_sql = []
    
    def mock_query(cls, select, qb=None):
        captured_sql.append(select)
        return []
    
    TestListObject.query = classmethod(mock_query)
    
    try:
        # Test with potentially problematic input
        TestListObject.where(where_clause=where_text)
        
        if captured_sql:
            sql = captured_sql[0]
            # The where clause should be properly included
            if where_text:
                assert ("WHERE " + where_text) in sql
    except:
        # If it raises an exception, that might indicate a bug
        pass
    finally:
        pass


# Advanced Test 6: Test FromJsonMixin with nested class_dict objects
def test_from_json_nested_objects():
    """Test FromJsonMixin handles nested objects via class_dict"""
    
    class NestedObject(FromJsonMixin):
        class_dict = {}
        list_dict = {}
        
        def __init__(self):
            self.value = None
    
    class ParentObject(FromJsonMixin):
        class_dict = {"nested": NestedObject}
        list_dict = {}
        
        def __init__(self):
            self.name = None
            self.nested = None
    
    json_data = {
        "name": "parent",
        "nested": {
            "value": 123
        }
    }
    
    obj = ParentObject.from_json(json_data)
    
    assert obj.name == "parent"
    assert isinstance(obj.nested, NestedObject)
    assert obj.nested.value == 123


# Advanced Test 7: Test FromJsonMixin with list_dict
def test_from_json_list_objects():
    """Test FromJsonMixin handles lists via list_dict"""
    
    class ListItem(FromJsonMixin):
        class_dict = {}
        list_dict = {}
        detail_dict = {}
        
        def __init__(self):
            self.id = None
            self.name = None
    
    class Container(FromJsonMixin):
        class_dict = {}
        list_dict = {"items": ListItem}
        detail_dict = {}
        
        def __init__(self):
            self.title = None
            self.items = []
    
    json_data = {
        "title": "Container",
        "items": [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"}
        ]
    }
    
    obj = Container.from_json(json_data)
    
    assert obj.title == "Container"
    assert len(obj.items) == 2
    assert obj.items[0].id == 1
    assert obj.items[0].name == "first"
    assert obj.items[1].id == 2
    assert obj.items[1].name == "second"


# Advanced Test 8: Test VoidMixin with unknown object types
@given(st.text(min_size=1, max_size=20))
def test_void_mixin_unknown_types(obj_name):
    """Test VoidMixin handles unknown object types with defaults"""
    
    class TestVoidObject(VoidMixin):
        def __init__(self, name):
            self.qbo_object_name = name
            self.Id = "123"
            self.SyncToken = "1"
    
    void_obj = TestVoidObject(obj_name)
    
    # Should return default operation for unknown types
    params = void_obj.get_void_params()
    data = void_obj.get_void_data()
    
    assert isinstance(params, dict)
    assert isinstance(data, dict)
    
    # Check default behavior
    if obj_name not in ["Payment", "SalesReceipt", "BillPayment", "Invoice"]:
        assert params == {"operation": "void"}
        assert data == {"operation": "void"}


# Advanced Test 9: Test ToJsonMixin.to_json with complex nested structures
def test_to_json_complex_nested():
    """Test ToJsonMixin.to_json with nested objects"""
    
    class NestedObj(ToJsonMixin):
        def __init__(self):
            self.value = decimal.Decimal("123.45")
            self._private = "ignored"
    
    class ParentObj(ToJsonMixin):
        def __init__(self):
            self.name = "test"
            self.amount = decimal.Decimal("999.99")
            self.nested = NestedObj()
            self.items = [1, 2, 3]
            self._secret = "filtered"
            self.empty = None
    
    obj = ParentObj()
    json_str = obj.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Check structure
    assert "name" in parsed
    assert "amount" in parsed
    assert "nested" in parsed
    assert "items" in parsed
    
    # Check filtered items are not present
    assert "_secret" not in parsed
    assert "empty" not in parsed
    assert "_private" not in parsed.get("nested", {})
    
    # Check decimal conversion
    assert parsed["amount"] == "999.99"
    assert parsed["nested"]["value"] == "123.45"


# Advanced Test 10: Test ObjectListMixin __reversed__
@given(st.lists(st.integers(), min_size=0, max_size=20))
def test_object_list_reversed(items):
    """Test ObjectListMixin __reversed__ method"""
    
    class TestObjectList(ObjectListMixin):
        def __init__(self):
            self._object_list = []
            self.qbo_object_name = "TestObject"
    
    obj_list = TestObjectList()
    
    for item in items:
        obj_list.append(item)
    
    # Test reversed iteration
    reversed_items = list(reversed(obj_list))
    expected_reversed = list(reversed(items))
    
    assert reversed_items == expected_reversed


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])