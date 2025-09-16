#!/usr/bin/env python3
"""Property-based tests for pyatlan.events module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
from hypothesis.strategies import composite
from unittest.mock import Mock, MagicMock
import json

# Import the modules we're testing
from pyatlan.events.atlan_event_handler import (
    is_validation_request,
    valid_signature,
    has_description,
    has_owner,
    has_lineage,
    AtlanEventHandler,
    WEBHOOK_VALIDATION_REQUEST
)
from pyatlan.model.assets import Asset, Catalog
from pyatlan.model.events import AtlanEvent, AtlanEventPayload


# Strategy for generating header dictionaries
@composite
def headers_strategy(draw):
    """Generate dictionary of headers with optional x-atlan-signing-secret."""
    headers = {}
    num_headers = draw(st.integers(min_value=0, max_value=10))
    for _ in range(num_headers):
        key = draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip() != ""))
        value = draw(st.text(min_size=0, max_size=100))
        headers[key] = value
    return headers


@composite 
def headers_with_signature(draw, signature):
    """Generate headers that include the x-atlan-signing-secret."""
    headers = draw(headers_strategy())
    headers["x-atlan-signing-secret"] = signature
    return headers


# Test 1: is_validation_request function
@given(st.text())
def test_is_validation_request_only_matches_exact_string(data):
    """Property: is_validation_request returns True only for the exact validation string."""
    result = is_validation_request(data)
    expected = (data == WEBHOOK_VALIDATION_REQUEST)
    assert result == expected, f"Expected {expected} for data={repr(data)}, got {result}"


@given(st.text())
def test_is_validation_request_idempotent(data):
    """Property: is_validation_request is idempotent - same input always produces same output."""
    result1 = is_validation_request(data)
    result2 = is_validation_request(data)
    assert result1 == result2


# Test 2: valid_signature function
@given(st.text(), st.one_of(st.none(), headers_strategy()))
def test_valid_signature_none_or_missing_header(expected, headers):
    """Property: valid_signature returns False when headers are None or don't contain the key."""
    if headers is not None and "x-atlan-signing-secret" in headers:
        # Skip this case as it's tested elsewhere
        assume(False)
    result = valid_signature(expected, headers)
    assert result is False


@given(st.text())
def test_valid_signature_with_matching_header(signature):
    """Property: valid_signature returns True when header matches expected signature."""
    headers = {"x-atlan-signing-secret": signature}
    result = valid_signature(signature, headers)
    assert result is True


@given(st.text(), st.text())
def test_valid_signature_with_different_signatures(expected, actual):
    """Property: valid_signature returns False when signatures don't match."""
    assume(expected != actual)
    headers = {"x-atlan-signing-secret": actual}
    result = valid_signature(expected, headers)
    assert result is False


@given(st.text(), headers_strategy())
def test_valid_signature_correctness(expected, headers):
    """Property: valid_signature(s, h) == (h.get('x-atlan-signing-secret') == s)."""
    result = valid_signature(expected, headers)
    expected_result = headers.get("x-atlan-signing-secret") == expected
    assert result == expected_result


# Test 3: has_description function
@composite
def asset_with_descriptions(draw):
    """Generate an Asset with optional descriptions."""
    asset = Mock(spec=Asset)
    asset.user_description = draw(st.one_of(st.none(), st.text()))
    asset.description = draw(st.one_of(st.none(), st.text()))
    return asset


@given(asset_with_descriptions())
def test_has_description_correctness(asset):
    """Property: has_description returns True iff user_description or description is non-empty."""
    result = has_description(asset)
    desc = asset.user_description or asset.description
    expected = desc is not None and desc != ""
    assert result == expected


@given(asset_with_descriptions())
def test_has_description_idempotent(asset):
    """Property: has_description is idempotent."""
    result1 = has_description(asset)
    result2 = has_description(asset)
    assert result1 == result2


# Test 4: has_owner function
@composite
def asset_with_owners(draw):
    """Generate an Asset with optional owners."""
    asset = Mock(spec=Asset)
    asset.owner_users = draw(st.one_of(st.none(), st.lists(st.text(), min_size=1)))
    asset.owner_groups = draw(st.one_of(st.none(), st.lists(st.text(), min_size=1)))
    return asset


@given(asset_with_owners())
def test_has_owner_correctness(asset):
    """Property: has_owner returns True iff owner_users or owner_groups is not None."""
    result = has_owner(asset)
    expected = (asset.owner_users is not None) or (asset.owner_groups is not None)
    assert result == expected


@given(asset_with_owners())
def test_has_owner_idempotent(asset):
    """Property: has_owner is idempotent."""
    result1 = has_owner(asset)
    result2 = has_owner(asset)
    assert result1 == result2


# Test 5: has_lineage function
@composite
def catalog_asset_with_lineage(draw):
    """Generate a Catalog asset with optional lineage."""
    asset = Mock(spec=Catalog)
    asset.input_to_processes = draw(st.one_of(st.none(), st.lists(st.text(), min_size=1)))
    asset.output_from_processes = draw(st.one_of(st.none(), st.lists(st.text(), min_size=1)))
    asset.has_lineage = draw(st.booleans())  # Also set this for completeness
    return asset


