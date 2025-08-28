#!/usr/bin/env python3
"""Property-based tests for QuickBooks module."""

import json
import sys
import base64
import hashlib
import hmac
from datetime import datetime, timezone
from decimal import Decimal

sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

from quickbooks import client, exceptions, helpers, utils
from quickbooks.objects.base import Address, EmailAddress, Ref, PhoneNumber, WebAddress
from quickbooks.mixins import DecimalEncoder


# Test 1: WHERE clause SQL injection prevention
@given(
    key=st.text(min_size=1, max_size=50).filter(lambda x: not x.startswith('_')),
    value=st.text(min_size=0, max_size=100)
)
def test_build_where_clause_escapes_quotes(key, value):
    """Test that build_where_clause properly escapes single quotes to prevent SQL injection."""
    result = utils.build_where_clause(**{key: value})
    
    # Property: Single quotes in the value should be escaped with backslash
    if "'" in value:
        # The original single quotes should be escaped
        assert r"\'" in result
        # No unescaped single quotes should exist in the value part
        # Split by = to get the value part
        if " = " in result:
            value_part = result.split(" = ", 1)[1]
            # Remove the surrounding quotes
            if value_part.startswith("'") and value_part.endswith("'"):
                inner_value = value_part[1:-1]
                # Check that all single quotes are escaped
                # Count unescaped quotes (not preceded by backslash)
                i = 0
                unescaped_count = 0
                while i < len(inner_value):
                    if inner_value[i] == "'":
                        if i == 0 or inner_value[i-1] != "\\":
                            unescaped_count += 1
                    i += 1
                assert unescaped_count == 0, f"Found unescaped quotes in WHERE clause value: {result}"


# Test 2: Exception error code mapping
@given(error_code=st.integers(min_value=-10000, max_value=20000))
def test_handle_exceptions_error_code_mapping(error_code):
    """Test that error codes are mapped to the correct exception types as documented."""
    error_data = {
        "Fault": {
            "Error": [{
                "Message": "Test error",
                "code": str(error_code) if error_code >= 0 else str(error_code),
                "Detail": "Test detail"
            }]
        }
    }
    
    # Test the documented error code ranges
    try:
        client.QuickBooks.handle_exceptions(error_data["Fault"])
        # If no exception was raised, the error code should be <= 0
        assert error_code <= 0
    except exceptions.AuthorizationException:
        # Error codes 1-499 should raise AuthorizationException
        assert 0 < error_code <= 499
    except exceptions.UnsupportedException:
        # Error codes 500-599 should raise UnsupportedException  
        assert 500 <= error_code <= 599
    except exceptions.ObjectNotFoundException:
        # Error code 610 specifically
        assert error_code == 610
    except exceptions.GeneralException:
        # Error codes 600-1999 (except 610) should raise GeneralException
        assert (600 <= error_code <= 1999) and error_code != 610
    except exceptions.ValidationException:
        # Error codes 2000-4999 should raise ValidationException
        assert 2000 <= error_code <= 4999
    except exceptions.SevereException:
        # Error codes >= 10000 should raise SevereException
        assert error_code >= 10000
    except exceptions.QuickbooksException:
        # Other error codes
        assert error_code < 0 or (error_code > 4999 and error_code < 10000)


# Test 3: JSON round-trip for base objects
@given(
    line1=st.text(max_size=100),
    city=st.text(max_size=50),
    postal_code=st.text(max_size=20),
    country_code=st.text(max_size=10)
)
def test_address_json_roundtrip(line1, city, postal_code, country_code):
    """Test that Address objects survive JSON serialization/deserialization."""
    original = Address()
    original.Line1 = line1
    original.City = city
    original.PostalCode = postal_code
    original.CountrySubDivisionCode = country_code
    
    # Serialize to JSON
    json_str = original.to_json()
    json_data = json.loads(json_str)
    
    # Deserialize back
    restored = Address.from_json(json_data)
    
    # Property: Round-trip should preserve all set fields
    assert restored.Line1 == line1
    assert restored.City == city
    assert restored.PostalCode == postal_code
    assert restored.CountrySubDivisionCode == country_code


