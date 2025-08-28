import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import awkward.forms as forms
from hypothesis import given, strategies as st, settings, assume

# Strategy for generating valid primitive types
primitives = st.sampled_from([
    "bool", "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64",
    "float16", "float32", "float64", "complex64", "complex128"
])

# Strategy for generating valid index types for forms
index_types = st.sampled_from(["i8", "u8", "i32", "u32", "i64"])

# Strategy for generating parameters (metadata)
@st.composite
def parameters_strategy(draw):
    """Generate valid parameters dict or None"""
    if draw(st.booleans()):
        return None
    # Generate small dict with string keys/values
    keys = draw(st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=3))
    vals = draw(st.lists(st.text(min_size=0, max_size=20), min_size=len(keys), max_size=len(keys)))
    return dict(zip(keys, vals)) if keys else {}

# Strategy for generating form_keys
form_keys = st.one_of(st.none(), st.text(min_size=1, max_size=50))

# Recursive strategy for generating Form objects
@st.composite
def form_strategy(draw, max_depth=3):
    """Generate arbitrary Form objects"""
    if max_depth == 0:
        # Base case: generate simple forms
        form_type = draw(st.sampled_from(["numpy", "empty"]))
        
        if form_type == "numpy":
            params = draw(parameters_strategy())
            key = draw(form_keys)
            return forms.NumpyForm(
                primitive=draw(primitives),
                parameters=params,
                form_key=key
            )
        else:  # empty
            # EmptyForm cannot have parameters!
            key = draw(form_keys)
            return forms.EmptyForm(form_key=key)
    
    # Recursive case: can generate any form type
    form_type = draw(st.sampled_from([
        "numpy", "empty", "regular", "listoffset", "list", "record", "indexed", 
        "indexedoption", "unmasked", "bytemasked", "bitmasked", "union"
    ]))
    
    params = draw(parameters_strategy())
    key = draw(form_keys)
    
    if form_type == "numpy":
        return forms.NumpyForm(
            primitive=draw(primitives),
            parameters=params,
            form_key=key
        )
    elif form_type == "empty":
        # EmptyForm cannot have parameters!
        return forms.EmptyForm(form_key=key)
    elif form_type == "regular":
        return forms.RegularForm(
            content=draw(form_strategy(max_depth=max_depth-1)),
            size=draw(st.integers(min_value=0, max_value=100)),
            parameters=params,
            form_key=key
        )
    elif form_type == "listoffset":
        return forms.ListOffsetForm(
            offsets=draw(index_types),
            content=draw(form_strategy(max_depth=max_depth-1)),
            parameters=params,
            form_key=key
        )
    elif form_type == "list":
        idx_type = draw(index_types)
        return forms.ListForm(
            starts=idx_type,
            stops=idx_type,
            content=draw(form_strategy(max_depth=max_depth-1)),
            parameters=params,
            form_key=key
        )
    elif form_type == "record":
        num_fields = draw(st.integers(min_value=0, max_value=3))
        contents = [draw(form_strategy(max_depth=max_depth-1)) for _ in range(num_fields)]
        # Fields can be None (tuple) or list of strings (named record)
        if draw(st.booleans()):
            fields = None  # tuple-like record
        else:
            fields = [f"field{i}" for i in range(num_fields)]
        return forms.RecordForm(
            contents=contents,
            fields=fields,
            parameters=params,
            form_key=key
        )
    elif form_type == "indexed":
        return forms.IndexedForm(
            index=draw(index_types),
            content=draw(form_strategy(max_depth=max_depth-1)),
            parameters=params,
            form_key=key
        )
    elif form_type == "indexedoption":
        return forms.IndexedOptionForm(
            index=draw(index_types),
            content=draw(form_strategy(max_depth=max_depth-1)),
            parameters=params,
            form_key=key
        )
    elif form_type == "unmasked":
        return forms.UnmaskedForm(
            content=draw(form_strategy(max_depth=max_depth-1)),
            parameters=params,
            form_key=key
        )
    elif form_type == "bytemasked":
        return forms.ByteMaskedForm(
            mask=draw(index_types),
            content=draw(form_strategy(max_depth=max_depth-1)),
            valid_when=draw(st.booleans()),
            parameters=params,
            form_key=key
        )
    elif form_type == "bitmasked":
        return forms.BitMaskedForm(
            mask=draw(index_types),
            content=draw(form_strategy(max_depth=max_depth-1)),
            valid_when=draw(st.booleans()),
            lsb_order=draw(st.booleans()),
            parameters=params,
            form_key=key
        )
    else:  # union
        num_contents = draw(st.integers(min_value=1, max_value=3))
        contents = [draw(form_strategy(max_depth=max_depth-1)) for _ in range(num_contents)]
        return forms.UnionForm(
            tags=draw(index_types),
            index=draw(index_types),
            contents=contents,
            parameters=params,
            form_key=key
        )


