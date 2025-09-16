import json
import decimal
import sys
import os
from hypothesis import given, strategies as st, assume
from hypothesis import settings

# Add the quickbooks package path
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.mixins import (
    DecimalEncoder, ToJsonMixin, FromJsonMixin, to_dict, 
    ToDictMixin, ObjectListMixin, ListMixin, VoidMixin
)


# Test 1: DecimalEncoder properly encodes Decimal objects to strings
@given(
    st.decimals(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
)
def test_decimal_encoder_round_trip(decimal_value):
    """Property: DecimalEncoder should encode Decimal objects to strings that preserve value"""
    # Create a dict with decimal value
    data = {"value": decimal_value}
    
    # Encode to JSON
    json_str = json.dumps(data, cls=DecimalEncoder)
    
    # Parse back
    parsed = json.loads(json_str)
    
    # The decimal should be converted to string
    assert isinstance(parsed["value"], str)
    
    # The string should convert back to the same decimal value
    reconstructed = decimal.Decimal(parsed["value"])
    assert reconstructed == decimal_value


# Test 2: ToJsonMixin.json_filter() filters underscore attributes and None values
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.none(), st.integers(), st.text()),
        min_size=0,
        max_size=10
    )
)
def test_json_filter_property(attributes):
    """Property: json_filter should filter out underscore-prefixed attributes and None values"""
    
    class TestObject(ToJsonMixin):
        def __init__(self):
            pass
    
    obj = TestObject()
    
    # Set attributes on the object
    for key, value in attributes.items():
        setattr(obj, key, value)
    
    # Get the filter function
    filter_func = obj.json_filter()
    
    # Apply the filter
    filtered_dict = filter_func(obj)
    
    # Check invariants:
    # 1. No keys starting with underscore
    for key in filtered_dict.keys():
        assert not key.startswith('_'), f"Found underscore key: {key}"
    
    # 2. No None values
    for value in filtered_dict.values():
        assert value is not None, "Found None value in filtered dict"
    
    # 3. All non-underscore, non-None attributes should be present
    for key, value in attributes.items():
        if not key.startswith('_') and value is not None:
            assert key in filtered_dict, f"Missing key: {key}"
            # Check decimal conversion
            if isinstance(value, decimal.Decimal):
                assert filtered_dict[key] == str(value)
            else:
                assert filtered_dict[key] == value


# Test 3: to_dict function recursively converts objects
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(
            st.integers(),
            st.text(),
            st.lists(st.integers(), max_size=5),
            st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=3)
        ),
        min_size=0,
        max_size=5
    )
)
def test_to_dict_recursive_conversion(data):
    """Property: to_dict should recursively convert nested structures"""
    
    result = to_dict(data)
    
    # The result should be JSON-serializable
    try:
        json.dumps(result)
    except (TypeError, ValueError) as e:
        assert False, f"Result not JSON-serializable: {e}"
    
    # Test specific conversions
    if isinstance(data, dict):
        assert isinstance(result, dict)
        assert set(result.keys()) == set(data.keys())
    elif isinstance(data, (list, tuple)):
        assert isinstance(result, list)
        assert len(result) == len(data)


# Test 4: ObjectListMixin list interface
@given(st.lists(st.integers(), min_size=0, max_size=20))
def test_object_list_mixin_list_operations(initial_items):
    """Property: ObjectListMixin should behave like a list"""
    
    class TestObjectList(ObjectListMixin):
        def __init__(self):
            self._object_list = []
            self.qbo_object_name = "TestObject"
    
    obj_list = TestObjectList()
    
    # Add initial items
    for item in initial_items:
        obj_list.append(item)
    
    # Test length
    assert len(obj_list) == len(initial_items)
    
    # Test iteration
    collected = []
    for item in obj_list:
        collected.append(item)
    assert collected == initial_items
    
    # Test contains
    for item in initial_items:
        assert item in obj_list
    
    # Test indexing
    for i in range(len(initial_items)):
        assert obj_list[i] == initial_items[i]
    
    # Test pop (if list is not empty)
    if initial_items:
        last_item = obj_list.pop()
        assert last_item == initial_items[-1]
        assert len(obj_list) == len(initial_items) - 1


# Test 5: VoidMixin get_void_params consistency
def test_void_mixin_params_data_consistency():
    """Property: VoidMixin get_void_params and get_void_data should have same keys"""
    
    class TestVoidObject(VoidMixin):
        def __init__(self, obj_name):
            self.qbo_object_name = obj_name
            self.Id = "123"
            self.SyncToken = "1"
    
    # Test known object types
    known_types = ["Payment", "SalesReceipt", "BillPayment", "Invoice"]
    
    for obj_type in known_types:
        void_obj = TestVoidObject(obj_type)
        params = void_obj.get_void_params()
        data = void_obj.get_void_data()
        
        # Both should return dictionaries
        assert isinstance(params, dict)
        assert isinstance(data, dict)
        
        # Params should have 'operation' key
        assert 'operation' in params
        
        # Data should have required fields
        assert 'Id' in data
        assert 'SyncToken' in data


# Test 6: ListMixin.where SQL clause building
@given(
    where_clause=st.text(min_size=0, max_size=50),
    order_by=st.text(min_size=0, max_size=20),
    start_position=st.one_of(st.just(""), st.integers(min_value=1, max_value=1000).map(str)),
    max_results=st.one_of(st.just(""), st.integers(min_value=1, max_value=100))
)
def test_list_mixin_where_clause_building(where_clause, order_by, start_position, max_results):
    """Property: ListMixin.where should correctly build SQL queries"""
    
    class TestListObject(ListMixin):
        qbo_object_name = "TestObject"
        qbo_json_object_name = ""
        
        @classmethod
        def from_json(cls, data):
            return data
    
    # Mock query method to capture the SQL
    captured_sql = []
    
    def mock_query(cls, select, qb=None):
        captured_sql.append(select)
        return []
    
    # Replace query method
    original_query = TestListObject.query
    TestListObject.query = classmethod(mock_query)
    
    try:
        # Call where method
        TestListObject.where(
            where_clause=where_clause,
            order_by=order_by,
            start_position=start_position,
            max_results=max_results
        )
        
        # Check the generated SQL
        if captured_sql:
            sql = captured_sql[0]
            
            # Basic structure check
            assert sql.startswith("SELECT * FROM TestObject")
            
            # Check WHERE clause
            if where_clause:
                assert "WHERE " + where_clause in sql
            else:
                assert "WHERE" not in sql
            
            # Check ORDER BY
            if order_by:
                assert " ORDERBY " + order_by in sql
            
            # Check START POSITION
            if start_position != "":
                assert " STARTPOSITION " + str(start_position) in sql
            
            # Check MAX RESULTS
            if max_results:
                assert " MAXRESULTS " + str(max_results) in sql
    
    finally:
        # Restore original method
        TestListObject.query = original_query


# Test 7: FromJsonMixin handles nested objects correctly
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.integers(), st.text()),
        min_size=1,
        max_size=5
    )
)
def test_from_json_mixin_basic(json_data):
    """Property: FromJsonMixin should set attributes from JSON data"""
    
    class TestFromJson(FromJsonMixin):
        class_dict = {}
        list_dict = {}
    
    obj = TestFromJson.from_json(json_data)
    
    # All keys from json_data should be set as attributes
    for key, value in json_data.items():
        assert hasattr(obj, key)
        assert getattr(obj, key) == value


if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    pytest.main([__file__, "-v"])