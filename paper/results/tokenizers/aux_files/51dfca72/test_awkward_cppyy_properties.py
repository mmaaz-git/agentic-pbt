#!/usr/bin/env python3
"""
Property-based tests for awkward.cppyy and awkward._connect.cling modules
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import awkward.forms as forms
from awkward._connect import cling
from hypothesis import given, strategies as st, assume, settings
import pytest


# Strategy for generating NumpyForm primitives
numpy_primitives = st.sampled_from([
    "bool", "int8", "uint8", "int16", "uint16", "int32", "uint32", 
    "int64", "uint64", "float32", "float64", 
    "complex64", "complex128"
])

# Strategy for generating index types
index_types = st.sampled_from(["i32", "u32", "i64"])

# Strategy for generating simple parameters
simple_params = st.dictionaries(
    st.text(min_size=1, max_size=10, alphabet=st.characters(categories=['Lu', 'Ll', 'Nd'])),
    st.one_of(st.text(max_size=20), st.integers(), st.floats(allow_nan=False, allow_infinity=False)),
    max_size=3
)


@st.composite
def simple_forms(draw):
    """Generate simple Awkward forms for testing"""
    form_type = draw(st.sampled_from(['numpy', 'empty', 'regular', 'list', 'unmasked']))
    params = draw(simple_params)
    
    if form_type == 'numpy':
        primitive = draw(numpy_primitives)
        return forms.NumpyForm(primitive=primitive, parameters=params)
    elif form_type == 'empty':
        # EmptyForm cannot have parameters
        return forms.EmptyForm()
    elif form_type == 'regular':
        primitive = draw(numpy_primitives)
        size = draw(st.integers(min_value=0, max_value=100))
        content = forms.NumpyForm(primitive=primitive)
        return forms.RegularForm(content=content, size=size, parameters=params)
    elif form_type == 'list':
        primitive = draw(numpy_primitives)
        index_type = draw(index_types)
        content = forms.NumpyForm(primitive=primitive)
        return forms.ListOffsetForm(offsets=index_type, content=content, parameters=params)
    else:  # unmasked
        primitive = draw(numpy_primitives)
        content = forms.NumpyForm(primitive=primitive)
        return forms.UnmaskedForm(content=content, parameters=params)


# Property 1: togenerator always returns a Generator instance
@given(form=simple_forms(), flatlist_as_rvec=st.booleans())
def test_togenerator_returns_generator(form, flatlist_as_rvec):
    """togenerator should always return a Generator subclass instance"""
    generator = cling.togenerator(form, flatlist_as_rvec)
    assert isinstance(generator, cling.Generator)
    # Check it has expected methods
    assert hasattr(generator, 'class_type')
    assert hasattr(generator, 'value_type')
    assert hasattr(generator, 'generate')
    assert callable(generator.class_type)
    assert callable(generator.value_type)
    assert callable(generator.generate)


# Property 2: togenerator idempotence
@given(form=simple_forms(), flatlist_as_rvec=st.booleans())
def test_togenerator_idempotence(form, flatlist_as_rvec):
    """Calling togenerator twice with same inputs should produce equivalent generators"""
    gen1 = cling.togenerator(form, flatlist_as_rvec)
    gen2 = cling.togenerator(form, flatlist_as_rvec)
    
    # They should produce the same class_type
    assert gen1.class_type() == gen2.class_type()
    
    # They should produce the same value_type
    assert gen1.value_type() == gen2.value_type()
    
    # They should be equal (if __eq__ is properly implemented)
    assert gen1 == gen2


# Property 3: EmptyForm is always converted to NumpyForm with float64
def test_empty_form_conversion():
    """EmptyForm should be converted to NumpyForm with float64 primitive"""
    empty_form = forms.EmptyForm()
    generator = cling.togenerator(empty_form, flatlist_as_rvec=False)
    
    # Should return a NumpyArrayGenerator
    assert isinstance(generator, cling.NumpyArrayGenerator)
    assert generator.primitive == "float64"
    # EmptyForm has no parameters, and converted form should also have empty parameters
    assert generator.parameters == {}


# Property 4: flatlist_as_rvec parameter affects class_type
@given(form=simple_forms())
def test_flatlist_as_rvec_affects_class_type(form):
    """The flatlist_as_rvec parameter should affect the generated class_type"""
    gen_false = cling.togenerator(form, flatlist_as_rvec=False)
    gen_true = cling.togenerator(form, flatlist_as_rvec=True)
    
    # The class_type should be different when flatlist_as_rvec changes
    # This is because the hash includes flatlist_as_rvec
    assert gen_false.class_type() != gen_true.class_type()


# Property 5: Form type mapping is consistent
@given(primitive=numpy_primitives, params=simple_params)
def test_form_type_mapping(primitive, params):
    """Each form type should map to the expected generator type"""
    # NumpyForm -> NumpyArrayGenerator
    numpy_form = forms.NumpyForm(primitive=primitive, parameters=params)
    gen = cling.togenerator(numpy_form, flatlist_as_rvec=False)
    assert isinstance(gen, cling.NumpyArrayGenerator)
    
    # RegularForm -> RegularArrayGenerator
    regular_form = forms.RegularForm(numpy_form, size=10, parameters=params)
    gen = cling.togenerator(regular_form, flatlist_as_rvec=False)
    assert isinstance(gen, cling.RegularArrayGenerator)
    
    # ListOffsetForm -> ListArrayGenerator
    list_form = forms.ListOffsetForm("i64", numpy_form, parameters=params)
    gen = cling.togenerator(list_form, flatlist_as_rvec=False)
    assert isinstance(gen, cling.ListArrayGenerator)
    
    # UnmaskedForm -> UnmaskedArrayGenerator
    unmasked_form = forms.UnmaskedForm(numpy_form, parameters=params)
    gen = cling.togenerator(unmasked_form, flatlist_as_rvec=False)
    assert isinstance(gen, cling.UnmaskedArrayGenerator)


# Property 6: Header generation functions always return valid C++ code strings
class MockCompiler:
    def __init__(self):
        self.compiled = []
    
    def __call__(self, code):
        self.compiled.append(code)


@given(use_cached=st.booleans())
def test_generate_headers_properties(use_cached):
    """generate_headers should always return valid C++ header code"""
    compiler = MockCompiler()
    headers = cling.generate_headers(compiler, use_cached=use_cached)
    
    # Should return a string
    assert isinstance(headers, str)
    
    # Should contain essential C++ headers
    assert '#include' in headers
    assert 'Python.h' in headers
    
    # Should not be empty
    assert len(headers) > 0
    
    # Compiler should have been called (if not cached or first time)
    if not use_cached or 'headers' not in cling.cache:
        assert len(compiler.compiled) > 0


@given(use_cached=st.booleans())
def test_generate_array_view_properties(use_cached):
    """generate_ArrayView should always return valid C++ class code"""
    compiler = MockCompiler()
    array_view = cling.generate_ArrayView(compiler, use_cached=use_cached)
    
    # Should return a string
    assert isinstance(array_view, str)
    
    # Should contain namespace and class definitions
    assert 'namespace awkward' in array_view
    assert 'class ArrayView' in array_view
    assert 'class Iterator' in array_view
    
    # Should not be empty
    assert len(array_view) > 0


@given(use_cached=st.booleans())
def test_generate_record_view_properties(use_cached):
    """generate_RecordView should always return valid C++ class code"""
    compiler = MockCompiler()
    record_view = cling.generate_RecordView(compiler, use_cached=use_cached)
    
    # Should return a string
    assert isinstance(record_view, str)
    
    # Should contain namespace and class definitions
    assert 'namespace awkward' in record_view
    assert 'class RecordView' in record_view
    
    # Should not be empty
    assert len(record_view) > 0


@given(use_cached=st.booleans())
def test_generate_array_builder_properties(use_cached):
    """generate_ArrayBuilder should always return valid C++ class code"""
    compiler = MockCompiler()
    array_builder = cling.generate_ArrayBuilder(compiler, use_cached=use_cached)
    
    # Should return a string
    assert isinstance(array_builder, str)
    
    # Should contain namespace and class definitions
    assert 'namespace awkward' in array_builder
    assert 'class ArrayBuilder' in array_builder
    
    # Should define error codes
    assert 'SUCCESS' in array_builder
    assert 'FAILURE' in array_builder
    
    # Should not be empty
    assert len(array_builder) > 0


# Property 7: Cache behavior
def test_cache_behavior():
    """Cache should return the same object when use_cached=True"""
    # Clear cache first
    cling.cache.clear()
    
    compiler1 = MockCompiler()
    compiler2 = MockCompiler()
    
    # First call should populate cache
    headers1 = cling.generate_headers(compiler1, use_cached=True)
    assert len(compiler1.compiled) == 1  # Compiler was called
    
    # Second call should use cache
    headers2 = cling.generate_headers(compiler2, use_cached=True)
    assert len(compiler2.compiled) == 0  # Compiler was NOT called
    
    # Should be the exact same object (not just equal)
    assert headers1 is headers2
    
    # With use_cached=False, should always call compiler
    compiler3 = MockCompiler()
    headers3 = cling.generate_headers(compiler3, use_cached=False)
    assert len(compiler3.compiled) == 1  # Compiler was called
    
    # But the result should still be equal
    assert headers3 == headers1


# Property 8: Generator class_type uniqueness
@given(form1=simple_forms(), form2=simple_forms(), flatlist=st.booleans())
def test_generator_class_type_uniqueness(form1, form2, flatlist):
    """Different forms should produce different class_types (unless they're equivalent)"""
    gen1 = cling.togenerator(form1, flatlist)
    gen2 = cling.togenerator(form2, flatlist)
    
    # If the generators are not equal, their class_types should be different
    if gen1 != gen2:
        assert gen1.class_type() != gen2.class_type()
    else:
        # If generators are equal, class_types should be the same
        assert gen1.class_type() == gen2.class_type()


# Property 9: NumpyArrayGenerator primitive mapping
@given(primitive=numpy_primitives, params=simple_params)
def test_numpy_generator_primitive_mapping(primitive, params):
    """NumpyArrayGenerator should correctly map primitives to C++ types"""
    form = forms.NumpyForm(primitive=primitive, parameters=params)
    gen = cling.togenerator(form, flatlist_as_rvec=False)
    
    assert isinstance(gen, cling.NumpyArrayGenerator)
    assert gen.primitive == primitive
    
    # Check value_type mapping
    expected_mapping = {
        "bool": "bool",
        "int8": "int8_t",
        "uint8": "uint8_t",
        "int16": "int16_t",
        "uint16": "uint16_t",
        "int32": "int32_t",
        "uint32": "uint32_t",
        "int64": "int64_t",
        "uint64": "uint64_t",
        "float32": "float",
        "float64": "double",
        "complex64": "std::complex<float>",
        "complex128": "std::complex<double>",
    }
    
    if primitive in expected_mapping:
        assert gen.value_type() == expected_mapping[primitive]


# Property 10: Generator generate method produces C++ code
@given(form=simple_forms(), flatlist=st.booleans())
@settings(max_examples=20)  # Limit this test as it's more expensive
def test_generator_generate_method(form, flatlist):
    """Generator.generate() should produce valid C++ code"""
    compiler = MockCompiler()
    gen = cling.togenerator(form, flatlist)
    
    # Clear cache to ensure fresh generation
    cling.cache.clear()
    
    # Call generate
    gen.generate(compiler, use_cached=False)
    
    # Compiler should have been called (at least for dependencies)
    assert len(compiler.compiled) > 0
    
    # The generated code should contain the class definition
    generated_code = '\n'.join(compiler.compiled)
    assert 'namespace awkward' in generated_code
    assert gen.class_type() in generated_code


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])