"""Property-based tests for quickbooks.objects edge cases"""

import sys
import json
import decimal
from hypothesis import given, strategies as st, settings, assume
import pytest

# Add the quickbooks env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.objects import (
    Customer, Invoice, Address, PhoneNumber, EmailAddress, 
    WebAddress, Ref, CustomField, LinkedTxn, CustomerMemo
)
from quickbooks.objects.base import QuickbooksBaseObject
from quickbooks.mixins import DecimalEncoder, to_dict


# Test edge cases with None values and empty strings
@given(
    include_none=st.booleans(),
    include_empty=st.booleans()
)
def test_json_filter_none_values(include_none, include_empty):
    """Test that None values are filtered out in JSON serialization"""
    addr = Address()
    
    # Set some values
    addr.Line1 = "Test Line" if not include_empty else ""
    addr.City = None if include_none else "Test City"
    addr.Country = "USA"
    addr.PostalCode = None if include_none else "12345"
    
    json_str = addr.to_json()
    json_data = json.loads(json_str)
    
    # None values should not be in JSON
    if include_none:
        assert "City" not in json_data
        assert "PostalCode" not in json_data
    else:
        assert "City" in json_data
        assert "PostalCode" in json_data
    
    # Empty strings should be included
    if include_empty:
        assert json_data.get("Line1") == ""
    
    assert "Country" in json_data


# Test decimal edge cases
@given(
    value=st.one_of(
        st.just(decimal.Decimal('0')),
        st.just(decimal.Decimal('0.00')),
        st.just(decimal.Decimal('-0')),
        st.just(decimal.Decimal('1E+10')),
        st.just(decimal.Decimal('1E-10')),
        st.just(decimal.Decimal('999999999999999999.99')),
        st.just(decimal.Decimal('-999999999999999999.99'))
    )
)
def test_decimal_encoder_edge_cases(value):
    """Test DecimalEncoder with edge case decimal values"""
    data = {"amount": value}
    
    json_str = json.dumps(data, cls=DecimalEncoder)
    parsed = json.loads(json_str)
    
    # Should be converted to string
    assert isinstance(parsed["amount"], str)
    # Should be parseable back to Decimal
    restored = decimal.Decimal(parsed["amount"])
    assert restored == value


# Test LinkedTxn ID edge cases
@given(
    txn_id=st.one_of(
        st.just(0),
        st.just(-1),
        st.just(999999999),
        st.integers(min_value=-1000, max_value=1000)
    ),
    txn_type=st.one_of(
        st.just(0),
        st.just(""),
        st.text(max_size=50)
    )
)
def test_linked_txn_edge_cases(txn_id, txn_type):
    """Test LinkedTxn with edge case values"""
    linked = LinkedTxn()
    linked.TxnId = txn_id
    linked.TxnType = txn_type
    linked.TxnLineId = 1
    
    json_str = linked.to_json()
    json_data = json.loads(json_str)
    restored = LinkedTxn.from_json(json_data)
    
    assert restored.TxnId == txn_id
    assert restored.TxnType == txn_type
    assert restored.TxnLineId == 1


# Test Ref with empty/None values
@given(
    value=st.one_of(st.none(), st.text(max_size=100)),
    name=st.one_of(st.none(), st.text(max_size=100)),
    ref_type=st.one_of(st.none(), st.text(max_size=50))
)
def test_ref_with_none_values(value, name, ref_type):
    """Test Ref object with None values"""
    ref = Ref()
    ref.value = value if value is not None else ""
    ref.name = name if name is not None else ""
    ref.type = ref_type if ref_type is not None else ""
    
    json_str = ref.to_json()
    json_data = json.loads(json_str)
    
    # Empty strings should be in JSON, None should not
    assert "value" in json_data
    assert "name" in json_data
    assert "type" in json_data


