import math
from hypothesis import given, strategies as st, settings, assume
import troposphere.securityhub as sh
from troposphere.validators import boolean, double, integer


# Test validator properties

@given(st.one_of(
    st.just(True), st.just(False),
    st.just(1), st.just(0),
    st.just("1"), st.just("0"),
    st.just("true"), st.just("false"),
    st.just("True"), st.just("False")
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts all documented valid inputs"""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: x.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit() if x else False)
))
def test_double_validator_numeric_inputs(value):
    """Test that double validator accepts numeric values and numeric strings"""
    try:
        float(str(value))
        result = double(value)
        assert result == value
    except (ValueError, OverflowError):
        pass


@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.lstrip('-').isdigit() if x else False)
))
def test_integer_validator_integer_inputs(value):
    """Test that integer validator accepts integers and integer strings"""
    try:
        int(str(value))
        result = integer(value) 
        assert result == value
    except (ValueError, OverflowError):
        pass


# Test round-trip properties for SecurityHub classes

@given(
    linked_regions=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10),
    region_linking_mode=st.sampled_from(['ALL_REGIONS', 'ALL_REGIONS_EXCEPT', 'SPECIFIED_REGIONS']),
    tags=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=256),
        max_size=10
    )
)
def test_aggregator_v2_round_trip(linked_regions, region_linking_mode, tags):
    """Test that AggregatorV2 survives to_dict/from_dict round-trip"""
    obj = sh.AggregatorV2('TestAggregator')
    obj.LinkedRegions = linked_regions
    obj.RegionLinkingMode = region_linking_mode
    if tags:
        obj.Tags = tags
    
    dict_repr = obj.to_dict()
    new_obj = sh.AggregatorV2.from_dict('TestAggregator', dict_repr)
    dict_repr2 = new_obj.to_dict()
    
    assert dict_repr == dict_repr2


@given(
    label=st.sampled_from(['INFORMATIONAL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    normalized=st.integers(min_value=0, max_value=100),
    product=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)
def test_severity_update_round_trip(label, normalized, product):
    """Test that SeverityUpdate survives to_dict/from_dict round-trip"""
    obj = sh.SeverityUpdate()
    if label:
        obj.Label = label
    if normalized is not None:
        obj.Normalized = normalized
    if product is not None:
        obj.Product = product
    
    dict_repr = obj.to_dict()
    new_obj = sh.SeverityUpdate.from_dict('Test', dict_repr)
    dict_repr2 = new_obj.to_dict()
    
    assert dict_repr == dict_repr2


@given(
    text=st.text(min_size=1, max_size=512),
    updated_by=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=256),
        min_size=1,
        max_size=5
    )
)
def test_note_update_round_trip(text, updated_by):
    """Test that NoteUpdate survives to_dict/from_dict round-trip"""
    obj = sh.NoteUpdate()
    obj.Text = text
    obj.UpdatedBy = updated_by
    
    dict_repr = obj.to_dict()
    new_obj = sh.NoteUpdate.from_dict('Test', dict_repr)
    dict_repr2 = new_obj.to_dict()
    
    assert dict_repr == dict_repr2


@given(
    eq_value=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    gte_value=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    lte_value=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
)  
def test_number_filter_round_trip(eq_value, gte_value, lte_value):
    """Test that NumberFilter survives to_dict/from_dict round-trip"""
    obj = sh.NumberFilter()
    
    # Randomly include some fields
    if eq_value is not None:
        obj.Eq = eq_value
    if gte_value is not None:
        obj.Gte = gte_value
    if lte_value is not None:
        obj.Lte = lte_value
    
    dict_repr = obj.to_dict()
    new_obj = sh.NumberFilter.from_dict('Test', dict_repr)
    dict_repr2 = new_obj.to_dict()
    
    assert dict_repr == dict_repr2


@given(
    comparison=st.sampled_from(['EQUALS', 'PREFIX', 'NOT_EQUALS', 'PREFIX_NOT_EQUALS', 'CONTAINS', 'NOT_CONTAINS']),
    value=st.text(min_size=1, max_size=512)
)
def test_string_filter_round_trip(comparison, value):
    """Test that StringFilter survives to_dict/from_dict round-trip"""
    obj = sh.StringFilter()
    obj.Comparison = comparison
    obj.Value = value
    
    dict_repr = obj.to_dict()
    new_obj = sh.StringFilter.from_dict('Test', dict_repr)
    dict_repr2 = new_obj.to_dict()
    
    assert dict_repr == dict_repr2


@given(
    unit=st.sampled_from(['DAYS', 'HOURS', 'MINUTES']),
    value=st.floats(min_value=1, max_value=365, allow_nan=False, allow_infinity=False)
)
def test_date_range_round_trip(unit, value):
    """Test that DateRange survives to_dict/from_dict round-trip"""
    obj = sh.DateRange()
    obj.Unit = unit
    obj.Value = value
    
    dict_repr = obj.to_dict()
    new_obj = sh.DateRange.from_dict('Test', dict_repr)
    dict_repr2 = new_obj.to_dict()
    
    assert dict_repr == dict_repr2


# Test validation of required fields

@given(
    include_regions=st.booleans(),
    include_mode=st.booleans(),
    include_tags=st.booleans()
)
def test_aggregator_v2_required_fields_validation(include_regions, include_mode, include_tags):
    """Test that AggregatorV2 validates required fields correctly"""
    obj = sh.AggregatorV2('TestAggregator')
    
    if include_regions:
        obj.LinkedRegions = ['us-east-1']
    if include_mode:
        obj.RegionLinkingMode = 'ALL_REGIONS'
    if include_tags:
        obj.Tags = {'test': 'value'}
    
    # Should only validate successfully if both required fields are present
    if include_regions and include_mode:
        dict_repr = obj.to_dict()
        assert 'Properties' in dict_repr
        assert dict_repr['Properties']['LinkedRegions'] == ['us-east-1']
        assert dict_repr['Properties']['RegionLinkingMode'] == 'ALL_REGIONS'
    else:
        try:
            obj.to_dict()
            assert False, "Should have raised validation error for missing required fields"
        except Exception as e:
            assert "required" in str(e).lower()


@given(
    include_text=st.booleans(),
    include_updated_by=st.booleans()
)
def test_note_update_required_fields_validation(include_text, include_updated_by):
    """Test that NoteUpdate validates required fields correctly"""
    obj = sh.NoteUpdate()
    
    if include_text:
        obj.Text = "Test note"
    if include_updated_by:
        obj.UpdatedBy = {"user": "testuser"}
    
    # Should only validate successfully if both required fields are present
    if include_text and include_updated_by:
        dict_repr = obj.to_dict()
        assert dict_repr['Text'] == "Test note"
        assert dict_repr['UpdatedBy'] == {"user": "testuser"}
    else:
        try:
            obj.to_dict()
            assert False, "Should have raised validation error for missing required fields"
        except Exception as e:
            assert "required" in str(e).lower()


# Test nested property structures

@given(
    confidence=st.integers(min_value=0, max_value=100),
    criticality=st.integers(min_value=0, max_value=100),
    types=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    verification_state=st.sampled_from(['UNKNOWN', 'TRUE_POSITIVE', 'FALSE_POSITIVE', 'BENIGN_POSITIVE'])
)
def test_automation_rules_finding_fields_update_nested(confidence, criticality, types, verification_state):
    """Test nested properties in AutomationRulesFindingFieldsUpdate"""
    obj = sh.AutomationRulesFindingFieldsUpdate()
    
    if confidence is not None:
        obj.Confidence = confidence
    if criticality is not None:
        obj.Criticality = criticality
    if types:
        obj.Types = types
    if verification_state:
        obj.VerificationState = verification_state
    
    # Add nested Severity object
    severity = sh.SeverityUpdate()
    severity.Label = 'HIGH'
    severity.Normalized = 80
    obj.Severity = severity
    
    # Add nested Note object
    note = sh.NoteUpdate()
    note.Text = "Test note"
    note.UpdatedBy = {"user": "testuser"}
    obj.Note = note
    
    dict_repr = obj.to_dict()
    new_obj = sh.AutomationRulesFindingFieldsUpdate.from_dict('Test', dict_repr)
    dict_repr2 = new_obj.to_dict()
    
    assert dict_repr == dict_repr2
    assert dict_repr2.get('Severity', {}).get('Label') == 'HIGH'
    assert dict_repr2.get('Note', {}).get('Text') == "Test note"


# Test edge cases in validators

@given(st.text())
def test_boolean_validator_invalid_strings(value):
    """Test that boolean validator rejects invalid string inputs"""
    if value not in ["1", "0", "true", "false", "True", "False"]:
        try:
            boolean(value)
            assert False, f"boolean() should have rejected '{value}'"
        except ValueError:
            pass


@given(st.one_of(
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text()),
    st.text().filter(lambda x: not x.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit() if x else True)
))
def test_double_validator_invalid_inputs(value):
    """Test that double validator rejects non-numeric inputs"""
    try:
        float(value) if value is not None else None
    except (ValueError, TypeError):
        try:
            double(value)
            assert False, f"double() should have rejected {value}"
        except (ValueError, TypeError):
            pass


@given(st.one_of(
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text()),
    st.floats(),
    st.text().filter(lambda x: not x.lstrip('-').isdigit() if x else True)
))
def test_integer_validator_invalid_inputs(value):
    """Test that integer validator rejects non-integer inputs"""
    try:
        if isinstance(value, float) and not value.is_integer():
            raise ValueError
        int(value) if value is not None else None
    except (ValueError, TypeError):
        try:
            integer(value)
            assert False, f"integer() should have rejected {value}"
        except (ValueError, TypeError):
            pass