# Test 1: Round-trip property for to_dict/from_dict
@given(form_strategy())
@settings(max_examples=200)
def test_form_dict_roundtrip(form):
    """Test that from_dict(form.to_dict()) equals the original form"""
    # Convert form to dict
    form_dict = form.to_dict(verbose=True)
    
    # Parse it back
    reconstructed = forms.from_dict(form_dict)
    
    # They should be equal
    assert reconstructed.is_equal_to(form, all_parameters=True, form_key=True), \
        f"Round-trip failed for {type(form).__name__}"


# Test 2: Round-trip property for to_json/from_json
@given(form_strategy())
@settings(max_examples=200)
def test_form_json_roundtrip(form):
    """Test that from_json(form.to_json()) equals the original form"""
    # Convert form to JSON
    form_json = form.to_json()
    
    # Parse it back
    reconstructed = forms.from_json(form_json)
    
    # They should be equal
    assert reconstructed.is_equal_to(form, all_parameters=True, form_key=True), \
        f"JSON round-trip failed for {type(form).__name__}"


# Test 3: Form equality is reflexive
@given(form_strategy())
def test_form_equality_reflexive(form):
    """Test that a form equals itself"""
    assert form.is_equal_to(form, all_parameters=True, form_key=True)
    assert form == form


# Test 4: to_dict produces valid JSON-serializable dicts
@given(form_strategy())
def test_form_to_dict_is_json_serializable(form):
    """Test that to_dict produces JSON-serializable output"""
    form_dict = form.to_dict(verbose=True)
    # This should not raise an exception
    json_str = json.dumps(form_dict)
    # And we should be able to parse it back
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)


# Test 5: from_dict/from_json consistency
@given(form_strategy())
def test_from_dict_json_consistency(form):
    """Test that from_dict and from_json produce consistent results"""
    form_dict = form.to_dict(verbose=True)
    form_json = json.dumps(form_dict)
    
    from_dict_form = forms.from_dict(form_dict)
    from_json_form = forms.from_json(form_json)
    
    assert from_dict_form.is_equal_to(from_json_form, all_parameters=True, form_key=True)


# Test 7: Form type property is consistent
@given(form_strategy(max_depth=2))
def test_form_type_property(form):
    """Test that form.type returns a valid Type object"""
    form_type = form.type
    assert isinstance(form_type, ak.types.Type)
    
    # The type should be convertible back to a form
    reconstructed = forms.from_type(form_type)
    # Note: from_type may not preserve all form details (like form_key)
    # but the basic structure should be similar
    assert isinstance(reconstructed, forms.Form)


# Test 8: length_zero_array produces valid empty arrays
@given(form_strategy(max_depth=2))
@settings(max_examples=50)
def test_length_zero_array(form):
    """Test that length_zero_array produces valid empty arrays"""
    try:
        arr = form.length_zero_array()
        assert len(arr) == 0
    except Exception as e:
        # Some forms might not support length_zero_array
        # Check if it's an expected failure
        if "EmptyForm" in str(e) or "unknowntype" in str(e):
            # Expected failures for EmptyForm
            pass
        else:
            raise


# Test 9: length_one_array produces valid single-element arrays
@given(form_strategy(max_depth=2))
@settings(max_examples=50)
def test_length_one_array(form):
    """Test that length_one_array produces valid single-element arrays"""
    try:
        arr = form.length_one_array()
        assert len(arr) == 1
    except TypeError as e:
        # Expected failure for EmptyForm
        if "unknowntype" in str(e) or "EmptyForm" in str(e):
            pass
        else:
            raise


if __name__ == "__main__":
    # Run a quick test
    test_form_dict_roundtrip()
    test_form_json_roundtrip()
    print("Basic tests passed!")