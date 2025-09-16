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
    ValidationError
)


# Strategy for valid JSON-serializable data
json_strategy = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(min_size=0, max_size=100),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            children,
            max_size=10
        )
    ),
    max_leaves=50
)


@given(json_strategy)
@hyp_settings(max_examples=200)
def test_jsonfield_roundtrip(data):
    """JSONField should preserve data through clean operation"""
    field = JSONField()
    
    # Convert to JSON string as would come from form input
    json_str = json.dumps(data)
    
    # Clean the data
    cleaned = field.clean(json_str)
    
    # The cleaned data should equal original data
    assert cleaned == data, f"Round-trip failed: {data} != {cleaned}"


@given(
    st.integers(min_value=-1000000, max_value=1000000),
    st.integers(min_value=-1000000, max_value=1000000)
)
def test_integerfield_idempotence(min_val, max_val):
    """IntegerField.clean should be idempotent - cleaning twice gives same result"""
    assume(min_val <= max_val)
    
    field = IntegerField(min_value=min_val, max_value=max_val)
    
    # Test with values in valid range
    test_value = (min_val + max_val) // 2
    
    # First clean
    cleaned_once = field.clean(test_value)
    
    # Second clean
    cleaned_twice = field.clean(cleaned_once)
    
    assert cleaned_once == cleaned_twice
    assert type(cleaned_once) == type(cleaned_twice) == int


@given(st.text(min_size=0, max_size=50))
def test_charfield_clean_preserves_valid_strings(text):
    """CharField should preserve strings within length bounds"""
    field = CharField(min_length=0, max_length=100)
    
    if text == '':
        # CharField raises ValidationError for empty string by default (required=True)
        with pytest.raises(ValidationError):
            field.clean(text)
    else:
        cleaned = field.clean(text)
        assert cleaned == text
        assert len(cleaned) == len(text)


@given(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=5))
def test_integerfield_string_coercion(values):
    """IntegerField should correctly coerce string representations to integers"""
    field = IntegerField()
    
    for value in values:
        # Test string representation
        str_value = str(value)
        cleaned_from_str = field.clean(str_value)
        cleaned_from_int = field.clean(value)
        
        assert cleaned_from_str == cleaned_from_int == value
        assert type(cleaned_from_str) == type(cleaned_from_int) == int


@given(st.lists(st.booleans(), min_size=1, max_size=10))
def test_all_valid_confluence(validity_list):
    """all_valid should return True iff all formsets are valid"""
    
    class SimpleForm(Form):
        value = IntegerField(min_value=0, max_value=100)
    
    formsets = []
    
    for should_be_valid in validity_list:
        FormSet = formset_factory(SimpleForm, extra=0)
        
        if should_be_valid:
            # Create valid formset
            data = {
                'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
                'form-0-value': '50',
            }
        else:
            # Create invalid formset  
            data = {
                'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
                'form-0-value': '200',  # Out of range
            }
        
        formset = FormSet(data)
        formsets.append(formset)
    
    all_are_valid = all_valid(formsets)
    individual_validity = all(fs.is_valid() for fs in formsets)
    
    assert all_are_valid == individual_validity


@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)
)
def test_floatfield_idempotence(value):
    """FloatField.clean should be idempotent"""
    field = FloatField()
    
    # Clean once
    cleaned_once = field.clean(value)
    
    # Clean twice
    cleaned_twice = field.clean(cleaned_once)
    
    assert cleaned_once == cleaned_twice
    assert type(cleaned_once) == type(cleaned_twice) == float


@given(st.text(min_size=1, max_size=100))
def test_charfield_strip_behavior(text):
    """CharField with strip=True should be idempotent after first strip"""
    field = CharField(strip=True)
    
    cleaned_once = field.clean(text)
    cleaned_twice = field.clean(cleaned_once)
    
    # After stripping once, further cleans should not change the value
    assert cleaned_once == cleaned_twice
    
    # The cleaned value should be stripped
    assert cleaned_once == text.strip()


@given(
    st.one_of(
        st.decimals(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        st.integers(min_value=-1000000, max_value=1000000)
    )
)
def test_decimalfield_numeric_preservation(value):
    """DecimalField should preserve numeric values correctly"""
    field = DecimalField()
    
    # Convert to string as form input would be
    if isinstance(value, decimal.Decimal):
        str_value = str(value)
    else:
        str_value = str(value)
    
    cleaned = field.clean(str_value)
    
    # Result should be a Decimal
    assert isinstance(cleaned, decimal.Decimal)
    
    # Value should be preserved (accounting for precision)
    if isinstance(value, (int, decimal.Decimal)):
        assert cleaned == decimal.Decimal(str(value))
    else:  # float
        # For floats, check they're close due to precision issues
        assert abs(float(cleaned) - value) < 1e-10


@given(st.booleans())
def test_booleanfield_false_string_handling(required):
    """BooleanField should handle 'False' string correctly"""
    field = BooleanField(required=required)
    
    # Test various false-like values
    false_values = ['False', 'false', '0', 0, False]
    
    for false_val in false_values:
        if required and false_val in [False, 'False', 'false', '0', 0]:
            # Required BooleanField treats these as empty/false
            with pytest.raises(ValidationError):
                field.clean(false_val)
        else:
            cleaned = field.clean(false_val)
            assert isinstance(cleaned, bool)