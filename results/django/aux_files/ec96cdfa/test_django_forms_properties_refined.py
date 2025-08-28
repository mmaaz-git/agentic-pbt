import django
from django.conf import settings
import json
import decimal
from hypothesis import given, strategies as st, assume, settings as hyp_settings
import pytest

# Configure Django
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
        FORMS_URLFIELD_ASSUME_HTTPS=True,
    )
    django.setup()

from django.forms import (
    CharField, IntegerField, FloatField, DecimalField,
    JSONField, EmailField, URLField, BooleanField,
    Form, BaseFormSet, formset_factory, all_valid,
    ValidationError, Field
)


# Strategy for valid JSON-serializable data (excluding None for required field)
json_strategy = st.recursive(
    st.one_of(
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(min_size=0, max_size=100).filter(lambda x: '\x00' not in x),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20).filter(lambda x: '\x00' not in x),
            children,
            max_size=10
        )
    ),
    max_leaves=50
)


@given(json_strategy)
@hyp_settings(max_examples=200)
def test_jsonfield_roundtrip_non_null(data):
    """JSONField with required=False should preserve data through clean operation"""
    field = JSONField(required=False)
    
    # Convert to JSON string as would come from form input
    json_str = json.dumps(data)
    
    # Clean the data
    cleaned = field.clean(json_str)
    
    # The cleaned data should equal original data
    assert cleaned == data, f"Round-trip failed: {data} != {cleaned}"


@given(json_strategy)
@hyp_settings(max_examples=200) 
def test_jsonfield_double_encoding_bug(data):
    """JSONField should handle already-parsed data correctly"""
    field = JSONField(required=False)
    
    # First, pass the actual Python object (not JSON string)
    # This mimics what might happen if data is passed incorrectly
    try:
        cleaned = field.clean(data)
        # If it accepts Python objects directly, it should preserve them
        assert cleaned == data
    except (ValidationError, TypeError):
        # If it only accepts strings, that's fine
        pass


@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)
)
def test_floatfield_boundary_precision(min_val, max_val):
    """FloatField with min/max should handle boundary values correctly"""
    assume(min_val <= max_val)
    
    field = FloatField(min_value=min_val, max_value=max_val)
    
    # Test exact boundary values
    try:
        cleaned_min = field.clean(min_val)
        assert cleaned_min == min_val
    except ValidationError:
        # Should not raise for exact min value
        assert False, f"FloatField rejected its own min_value: {min_val}"
    
    try:
        cleaned_max = field.clean(max_val)
        assert cleaned_max == max_val
    except ValidationError:
        # Should not raise for exact max value
        assert False, f"FloatField rejected its own max_value: {max_val}"


@given(st.text(min_size=1, max_size=100).filter(lambda x: '\x00' not in x))
def test_charfield_whitespace_edge_cases(text):
    """CharField with strip=False should preserve all whitespace correctly"""
    field = CharField(strip=False, required=False)
    
    # Whitespace-only strings should be preserved when strip=False
    cleaned = field.clean(text)
    assert cleaned == text
    
    # Length should be preserved exactly
    assert len(cleaned) == len(text)


@given(st.lists(
    st.tuples(
        st.text(min_size=1, max_size=20).filter(lambda x: '\x00' not in x),
        st.one_of(
            st.integers(min_value=-1000, max_value=1000),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=50).filter(lambda x: '\x00' not in x)
        )
    ),
    min_size=1,
    max_size=5
))
def test_form_data_preservation(field_data):
    """Form should preserve field data through validation cycle"""
    
    class DynamicForm(Form):
        pass
    
    # Add fields dynamically
    for i, (name, value) in enumerate(field_data):
        if isinstance(value, int):
            field = IntegerField(required=False)
        elif isinstance(value, float):
            field = FloatField(required=False)
        else:
            field = CharField(required=False)
        
        setattr(DynamicForm, f'field_{i}', field)
    
    # Create form with data
    form_data = {f'field_{i}': str(value) for i, (_, value) in enumerate(field_data)}
    form = DynamicForm(data=form_data)
    
    # Validate
    is_valid = form.is_valid()
    
    if is_valid:
        # Check that cleaned_data preserves values correctly
        for i, (_, original_value) in enumerate(field_data):
            cleaned = form.cleaned_data.get(f'field_{i}')
            
            if isinstance(original_value, str):
                assert cleaned == original_value
            elif isinstance(original_value, (int, float)):
                # Numeric values should be converted from string correctly
                if isinstance(form.fields[f'field_{i}'], IntegerField):
                    assert cleaned == int(original_value)
                elif isinstance(form.fields[f'field_{i}'], FloatField):
                    assert abs(cleaned - float(original_value)) < 1e-10