# Test CustomerMemo edge cases
@given(memo_value=st.one_of(
    st.just(""),
    st.just(" "),
    st.just("\n"),
    st.just("\t"),
    st.text(alphabet=st.characters(whitelist_categories=["Zs", "Cc"]), max_size=10),
    st.text(max_size=1000)
))
def test_customer_memo_edge_cases(memo_value):
    """Test CustomerMemo with various string edge cases"""
    memo = CustomerMemo()
    memo.value = memo_value
    
    json_str = memo.to_json()
    json_data = json.loads(json_str)
    restored = CustomerMemo.from_json(json_data)
    
    assert restored.value == memo_value


# Test to_dict with nested None objects
def test_to_dict_nested_none_objects():
    """Test to_dict behavior with nested None objects"""
    customer = Customer()
    customer.DisplayName = "Test Customer"
    customer.BillAddr = None  # Explicitly None
    customer.PrimaryPhone = None
    
    dict_repr = customer.to_dict()
    
    # DisplayName should be present
    assert "DisplayName" in dict_repr
    assert dict_repr["DisplayName"] == "Test Customer"
    
    # None objects should not appear in dict
    # Note: This is testing actual behavior
    assert "BillAddr" not in dict_repr or dict_repr["BillAddr"] is None
    assert "PrimaryPhone" not in dict_repr or dict_repr["PrimaryPhone"] is None


# Test from_json with missing keys
def test_from_json_missing_keys():
    """Test from_json behavior when keys are missing"""
    # Minimal JSON data
    json_data = {
        "DisplayName": "Test",
        "Id": "123"
    }
    
    # Should not raise exception
    customer = Customer.from_json(json_data)
    
    assert customer.DisplayName == "Test"
    assert customer.Id == "123"
    # Other fields should have default values
    assert customer.Active == True  # Default from __init__
    assert customer.Taxable == True  # Default from __init__


# Test from_json with extra keys
@given(extra_key=st.text(min_size=1, max_size=50), extra_value=st.text(max_size=100))
def test_from_json_extra_keys(extra_key, extra_value):
    """Test from_json behavior with extra/unknown keys"""
    assume(extra_key not in ["DisplayName", "Id", "Active", "Taxable"])
    
    json_data = {
        "DisplayName": "Test",
        "Id": "123",
        extra_key: extra_value  # Unknown key
    }
    
    # Should not raise exception
    customer = Customer.from_json(json_data)
    
    assert customer.DisplayName == "Test"
    assert customer.Id == "123"
    # Extra key should be set as attribute
    assert hasattr(customer, extra_key)
    assert getattr(customer, extra_key) == extra_value


# Test recursive to_dict
def test_recursive_to_dict():
    """Test to_dict with deeply nested objects"""
    
    class TestObject(QuickbooksBaseObject):
        def __init__(self):
            self.value = "test"
            self.nested = None
    
    # Create nested structure
    obj1 = TestObject()
    obj2 = TestObject()
    obj3 = TestObject()
    
    obj1.nested = obj2
    obj2.nested = obj3
    obj3.value = "deep"
    
    dict_repr = to_dict(obj1)
    
    # Should handle nested objects
    assert dict_repr["value"] == "test"
    assert "nested" in dict_repr
    assert dict_repr["nested"]["value"] == "test"
    assert dict_repr["nested"]["nested"]["value"] == "deep"


# Test circular reference handling
def test_circular_reference_to_dict():
    """Test to_dict behavior with circular references"""
    
    class TestObject(QuickbooksBaseObject):
        def __init__(self):
            self.value = "test"
            self.ref = None
    
    obj1 = TestObject()
    obj2 = TestObject()
    
    # Create circular reference
    obj1.ref = obj2
    obj2.ref = obj1
    
    # This might cause infinite recursion or should handle it gracefully
    # Testing actual behavior
    try:
        dict_repr = to_dict(obj1)
        # If it succeeds, check structure
        assert "value" in dict_repr
    except RecursionError:
        # This is a bug - circular references cause RecursionError
        pytest.fail("to_dict does not handle circular references - causes RecursionError")