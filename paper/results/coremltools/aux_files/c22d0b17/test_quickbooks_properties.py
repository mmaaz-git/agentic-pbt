import math
import hashlib
import hmac
import base64
from hypothesis import given, strategies as st, assume, settings
from quickbooks import utils, exceptions
from quickbooks.client import QuickBooks, to_bytes
import pytest


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans()
    )
))
def test_build_where_clause_sql_injection_protection(params):
    """Test that build_where_clause properly escapes single quotes to prevent SQL injection"""
    where_clause = utils.build_where_clause(**params)
    
    for key, value in params.items():
        if isinstance(value, str) and "'" in value:
            escaped_value = value.replace("'", r"\'")
            assert escaped_value in where_clause
            assert f"'{value}'" not in where_clause


@given(st.lists(
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    ),
    min_size=1
), st.text(min_size=1))
def test_build_choose_clause_sql_injection_protection(choices, field):
    """Test that build_choose_clause properly escapes single quotes to prevent SQL injection"""
    where_clause = utils.build_choose_clause(choices, field)
    
    for choice in choices:
        if isinstance(choice, str) and "'" in choice:
            escaped_choice = choice.replace("'", r"\'")
            assert escaped_choice in where_clause
            if len(choice) > 1:
                assert f"'{choice}'" not in where_clause


@given(st.integers())
def test_exception_code_range_mapping(error_code):
    """Test that error codes map to correct exception types according to documented ranges"""
    
    error = {
        "Message": "Test error",
        "Detail": "Test detail",
        "code": error_code
    }
    fault = {"Error": [error]}
    
    try:
        QuickBooks.handle_exceptions(fault)
        assert False, "Should have raised an exception"
    except exceptions.QuickbooksException as e:
        if 0 < error_code <= 499:
            assert isinstance(e, exceptions.AuthorizationException)
        elif 500 <= error_code <= 599:
            assert isinstance(e, exceptions.UnsupportedException)
        elif 600 <= error_code <= 1999:
            if error_code == 610:
                assert isinstance(e, exceptions.ObjectNotFoundException)
            else:
                assert isinstance(e, exceptions.GeneralException)
        elif 2000 <= error_code <= 4999:
            assert isinstance(e, exceptions.ValidationException)
        elif error_code >= 10000:
            assert isinstance(e, exceptions.SevereException)
        else:
            assert type(e) == exceptions.QuickbooksException


@given(st.binary(min_size=1, max_size=1000), st.text(min_size=1, max_size=100))
def test_webhook_signature_validation_round_trip(request_body, verifier_token):
    """Test that webhook signature validation correctly verifies HMAC signatures"""
    
    # Generate a valid signature
    hmac_hash = hmac.new(
        to_bytes(verifier_token),
        request_body,
        hashlib.sha256
    ).digest()
    valid_signature = base64.b64encode(hmac_hash).decode('utf-8')
    
    # Create QuickBooks instance with verifier token
    qb = QuickBooks()
    qb.verifier_token = verifier_token
    
    # Test that valid signature passes
    request_body_str = request_body.decode('utf-8', errors='replace')
    assert qb.validate_webhook_signature(request_body_str, valid_signature) == True
    
    # Test that invalid signature fails
    invalid_signature = base64.b64encode(b"invalid").decode('utf-8')
    assert qb.validate_webhook_signature(request_body_str, invalid_signature) == False


@given(st.text())
def test_isvalid_object_name_property(object_name):
    """Test that isvalid_object_name only accepts predefined business objects"""
    qb = QuickBooks()
    
    if object_name in qb._BUSINESS_OBJECTS:
        assert qb.isvalid_object_name(object_name) == True
    else:
        with pytest.raises(Exception) as exc_info:
            qb.isvalid_object_name(object_name)
        assert f"{object_name} is not a valid QBO Business Object" in str(exc_info.value)


@given(st.booleans())
def test_api_url_sandbox_switching(sandbox):
    """Test that api_url property returns correct URL based on sandbox flag"""
    qb = QuickBooks()
    qb.sandbox = sandbox
    
    if sandbox:
        assert qb.api_url == "https://sandbox-quickbooks.api.intuit.com/v3"
    else:
        assert qb.api_url == "https://quickbooks.api.intuit.com/v3"


@given(st.dictionaries(
    st.text(min_size=1, alphabet=st.characters(blacklist_characters=["'"])),
    st.text(alphabet=st.characters(blacklist_characters=["'"]))
))
def test_build_where_clause_without_quotes(params):
    """Test build_where_clause with inputs that don't contain quotes"""
    where_clause = utils.build_where_clause(**params)
    
    if params:
        parts = where_clause.split(" AND ")
        assert len(parts) == len(params)
        
        for key, value in params.items():
            if isinstance(value, str):
                assert f"{key} = '{value}'" in where_clause
            else:
                assert f"{key} = {value}" in where_clause


@given(st.text(min_size=1).filter(lambda x: "'" in x))
def test_single_quote_escaping_invariant(text_with_quote):
    """Test that single quotes are always escaped in build_where_clause"""
    params = {"field": text_with_quote}
    where_clause = utils.build_where_clause(**params)
    
    # Count unescaped single quotes (not preceded by backslash)
    import re
    unescaped = re.findall(r"(?<!\\)'", where_clause)
    # Should only have the surrounding quotes, not the ones from the value
    assert len(unescaped) == 2  # Only the surrounding quotes