@given(
    st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=10)
)
def test_formset_management_form_manipulation(values):
    """FormSet should handle management form data correctly"""
    
    class SimpleForm(Form):
        value = IntegerField()
    
    FormSet = formset_factory(SimpleForm, extra=0, can_delete=True)
    
    # Create formset data
    data = {
        'form-TOTAL_FORMS': str(len(values)),
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': str(max(1000, len(values))),
    }
    
    for i, val in enumerate(values):
        data[f'form-{i}-value'] = str(val)
        data[f'form-{i}-DELETE'] = ''
    
    formset = FormSet(data)
    
    if formset.is_valid():
        # Check that all non-deleted forms have correct data
        assert len(formset.cleaned_data) == len(values)
        
        for i, form_data in enumerate(formset.cleaned_data):
            if not form_data.get('DELETE', False):
                assert form_data['value'] == values[i]


@given(
    st.decimals(
        min_value=decimal.Decimal('-1e10'),
        max_value=decimal.Decimal('1e10'),
        allow_nan=False,
        allow_infinity=False
    ),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=1, max_value=10)
)
def test_decimalfield_precision_settings(value, max_digits, decimal_places):
    """DecimalField should respect max_digits and decimal_places"""
    assume(max_digits >= decimal_places)
    
    field = DecimalField(max_digits=max_digits, decimal_places=decimal_places)
    
    # Convert value to string with appropriate precision
    value_str = str(value)
    
    try:
        cleaned = field.clean(value_str)
        
        # Check that the cleaned value respects decimal_places
        if '.' in str(cleaned):
            _, dec_part = str(cleaned).split('.')
            assert len(dec_part) <= decimal_places
        
        # Check total digits
        clean_str = str(cleaned).replace('-', '').replace('.', '')
        assert len(clean_str) <= max_digits
        
    except ValidationError:
        # It's ok to reject values that don't fit the constraints
        pass


@given(st.integers())
def test_integerfield_string_number_with_whitespace(value):
    """IntegerField should handle string numbers with whitespace"""
    field = IntegerField(required=False)
    
    # Test with various whitespace
    test_cases = [
        f' {value}',
        f'{value} ',
        f' {value} ',
        f'\t{value}\n',
        f'  {value}  ',
    ]
    
    for test_str in test_cases:
        cleaned = field.clean(test_str)
        assert cleaned == value, f"Failed to parse '{test_str}' as {value}"


@given(st.booleans())
def test_booleanfield_string_representations(value):
    """BooleanField should handle various string representations consistently"""
    field = BooleanField(required=False)
    
    if value:
        # True representations
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'on']
        for true_str in true_values:
            cleaned = field.clean(true_str)
            assert cleaned is True, f"'{true_str}' should be True"
    else:
        # False representations - BooleanField treats many as False/empty
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'off']
        for false_str in false_values:
            cleaned = field.clean(false_str)
            # BooleanField with required=False accepts these as False
            assert cleaned is False, f"'{false_str}' should be False"


@given(
    st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        min_size=1,
        max_size=100
    )
)
def test_field_clean_consistency_across_instances(values):
    """Multiple instances of the same field type should behave consistently"""
    
    # Create multiple field instances with same config
    fields = [FloatField(min_value=-1e6, max_value=1e6) for _ in range(3)]
    
    for value in values:
        results = []
        for field in fields:
            cleaned = field.clean(value)
            results.append(cleaned)
        
        # All fields should produce the same result
        assert all(r == results[0] for r in results), \
            f"Inconsistent results across field instances: {results}"