@composite
def non_catalog_asset_with_lineage(draw):
    """Generate a non-Catalog asset with has_lineage flag."""
    asset = Mock(spec=Asset)
    asset.has_lineage = draw(st.booleans())
    return asset


@given(catalog_asset_with_lineage())
def test_has_lineage_catalog_correctness(asset):
    """Property: For Catalog assets, has_lineage checks input/output processes."""
    result = has_lineage(asset)
    expected = (asset.input_to_processes is not None) or (asset.output_from_processes is not None)
    assert result == expected


@given(non_catalog_asset_with_lineage())
def test_has_lineage_non_catalog_correctness(asset):
    """Property: For non-Catalog assets, has_lineage returns bool(asset.has_lineage)."""
    result = has_lineage(asset)
    expected = bool(asset.has_lineage)
    assert result == expected


@given(st.one_of(catalog_asset_with_lineage(), non_catalog_asset_with_lineage()))
def test_has_lineage_idempotent(asset):
    """Property: has_lineage is idempotent."""
    result1 = has_lineage(asset)
    result2 = has_lineage(asset)
    assert result1 == result2


# Test 6: AtlanEventHandler.validate_prerequisites
@composite
def valid_event(draw):
    """Generate a valid AtlanEvent with proper structure."""
    asset = Mock(spec=Asset)
    payload = Mock(spec=AtlanEventPayload)
    payload.asset = asset
    event = Mock(spec=AtlanEvent)
    event.payload = payload
    return event


@composite
def invalid_event(draw):
    """Generate various invalid event structures."""
    choice = draw(st.integers(min_value=0, max_value=3))
    if choice == 0:
        # None event
        return None
    elif choice == 1:
        # Event without payload
        event = Mock(spec=AtlanEvent)
        event.payload = None
        return event
    elif choice == 2:
        # Event with non-AtlanEventPayload payload
        event = Mock(spec=AtlanEvent)
        event.payload = "not a payload"
        return event
    else:
        # Event with payload but no asset
        payload = Mock(spec=AtlanEventPayload)
        payload.asset = None
        event = Mock(spec=AtlanEvent)
        event.payload = payload
        return event


@given(valid_event())
def test_validate_prerequisites_accepts_valid_events(event):
    """Property: validate_prerequisites returns True for properly structured events."""
    client = Mock()
    handler = AtlanEventHandler(client)
    result = handler.validate_prerequisites(event)
    assert result is True


@given(invalid_event())
def test_validate_prerequisites_rejects_invalid_events(event):
    """Property: validate_prerequisites returns False for improperly structured events."""
    client = Mock()
    handler = AtlanEventHandler(client)
    result = handler.validate_prerequisites(event)
    assert result is False


@given(st.one_of(valid_event(), invalid_event()))
def test_validate_prerequisites_idempotent(event):
    """Property: validate_prerequisites is idempotent."""
    client = Mock()
    handler = AtlanEventHandler(client)
    result1 = handler.validate_prerequisites(event)
    result2 = handler.validate_prerequisites(event)
    assert result1 == result2


# Test 7: Edge cases with empty strings
@given(st.sampled_from(["", " ", "  ", "\t", "\n", "\r\n"]))
def test_is_validation_request_whitespace(data):
    """Property: Whitespace strings don't match validation request."""
    result = is_validation_request(data)
    assert result is False


@given(st.text())
def test_valid_signature_empty_expected(actual):
    """Property: Empty expected signature only matches empty actual signature."""
    headers = {"x-atlan-signing-secret": actual}
    result = valid_signature("", headers)
    assert result == (actual == "")


# Test 8: Round-trip property for validation request constant
def test_validation_request_constant_round_trip():
    """Property: The validation request constant matches itself."""
    assert is_validation_request(WEBHOOK_VALIDATION_REQUEST) is True
    assert is_validation_request(json.dumps(json.loads(WEBHOOK_VALIDATION_REQUEST))) is True


# Test 9: has_changes method default implementation
@composite
def mock_assets(draw):
    """Generate two mock assets for comparison."""
    asset1 = Mock(spec=Asset)
    asset2 = Mock(spec=Asset)
    # Make them equal or not based on random choice
    are_equal = draw(st.booleans())
    if are_equal:
        asset1.__eq__ = lambda self, other: True
        asset2.__eq__ = lambda self, other: True
    else:
        asset1.__eq__ = lambda self, other: False
        asset2.__eq__ = lambda self, other: False
    return asset1, asset2


@given(mock_assets())
def test_has_changes_uses_equality(assets):
    """Property: Default has_changes implementation uses equality check."""
    current, modified = assets
    client = Mock()
    handler = AtlanEventHandler(client)
    result = handler.has_changes(current, modified)
    # The default implementation returns current == modified
    # So if they're equal, there are no changes (returns False)
    expected = (current == modified)
    assert result == expected


if __name__ == "__main__":
    print("Running property-based tests for pyatlan.events module...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])