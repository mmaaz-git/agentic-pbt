"""Property-based tests for quickbooks.objects module"""

import sys
import json
import decimal
from hypothesis import given, strategies as st, settings, assume
import pytest

# Add the quickbooks env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.objects import (
    Customer, Invoice, Address, PhoneNumber, EmailAddress, 
    WebAddress, Ref, CustomField, Item, Vendor, Account
)
from quickbooks.mixins import DecimalEncoder


# Strategy for generating valid decimal values
decimal_strategy = st.decimals(
    min_value=decimal.Decimal('-999999999'),
    max_value=decimal.Decimal('999999999'),
    places=2,
    allow_nan=False,
    allow_infinity=False
)


# Test 1: JSON round-trip for basic objects
@given(
    line1=st.text(max_size=100),
    city=st.text(max_size=50), 
    postal_code=st.text(max_size=20),
    country=st.text(max_size=30)
)
def test_address_json_roundtrip(line1, city, postal_code, country):
    """Test that Address objects can be serialized to JSON and back without loss"""
    addr = Address()
    addr.Line1 = line1
    addr.City = city  
    addr.PostalCode = postal_code
    addr.Country = country
    
    # Convert to JSON and back
    json_str = addr.to_json()
    json_data = json.loads(json_str)
    addr_restored = Address.from_json(json_data)
    
    # Check that all set fields are preserved
    assert addr_restored.Line1 == line1
    assert addr_restored.City == city
    assert addr_restored.PostalCode == postal_code
    assert addr_restored.Country == country


# Test 2: Ref object consistency
@given(
    obj_id=st.integers(min_value=1, max_value=999999),
    display_name=st.text(min_size=1, max_size=100)
)
def test_customer_to_ref_consistency(obj_id, display_name):
    """Test that to_ref() maintains consistency with object properties"""
    customer = Customer()
    customer.Id = str(obj_id)
    customer.DisplayName = display_name
    
    ref = customer.to_ref()
    
    # Properties claimed by the implementation
    assert ref.value == str(obj_id)
    assert ref.name == display_name
    assert ref.type == "Customer"


# Test 3: DecimalEncoder handles various decimal values
@given(value=decimal_strategy)
def test_decimal_encoder_handles_decimals(value):
    """Test that DecimalEncoder properly handles decimal values"""
    data = {"amount": value, "nested": {"val": value}}
    
    # Should not raise an exception
    json_str = json.dumps(data, cls=DecimalEncoder)
    
    # Should be parseable back
    parsed = json.loads(json_str)
    
    # The decimal should be converted to string
    assert parsed["amount"] == str(value)
    assert parsed["nested"]["val"] == str(value)


# Test 4: PhoneNumber to_json preserves data
@given(phone=st.text(max_size=50))
def test_phone_number_json_roundtrip(phone):
    """Test PhoneNumber JSON serialization round-trip"""
    phone_obj = PhoneNumber()
    phone_obj.FreeFormNumber = phone
    
    json_str = phone_obj.to_json()
    json_data = json.loads(json_str)
    phone_restored = PhoneNumber.from_json(json_data)
    
    assert phone_restored.FreeFormNumber == phone


# Test 5: EmailAddress preservation
@given(email=st.text(max_size=100))
def test_email_address_json_roundtrip(email):
    """Test EmailAddress JSON serialization round-trip"""
    email_obj = EmailAddress()
    email_obj.Address = email
    
    json_str = email_obj.to_json()
    json_data = json.loads(json_str)
    email_restored = EmailAddress.from_json(json_data)
    
    assert email_restored.Address == email


# Test 6: CustomField preservation
@given(
    def_id=st.text(max_size=50),
    field_type=st.text(max_size=20),
    name=st.text(max_size=100),
    value=st.text(max_size=500)
)  
def test_custom_field_json_roundtrip(def_id, field_type, name, value):
    """Test CustomField JSON serialization round-trip"""
    field = CustomField()
    field.DefinitionId = def_id
    field.Type = field_type
    field.Name = name
    field.StringValue = value
    
    json_str = field.to_json()
    json_data = json.loads(json_str)
    field_restored = CustomField.from_json(json_data)
    
    assert field_restored.DefinitionId == def_id
    assert field_restored.Type == field_type
    assert field_restored.Name == name
    assert field_restored.StringValue == value