# Test 4: Webhook signature validation properties
@given(
    request_body=st.text(min_size=1, max_size=1000),
    verifier_token=st.text(min_size=1, max_size=100)
)
def test_webhook_signature_validation(request_body, verifier_token):
    """Test webhook signature validation has correct cryptographic properties."""
    qb = client.QuickBooks()
    qb.verifier_token = verifier_token
    
    # Generate correct signature
    correct_hash = hmac.new(
        bytes(verifier_token, "utf-8"),
        request_body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    correct_signature = base64.b64encode(correct_hash).decode('utf-8')
    
    # Property 1: Correct signature should validate
    assert qb.validate_webhook_signature(request_body, correct_signature, verifier_token)
    
    # Property 2: Different request body should fail validation
    if len(request_body) > 1:
        modified_body = request_body[:-1] + ('x' if request_body[-1] != 'x' else 'y')
        assert not qb.validate_webhook_signature(modified_body, correct_signature, verifier_token)
    
    # Property 3: Different token should fail validation
    wrong_token = verifier_token + "x"
    assert not qb.validate_webhook_signature(request_body, correct_signature, wrong_token)


# Test 5: DecimalEncoder handles Decimal values
@given(
    value=st.decimals(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
)
def test_decimal_encoder_handles_decimals(value):
    """Test that DecimalEncoder properly serializes Decimal values."""
    from quickbooks.mixins import DecimalEncoder
    
    data = {"amount": value}
    
    # Should not raise an exception
    json_str = json.dumps(data, cls=DecimalEncoder)
    
    # Property: Decimal values should be serialized as strings
    parsed = json.loads(json_str)
    assert isinstance(parsed["amount"], str)
    
    # Property: The string representation should convert back to the same Decimal value
    restored = Decimal(parsed["amount"])
    assert restored == value


# Test 6: build_choose_clause SQL injection prevention
@given(
    choices=st.lists(st.text(min_size=0, max_size=50), min_size=1, max_size=10),
    field=st.text(min_size=1, max_size=30).filter(lambda x: not x.startswith('_'))
)
def test_build_choose_clause_escapes_quotes(choices, field):
    """Test that build_choose_clause properly escapes single quotes."""
    result = utils.build_choose_clause(choices, field)
    
    # The result should be in format: field in (values)
    assert result.startswith(f"{field} in (")
    assert result.endswith(")")
    
    # Extract the values part
    values_part = result[len(f"{field} in ("):-1]
    
    # For string choices with quotes, they should be escaped
    for choice in choices:
        if isinstance(choice, str) and "'" in choice:
            # The choice should appear escaped in the result
            escaped_choice = choice.replace(r"'", r"\'")
            assert escaped_choice in result


# Test 7: Date formatting functions
@given(dt=st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31)))
def test_qb_date_format(dt):
    """Test that QB date formatting produces valid format."""
    result = helpers.qb_date_format(dt)
    
    # Property: Should be in YYYY-MM-DD format
    assert len(result) == 10
    assert result[4] == '-' and result[7] == '-'
    
    # Property: Should be parseable back to a date
    year, month, day = result.split('-')
    assert int(year) == dt.year
    assert int(month) == dt.month
    assert int(day) == dt.day


@given(dt=st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31)))
def test_qb_datetime_format(dt):
    """Test that QB datetime formatting produces valid format."""
    result = helpers.qb_datetime_format(dt)
    
    # Property: Should be in YYYY-MM-DDTHH:MM:SS format
    assert 'T' in result
    date_part, time_part = result.split('T')
    
    # Verify date part
    assert len(date_part) == 10
    year, month, day = date_part.split('-')
    assert int(year) == dt.year
    assert int(month) == dt.month
    assert int(day) == dt.day
    
    # Verify time part
    assert len(time_part) == 8
    hour, minute, second = time_part.split(':')
    assert int(hour) == dt.hour
    assert int(minute) == dt.minute
    assert int(second) == dt.second


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])