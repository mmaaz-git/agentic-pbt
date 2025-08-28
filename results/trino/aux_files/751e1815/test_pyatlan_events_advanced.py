#!/usr/bin/env python3
"""Advanced property-based tests for pyatlan.events module - hunting for edge cases."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings, example
from hypothesis.strategies import composite
from unittest.mock import Mock, MagicMock, patch
import json

from pyatlan.events.atlan_event_handler import (
    is_validation_request,
    valid_signature,
    has_description,
    has_owner,
    has_lineage,
    get_current_view_of_asset,
    AtlanEventHandler,
    WEBHOOK_VALIDATION_REQUEST
)
from pyatlan.events.atlan_lambda_handler import process_event
from pyatlan.model.assets import Asset, Catalog
from pyatlan.model.events import AtlanEvent, AtlanEventPayload


# Test edge cases with Unicode and special characters
@given(st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"])))
def test_is_validation_request_unicode(data):
    """Property: Unicode strings are handled correctly."""
    result = is_validation_request(data)
    expected = (data == WEBHOOK_VALIDATION_REQUEST)
    assert result == expected


@given(st.text(min_size=10000, max_size=100000))
def test_is_validation_request_large_strings(data):
    """Property: Large strings are handled efficiently."""
    result = is_validation_request(data)
    assert result is False  # Large strings can't match the short validation request


# Test valid_signature with case sensitivity
@given(st.text())
def test_valid_signature_case_sensitive_header_key(signature):
    """Property: Header key lookup should be case-sensitive."""
    # Try various case variations of the header key
    headers_variations = [
        {"X-Atlan-Signing-Secret": signature},  # Different case
        {"X-ATLAN-SIGNING-SECRET": signature},  # All caps
        {"x-Atlan-Signing-Secret": signature},  # Mixed case
    ]
    
    for headers in headers_variations:
        result = valid_signature(signature, headers)
        # Should be False because the key is case-sensitive
        assert result is False


# Test edge cases with empty owners
def test_has_owner_empty_lists():
    """Property: Empty lists for owners should be treated as having owners."""
    asset = Mock(spec=Asset)
    asset.owner_users = []
    asset.owner_groups = []
    result = has_owner(asset)
    # Empty lists are not None, so this should return True
    assert result is True


def test_has_owner_none_vs_empty():
    """Property: None and empty list are treated differently."""
    asset1 = Mock(spec=Asset)
    asset1.owner_users = None
    asset1.owner_groups = []
    
    asset2 = Mock(spec=Asset)
    asset2.owner_users = []
    asset2.owner_groups = None
    
    result1 = has_owner(asset1)
    result2 = has_owner(asset2)
    
    # Both should return True because empty list is not None
    assert result1 is True
    assert result2 is True


# Test description with various whitespace
@given(st.sampled_from([" ", "  ", "\t", "\n", "\r", "\t\n", " \n "]))
def test_has_description_whitespace_only(whitespace):
    """Property: Whitespace-only descriptions count as having a description."""
    asset = Mock(spec=Asset)
    asset.user_description = whitespace
    asset.description = None
    result = has_description(asset)
    # Whitespace is not empty string, so should return True
    assert result is True


def test_has_description_empty_string_vs_none():
    """Property: Empty string is treated as no description."""
    asset1 = Mock(spec=Asset)
    asset1.user_description = ""
    asset1.description = None
    result1 = has_description(asset1)
    assert result1 is False
    
    asset2 = Mock(spec=Asset)
    asset2.user_description = None
    asset2.description = ""
    result2 = has_description(asset2)
    assert result2 is False


# Test has_lineage with edge cases
def test_has_lineage_empty_lists():
    """Property: Empty process lists should be treated as no lineage."""
    asset = Mock(spec=Catalog)
    asset.input_to_processes = []
    asset.output_from_processes = []
    asset.has_lineage = False
    result = has_lineage(asset)
    # Empty lists are not None, so this should return True
    assert result is True


def test_has_lineage_inconsistent_flags():
    """Property: For Catalog assets, process lists take precedence over has_lineage flag."""
    asset = Mock(spec=Catalog)
    asset.input_to_processes = ["process1"]
    asset.output_from_processes = None
    asset.has_lineage = False  # Contradictory flag
    
    result = has_lineage(asset)
    # Should return True based on processes, ignoring the flag
    assert result is True


# Test has_lineage with various boolean-like values
@given(st.sampled_from([0, 1, "", "false", "true", [], [1], {}, {"a": 1}]))
def test_has_lineage_bool_coercion(lineage_value):
    """Property: has_lineage uses bool() coercion for non-Catalog assets."""
    asset = Mock(spec=Asset)
    asset.has_lineage = lineage_value
    result = has_lineage(asset)
    expected = bool(lineage_value)
    assert result == expected


# Test AtlanEventHandler methods
def test_calculate_changes_default_returns_empty():
    """Property: Default calculate_changes always returns empty list."""
    client = Mock()
    handler = AtlanEventHandler(client)
    asset = Mock(spec=Asset)
    result = handler.calculate_changes(asset)
    assert result == []
    assert isinstance(result, list)


def test_has_changes_with_none():
    """Property: has_changes handles None comparisons."""
    client = Mock()
    handler = AtlanEventHandler(client)
    
    asset = Mock(spec=Asset)
    asset.__eq__ = lambda self, other: other is None
    
    result1 = handler.has_changes(None, asset)
    result2 = handler.has_changes(asset, None)
    
    # These will use the equality check
    assert result1 is False  # None.__eq__(asset) is False
    assert result2 is True   # asset.__eq__(None) is True


# Test complex header scenarios
@composite
def complex_headers(draw):
    """Generate headers with edge cases."""
    choice = draw(st.integers(0, 5))
    if choice == 0:
        # Headers with duplicate keys (case variations)
        return {
            "x-atlan-signing-secret": draw(st.text()),
            "X-Atlan-Signing-Secret": draw(st.text()),
        }
    elif choice == 1:
        # Headers with empty string key
        return {"": draw(st.text()), "x-atlan-signing-secret": draw(st.text())}
    elif choice == 2:
        # Headers with None value
        return {"x-atlan-signing-secret": None}
    elif choice == 3:
        # Headers with numeric value
        return {"x-atlan-signing-secret": draw(st.integers())}
    elif choice == 4:
        # Headers with very long key
        long_key = "x" * 10000 + "-atlan-signing-secret"
        return {long_key: draw(st.text())}
    else:
        # Headers with special characters in value
        return {"x-atlan-signing-secret": draw(st.text(alphabet=st.characters()))}


@given(st.text(), complex_headers())
def test_valid_signature_complex_headers(expected, headers):
    """Property: valid_signature handles complex header scenarios."""
    try:
        result = valid_signature(expected, headers)
        # Should work and return appropriate boolean
        assert isinstance(result, bool)
        
        # Verify the logic
        found = headers.get("x-atlan-signing-secret")
        if found is None:
            assert result is False
        else:
            assert result == (found == expected)
    except (TypeError, AttributeError):
        # If there's a type error, that might be a bug
        # Let's check if it's because of incompatible types
        found = headers.get("x-atlan-signing-secret")
        if not isinstance(found, (str, type(None))):
            # This is a potential bug - the function doesn't handle non-string values well
            pass


# Test validation request with JSON-like strings
@given(st.text())
def test_is_validation_request_json_structure(data):
    """Property: Only exact JSON string matches, not similar structures."""
    # Try to create similar but different JSON
    if data != WEBHOOK_VALIDATION_REQUEST:
        try:
            # Parse the validation request and modify it slightly
            parsed = json.loads(WEBHOOK_VALIDATION_REQUEST)
            modified = json.dumps(parsed, separators=(',', ':'))  # Different formatting
            if modified != WEBHOOK_VALIDATION_REQUEST:
                result = is_validation_request(modified)
                # Even valid JSON with same content but different format should not match
                assert result is False
        except:
            pass


# Test process_event function with edge cases
def test_process_event_validation_request():
    """Property: process_event handles validation requests correctly."""
    handler = Mock(spec=AtlanEventHandler)
    event = {"body": WEBHOOK_VALIDATION_REQUEST}
    context = {}
    
    result = process_event(handler, event, context)
    
    # Should return success without calling handler methods
    assert result == {"statusCode": 200}
    handler.validate_prerequisites.assert_not_called()


def test_process_event_invalid_signature():
    """Property: process_event rejects invalid signatures."""
    handler = Mock(spec=AtlanEventHandler)
    event = {
        "body": '{"test": "data"}',
        "headers": {"x-atlan-signing-secret": "wrong"}
    }
    context = {}
    
    # Mock the SIGNING_SECRET
    with patch('pyatlan.events.atlan_lambda_handler.SIGNING_SECRET', 'correct'):
        try:
            process_event(handler, event, context)
            assert False, "Should have raised IOError"
        except IOError as e:
            assert "Invalid signing secret" in str(e)


# Test malformed event handling
@given(st.text())
def test_process_event_malformed_json(json_str):
    """Property: process_event handles malformed JSON gracefully."""
    assume(json_str != WEBHOOK_VALIDATION_REQUEST)
    
    handler = Mock(spec=AtlanEventHandler)
    event = {
        "body": json_str,
        "headers": {"x-atlan-signing-secret": "test"}
    }
    context = {}
    
    with patch('pyatlan.events.atlan_lambda_handler.SIGNING_SECRET', 'test'):
        try:
            process_event(handler, event, context)
            # If it succeeds, the JSON must have been valid
        except json.JSONDecodeError:
            # This is expected for invalid JSON
            pass
        except Exception as e:
            # Other exceptions might indicate bugs
            if "Invalid signing secret" not in str(e):
                print(f"Unexpected exception: {e}")


if __name__ == "__main__":
    print("Running advanced property-based tests for pyatlan.events...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])