# Test 7: to_dict excludes private attributes
@given(
    public_val=st.text(max_size=50),
    private_val=st.text(max_size=50)
)
def test_to_dict_excludes_private_attrs(public_val, private_val):
    """Test that to_dict excludes private attributes (starting with _)"""
    addr = Address()
    addr.Line1 = public_val
    addr._private_attr = private_val  # This should be excluded
    
    dict_repr = addr.to_dict()
    
    # Public attribute should be included
    assert "Line1" in dict_repr
    assert dict_repr["Line1"] == public_val
    
    # Private attribute should be excluded
    assert "_private_attr" not in dict_repr


# Test 8: Invoice to_ref consistency
@given(
    invoice_id=st.integers(min_value=1, max_value=999999),
    doc_number=st.text(min_size=1, max_size=50)
)
def test_invoice_to_ref_consistency(invoice_id, doc_number):
    """Test that Invoice.to_ref() maintains consistency"""
    invoice = Invoice()
    invoice.Id = str(invoice_id)
    invoice.DocNumber = doc_number
    
    ref = invoice.to_ref()
    
    assert ref.value == str(invoice_id)
    assert ref.name == doc_number
    assert ref.type == "Invoice"


# Test 9: WebAddress JSON round-trip
@given(uri=st.text(max_size=200))
def test_web_address_json_roundtrip(uri):
    """Test WebAddress JSON serialization round-trip"""
    web = WebAddress()
    web.URI = uri
    
    json_str = web.to_json()
    json_data = json.loads(json_str)
    web_restored = WebAddress.from_json(json_data)
    
    assert web_restored.URI == uri


# Test 10: Complex nested object JSON round-trip
@given(
    cust_id=st.integers(min_value=1, max_value=999999),
    display_name=st.text(min_size=1, max_size=100),
    given_name=st.text(max_size=50),
    family_name=st.text(max_size=50),
    company_name=st.text(max_size=100),
    phone_number=st.text(max_size=50),
    email_address=st.text(max_size=100),
    line1=st.text(max_size=100),
    city=st.text(max_size=50),
    postal_code=st.text(max_size=20),
    active=st.booleans(),
    taxable=st.booleans()
)
def test_customer_complex_json_roundtrip(
    cust_id, display_name, given_name, family_name, company_name,
    phone_number, email_address, line1, city, postal_code, active, taxable
):
    """Test Customer with nested objects JSON round-trip"""
    customer = Customer()
    customer.Id = str(cust_id)
    customer.DisplayName = display_name
    customer.GivenName = given_name
    customer.FamilyName = family_name
    customer.CompanyName = company_name
    customer.Active = active
    customer.Taxable = taxable
    
    # Add nested objects
    if phone_number:
        customer.PrimaryPhone = PhoneNumber()
        customer.PrimaryPhone.FreeFormNumber = phone_number
    
    if email_address:
        customer.PrimaryEmailAddr = EmailAddress()
        customer.PrimaryEmailAddr.Address = email_address
    
    if line1 or city:
        customer.BillAddr = Address()
        customer.BillAddr.Line1 = line1
        customer.BillAddr.City = city
        customer.BillAddr.PostalCode = postal_code
    
    # Convert to JSON and back
    json_str = customer.to_json()
    json_data = json.loads(json_str)
    customer_restored = Customer.from_json(json_data)
    
    # Check main fields
    assert customer_restored.Id == str(cust_id)
    assert customer_restored.DisplayName == display_name
    assert customer_restored.GivenName == given_name
    assert customer_restored.FamilyName == family_name
    assert customer_restored.CompanyName == company_name
    assert customer_restored.Active == active
    assert customer_restored.Taxable == taxable
    
    # Check nested objects
    if phone_number:
        assert customer_restored.PrimaryPhone.FreeFormNumber == phone_number
    
    if email_address:
        assert customer_restored.PrimaryEmailAddr.Address == email_address
    
    if line1 or city:
        assert customer_restored.BillAddr.Line1 == line1
        assert customer_restored.BillAddr.City == city
        assert customer_restored.BillAddr.PostalCode == postal_code