#!/usr/bin/env python3
"""
Edge case tests for awkward.cppyy and cling modules
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import awkward.forms as forms
from awkward._connect import cling
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test for nested structures
@st.composite
def nested_forms(draw):
    """Generate nested form structures"""
    depth = draw(st.integers(min_value=1, max_value=3))
    
    # Start with a simple numpy form
    base = forms.NumpyForm(draw(st.sampled_from(["float64", "int32", "bool"])))
    
    for _ in range(depth):
        choice = draw(st.sampled_from(['regular', 'list', 'option']))
        if choice == 'regular':
            size = draw(st.integers(min_value=0, max_value=10))
            base = forms.RegularForm(base, size=size)
        elif choice == 'list':
            base = forms.ListOffsetForm("i64", base)
        else:  # option
            base = forms.UnmaskedForm(base)
    
    return base


# Test deeply nested structures
@given(form=nested_forms(), flatlist=st.booleans())
def test_nested_togenerator(form, flatlist):
    """Test togenerator with nested structures"""
    gen = cling.togenerator(form, flatlist)
    
    # Should return a generator
    assert isinstance(gen, cling.Generator)
    
    # Should have class_type
    ct = gen.class_type()
    assert isinstance(ct, str)
    assert len(ct) > 0
    
    # Should have value_type
    vt = gen.value_type()
    assert isinstance(vt, str)
    assert len(vt) > 0


# Test record forms
@st.composite
def record_forms(draw):
    """Generate record forms"""
    n_fields = draw(st.integers(min_value=1, max_value=5))
    
    # Generate field names
    use_tuple = draw(st.booleans())
    if use_tuple:
        fields = None  # Tuple (no field names)
    else:
        # Generate unique field names
        fields = []
        for i in range(n_fields):
            fields.append(f"field_{i}")
    
    # Generate contents
    contents = []
    for _ in range(n_fields):
        primitive = draw(st.sampled_from(["float64", "int32", "bool"]))
        contents.append(forms.NumpyForm(primitive))
    
    params = draw(st.one_of(
        st.just({}),
        st.just({"__record__": "TestRecord"}),
        st.dictionaries(st.text(min_size=1, max_size=5), st.text(max_size=10), max_size=2)
    ))
    
    return forms.RecordForm(contents, fields, parameters=params)


@given(form=record_forms(), flatlist=st.booleans())
def test_record_togenerator(form, flatlist):
    """Test togenerator with record forms"""
    gen = cling.togenerator(form, flatlist)
    
    # Should return a RecordArrayGenerator
    assert isinstance(gen, cling.RecordArrayGenerator)
    
    # Check fields preservation
    assert gen.fields == form.fields
    
    # Check number of contents
    assert len(gen.contenttypes) == len(form.contents)
    
    # Parameters should be preserved
    assert gen.parameters == form.parameters


# Test union forms
@st.composite
def union_forms(draw):
    """Generate union forms"""
    n_contents = draw(st.integers(min_value=2, max_value=5))
    
    contents = []
    for _ in range(n_contents):
        primitive = draw(st.sampled_from(["float64", "int32", "bool", "uint8"]))
        contents.append(forms.NumpyForm(primitive))
    
    index_type = draw(st.sampled_from(["i32", "u32", "i64"]))
    
    params = draw(st.dictionaries(
        st.text(min_size=1, max_size=5), 
        st.text(max_size=10), 
        max_size=2
    ))
    
    return forms.UnionForm(index_type, contents, parameters=params)


@given(form=union_forms(), flatlist=st.booleans())
def test_union_togenerator(form, flatlist):
    """Test togenerator with union forms"""
    gen = cling.togenerator(form, flatlist)
    
    # Should return a UnionArrayGenerator
    assert isinstance(gen, cling.UnionArrayGenerator)
    
    # Check index type mapping
    expected_index_type = {
        "i32": "int32_t",
        "u32": "uint32_t",
        "i64": "int64_t"
    }[form.index]
    assert gen.indextype == expected_index_type
    
    # Check number of contents
    assert len(gen.contenttypes) == len(form.contents)
    
    # Parameters should be preserved
    assert gen.parameters == form.parameters
    
    # value_type should be a std::variant
    vt = gen.value_type()
    assert "std::variant" in vt


# Test BitMaskedForm
@given(
    primitive=st.sampled_from(["float64", "int32", "bool"]),
    valid_when=st.booleans(),
    lsb_order=st.booleans()
)
def test_bitmasked_togenerator(primitive, valid_when, lsb_order):
    """Test togenerator with BitMaskedForm"""
    content = forms.NumpyForm(primitive)
    form = forms.BitMaskedForm(content, valid_when=valid_when, lsb_order=lsb_order)
    
    gen = cling.togenerator(form, flatlist_as_rvec=False)
    
    # Should return a BitMaskedArrayGenerator
    assert isinstance(gen, cling.BitMaskedArrayGenerator)
    
    # Check properties
    assert gen.valid_when == valid_when
    assert gen.lsb_order == lsb_order
    
    # value_type should be optional
    vt = gen.value_type()
    assert "std::optional" in vt


# Test IndexedForm and IndexedOptionForm
@given(
    primitive=st.sampled_from(["float64", "int32"]),
    index_type=st.sampled_from(["i32", "u32", "i64"]),
    is_option=st.booleans()
)
def test_indexed_togenerator(primitive, index_type, is_option):
    """Test togenerator with IndexedForm and IndexedOptionForm"""
    content = forms.NumpyForm(primitive)
    
    if is_option:
        # IndexedOptionForm only supports i32 and i64
        if index_type == "u32":
            index_type = "i32"
        form = forms.IndexedOptionForm(index_type, content)
    else:
        form = forms.IndexedForm(index_type, content)
    
    gen = cling.togenerator(form, flatlist_as_rvec=False)
    
    if is_option:
        assert isinstance(gen, cling.IndexedOptionArrayGenerator)
        # value_type should be optional
        vt = gen.value_type()
        assert "std::optional" in vt
    else:
        assert isinstance(gen, cling.IndexedArrayGenerator)


# Test generator hash and equality
@given(
    primitive1=st.sampled_from(["float64", "int32"]),
    primitive2=st.sampled_from(["float64", "int32"]),
    flatlist1=st.booleans(),
    flatlist2=st.booleans()
)
def test_generator_hash_equality(primitive1, primitive2, flatlist1, flatlist2):
    """Test generator hash and equality properties"""
    form1 = forms.NumpyForm(primitive1)
    form2 = forms.NumpyForm(primitive2)
    
    gen1a = cling.togenerator(form1, flatlist1)
    gen1b = cling.togenerator(form1, flatlist1)
    gen2 = cling.togenerator(form2, flatlist2)
    
    # Same form and flatlist should produce equal generators
    assert gen1a == gen1b
    assert hash(gen1a) == hash(gen1b)
    
    # Different forms or flatlist should produce different generators (usually)
    if primitive1 != primitive2 or flatlist1 != flatlist2:
        assert gen1a != gen2
        # Hashes should be different (with high probability)
        # This might occasionally fail due to hash collisions
        # but should work in most cases


# Test cache corruption
def test_cache_corruption():
    """Test that cache doesn't get corrupted by multiple accesses"""
    # Clear cache
    cling.cache.clear()
    
    # Mock compiler
    class MockCompiler:
        def __init__(self):
            self.calls = []
        
        def __call__(self, code):
            self.calls.append(code)
    
    compiler1 = MockCompiler()
    compiler2 = MockCompiler()
    
    # Generate headers twice with caching
    h1 = cling.generate_headers(compiler1, use_cached=True)
    h2 = cling.generate_headers(compiler2, use_cached=True)
    
    # Should be same object
    assert h1 is h2
    
    # Only first compiler should be called
    assert len(compiler1.calls) == 1
    assert len(compiler2.calls) == 0
    
    # Clear cache and try with different functions
    cling.cache.clear()
    
    av1 = cling.generate_ArrayView(compiler1, use_cached=True)
    av2 = cling.generate_ArrayView(compiler2, use_cached=True)
    
    assert av1 is av2
    
    # Check that different functions don't interfere
    h3 = cling.generate_headers(compiler1, use_cached=True)
    assert h3 is not av1  # Different functions should have different cache entries


# Test edge case: zero-size regular array
def test_zero_size_regular():
    """Test RegularForm with size=0"""
    form = forms.RegularForm(forms.NumpyForm("float64"), size=0)
    gen = cling.togenerator(form, flatlist_as_rvec=False)
    
    assert isinstance(gen, cling.RegularArrayGenerator)
    assert gen.size == 0
    
    # Should still generate valid code
    compiler = lambda x: None
    gen.generate(compiler, use_cached=False)  # Should not crash


# Test special characters in parameters
@given(
    key=st.text(min_size=1, max_size=10, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
    value=st.one_of(
        st.text(max_size=20),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_special_chars_in_parameters(key, value):
    """Test forms with special characters in parameters"""
    assume(key.strip() != "")  # Skip empty keys
    
    params = {key: value}
    form = forms.NumpyForm("float64", parameters=params)
    
    gen = cling.togenerator(form, flatlist_as_rvec=False)
    
    # Parameters should be preserved exactly
    assert gen.parameters == params
    
    # Should still generate valid class_type
    ct = gen.class_type()
    assert isinstance(ct, str)
    assert len(ct) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])