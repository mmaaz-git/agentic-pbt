"""Focused tests on FieldInfo.merge_field_infos for potential bugs."""

from hypothesis import given, strategies as st
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
import annotated_types


# Test metadata preservation in merge
@given(
    num_fields=st.integers(min_value=2, max_value=5),
    add_constraints=st.booleans()
)
def test_merge_metadata_preservation(num_fields: int, add_constraints: bool):
    """Test that metadata is properly preserved/overridden in merge_field_infos."""
    fields = []
    
    for i in range(num_fields):
        kwargs = {}
        metadata = []
        
        if add_constraints and i % 2 == 0:
            # Add some constraints that become metadata
            kwargs['gt'] = float(i)
            kwargs['lt'] = float(i + 10)
        
        if i % 3 == 0:
            kwargs['min_length'] = i
        
        field = FieldInfo.from_field(**kwargs)
        fields.append(field)
    
    # Test sequential merging
    result = fields[0]
    for field in fields[1:]:
        result = FieldInfo.merge_field_infos(result, field)
    
    # The last field's metadata should win
    last_field = fields[-1]
    
    # Check metadata is from last field with metadata
    if add_constraints:
        # Find the last field that had constraints
        for field in reversed(fields):
            if field.metadata:
                assert result.metadata == field.metadata, f"Metadata not preserved correctly"
                break


# Test merging with PydanticUndefined values
@given(
    set_default1=st.booleans(),
    set_default2=st.booleans(),
    set_default3=st.booleans()
)
def test_merge_undefined_handling(set_default1: bool, set_default2: bool, set_default3: bool):
    """Test that PydanticUndefined is handled correctly in merges."""
    kwargs1 = {'default': 1} if set_default1 else {}
    kwargs2 = {'default': 2} if set_default2 else {}
    kwargs3 = {'default': 3} if set_default3 else {}
    
    f1 = FieldInfo(**kwargs1)
    f2 = FieldInfo(**kwargs2)
    f3 = FieldInfo(**kwargs3)
    
    merged = FieldInfo.merge_field_infos(f1, f2, f3)
    
    # The last defined default should win
    if set_default3:
        assert merged.default == 3
    elif set_default2:
        assert merged.default == 2
    elif set_default1:
        assert merged.default == 1
    else:
        assert merged.default is PydanticUndefined


# Test conflicting frozen states
@given(
    frozen_states=st.lists(st.one_of(st.none(), st.booleans()), min_size=2, max_size=5)
)
def test_merge_frozen_conflicts(frozen_states):
    """Test merging FieldInfos with different frozen states."""
    fields = []
    for frozen in frozen_states:
        kwargs = {}
        if frozen is not None:
            kwargs['frozen'] = frozen
        fields.append(FieldInfo(**kwargs))
    
    # Merge all fields
    merged = FieldInfo.merge_field_infos(*fields)
    
    # Find the last non-None frozen state
    expected_frozen = None
    for frozen in reversed(frozen_states):
        if frozen is not None:
            expected_frozen = frozen
            break
    
    assert merged.frozen == expected_frozen, f"Frozen state not correctly merged"


# Test complex merge scenarios with all attributes
@given(
    data=st.data()
)
def test_complex_merge_scenarios(data):
    """Test complex merge scenarios with multiple attributes."""
    # Generate random field configurations
    num_fields = data.draw(st.integers(min_value=2, max_value=4))
    fields = []
    
    for i in range(num_fields):
        kwargs = {}
        
        # Randomly set various attributes
        if data.draw(st.booleans()):
            kwargs['default'] = data.draw(st.integers())
        
        if data.draw(st.booleans()):
            kwargs['title'] = data.draw(st.text(min_size=1, max_size=10))
        
        if data.draw(st.booleans()):
            kwargs['description'] = data.draw(st.text(min_size=1, max_size=20))
        
        if data.draw(st.booleans()):
            kwargs['gt'] = data.draw(st.floats(allow_nan=False, allow_infinity=False))
        
        if data.draw(st.booleans()):
            kwargs['frozen'] = data.draw(st.booleans())
        
        if data.draw(st.booleans()):
            kwargs['exclude'] = data.draw(st.booleans())
        
        field = FieldInfo.from_field(**kwargs)
        fields.append(field)
    
    # Test that merge doesn't raise unexpected errors
    try:
        merged = FieldInfo.merge_field_infos(*fields)
        
        # Verify basic invariant: merged field should be a valid FieldInfo
        assert isinstance(merged, FieldInfo)
        
        # The merged field should be usable
        _ = merged.is_required()
        _ = merged.get_default()
        
    except Exception as e:
        # Merging should not raise exceptions for valid FieldInfos
        assert False, f"Unexpected exception during merge: {e}"


# Test merge with custom json_schema_extra
@given(
    num_fields=st.integers(min_value=2, max_value=4)
)
def test_merge_json_schema_extra(num_fields: int):
    """Test that json_schema_extra is properly handled in merges."""
    fields = []
    
    for i in range(num_fields):
        kwargs = {}
        if i % 2 == 0:
            # Add json_schema_extra as a dict
            kwargs['json_schema_extra'] = {'custom_field': f'value_{i}', 'index': i}
        field = FieldInfo.from_field(**kwargs)
        fields.append(field)
    
    merged = FieldInfo.merge_field_infos(*fields)
    
    # The last field with json_schema_extra should win
    for field in reversed(fields):
        if field.json_schema_extra is not None:
            assert merged.json_schema_extra == field.json_schema_extra
            break
    else:
        assert merged.json_schema_extra is None