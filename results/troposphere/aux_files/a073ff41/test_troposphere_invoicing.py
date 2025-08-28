#!/usr/bin/env python3
"""Property-based tests for troposphere.invoicing module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import json
import troposphere.invoicing as invoicing
from troposphere.validators import boolean


# Strategy for valid AWS resource titles (ASCII alphanumeric only)
valid_titles = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=255)

# Strategy for invalid titles (containing non-alphanumeric)
invalid_titles = st.text(min_size=1, max_size=255).filter(lambda x: not x.replace(' ', '').replace('-', '').replace('_', '').replace('.', '').isalnum() and x != '')

# Strategy for strings
text_strategy = st.text(min_size=0, max_size=1000)

# Strategy for resource tags
resource_tag_strategy = st.builds(
    invoicing.ResourceTag,
    Key=text_strategy,
    Value=text_strategy
)

# Strategy for rules
rule_strategy = st.builds(
    invoicing.Rule,
    LinkedAccounts=st.lists(text_strategy, min_size=1, max_size=10)
)


@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_accepts_valid_values(value):
    """Test that boolean validator accepts documented valid values."""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_boolean_validator_rejects_invalid_values(value):
    """Test that boolean validator rejects non-boolean values."""
    try:
        boolean(value)
        assert False, f"boolean() should have raised ValueError for {value}"
    except ValueError:
        pass  # Expected


@given(valid_titles)
def test_valid_title_acceptance(title):
    """Test that valid alphanumeric titles are accepted."""
    obj = invoicing.InvoiceUnit(
        title,
        InvoiceReceiver="arn:aws:iam::123456789012:root",
        Name="TestUnit",
        Rule=invoicing.Rule(LinkedAccounts=["123456789012"])
    )
    obj.validate_title()  # Should not raise


@given(invalid_titles)
def test_invalid_title_rejection(title):
    """Test that non-alphanumeric titles are rejected."""
    assume(title)  # Skip empty strings
    assume(not all(c.isalnum() for c in title))  # Ensure it's actually invalid
    
    try:
        obj = invoicing.InvoiceUnit(
            title,
            InvoiceReceiver="arn:aws:iam::123456789012:root", 
            Name="TestUnit",
            Rule=invoicing.Rule(LinkedAccounts=["123456789012"])
        )
        assert False, f"InvoiceUnit should have rejected title: {repr(title)}"
    except ValueError as e:
        assert "not alphanumeric" in str(e)


@given(
    valid_titles,
    text_strategy,  # description
    text_strategy,  # invoice_receiver
    text_strategy,  # name
    st.lists(resource_tag_strategy, min_size=0, max_size=5),
    rule_strategy,
    st.one_of(st.none(), st.sampled_from([True, False, 0, 1, "true", "false"]))
)
def test_invoice_unit_round_trip(title, description, invoice_receiver, name, resource_tags, rule, tax_inheritance):
    """Test that InvoiceUnit survives round-trip serialization."""
    kwargs = {
        "InvoiceReceiver": invoice_receiver,
        "Name": name,
        "Rule": rule
    }
    if description:
        kwargs["Description"] = description
    if resource_tags:
        kwargs["ResourceTags"] = resource_tags
    if tax_inheritance is not None:
        kwargs["TaxInheritanceDisabled"] = tax_inheritance
    
    # Create the object
    original = invoicing.InvoiceUnit(title, **kwargs)
    
    # Convert to dict
    as_dict = original.to_dict()
    
    # Verify resource type is preserved
    assert as_dict["Type"] == "AWS::Invoicing::InvoiceUnit"
    
    # Convert back from dict
    props = as_dict.get("Properties", {})
    reconstructed = invoicing.InvoiceUnit.from_dict(title, props)
    
    # Compare JSON representations (this is how __eq__ works)
    assert original.to_json(validation=False) == reconstructed.to_json(validation=False)


@given(valid_titles)
def test_required_properties_validation(title):
    """Test that missing required properties cause validation errors."""
    # Create InvoiceUnit without required properties
    obj = invoicing.InvoiceUnit(title)
    
    # Should raise when validating because required props are missing
    try:
        obj.to_dict(validation=True)
        assert False, "Should have raised ValueError for missing required properties"
    except ValueError as e:
        # Should mention one of the required properties
        assert any(prop in str(e) for prop in ["InvoiceReceiver", "Name", "Rule"])


@given(
    valid_titles,
    st.lists(st.integers(), min_size=1),  # Invalid type for InvoiceReceiver
)
def test_type_validation_for_string_properties(title, invalid_value):
    """Test that setting wrong types for string properties raises TypeError."""
    try:
        invoicing.InvoiceUnit(
            title,
            InvoiceReceiver=invalid_value,  # Should be string, not list
            Name="TestUnit",
            Rule=invoicing.Rule(LinkedAccounts=["123456789012"])
        )
        assert False, f"Should have raised TypeError for invalid InvoiceReceiver type"
    except (TypeError, AttributeError):
        pass  # Expected


@given(
    valid_titles,
    text_strategy
)
def test_rule_linked_accounts_is_list(title, single_account):
    """Test that Rule.LinkedAccounts must be a list."""
    # Test with valid list
    rule = invoicing.Rule(LinkedAccounts=[single_account])
    assert rule.LinkedAccounts == [single_account]
    
    # Test with invalid non-list
    try:
        invoicing.Rule(LinkedAccounts=single_account)  # Should be list
        assert False, "Rule should require LinkedAccounts to be a list"
    except (TypeError, ValueError):
        pass  # Expected


@given(valid_titles)
def test_resource_type_invariant(title):
    """Test that InvoiceUnit always has correct resource type."""
    obj = invoicing.InvoiceUnit(
        title,
        InvoiceReceiver="arn:aws:iam::123456789012:root",
        Name="TestUnit", 
        Rule=invoicing.Rule(LinkedAccounts=["123456789012"])
    )
    
    # Check internal resource type
    assert obj.resource_type == "AWS::Invoicing::InvoiceUnit"
    
    # Check it appears in serialized form
    as_dict = obj.to_dict()
    assert as_dict.get("Type") == "AWS::Invoicing::InvoiceUnit"