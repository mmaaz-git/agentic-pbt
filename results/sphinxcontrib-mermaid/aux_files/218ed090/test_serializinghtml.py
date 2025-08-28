"""Property-based tests for sphinxcontrib.serializinghtml"""

import json
import tempfile
from collections import UserString
from pathlib import Path

import pytest
from hypothesis import given, strategies as st, assume

# Import module under test
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.serializinghtml import jsonimpl
from sphinxcontrib.serializinghtml import JSONHTMLBuilder


# Strategy for generating JSON-serializable values
json_value = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(), children, max_size=10)
    ),
    max_leaves=50
)


@given(json_value)
def test_json_round_trip_dumps_loads(data):
    """Test that jsonimpl.loads(jsonimpl.dumps(x)) == x for JSON-serializable data"""
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


@given(json_value)
def test_json_round_trip_dump_load(data):
    """Test that jsonimpl.dump/load round-trips correctly through files"""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        jsonimpl.dump(data, f)
        f.flush()
        f.seek(0)
        loaded = jsonimpl.load(f)
        assert loaded == data


@given(st.text())
def test_userstring_serialization(text):
    """Test that UserString objects are correctly serialized"""
    user_str = UserString(text)
    
    # Test dumps
    serialized = jsonimpl.dumps(user_str)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == text
    
    # Test that it serializes the same as a regular string
    regular_serialized = jsonimpl.dumps(text)
    assert serialized == regular_serialized


@given(st.dictionaries(
    st.text(),
    st.one_of(
        st.text(),
        st.lists(UserString, max_size=5),
        st.dictionaries(st.text(), UserString, max_size=5)
    ),
    max_size=10
))
def test_nested_userstring_serialization(data):
    """Test that nested structures with UserString are handled correctly"""
    # Create UserString instances in the data
    def make_userstrings(obj):
        if isinstance(obj, str):
            return UserString(obj)
        elif isinstance(obj, list):
            return [make_userstrings(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: make_userstrings(v) for k, v in obj.items()}
        return obj
    
    data_with_userstrings = make_userstrings(data)
    
    # Should not raise an exception
    serialized = jsonimpl.dumps(data_with_userstrings)
    
    # The result should be valid JSON
    deserialized = jsonimpl.loads(serialized)
    
    # Convert UserStrings back to regular strings for comparison
    def to_strings(obj):
        if isinstance(obj, UserString):
            return str(obj)
        elif isinstance(obj, list):
            return [to_strings(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: to_strings(v) for k, v in obj.items()}
        return obj
    
    expected = to_strings(data_with_userstrings)
    assert deserialized == expected


@given(st.text())
def test_get_target_uri_properties(docname):
    """Test properties of get_target_uri method"""
    # Create a minimal JSONHTMLBuilder instance
    # We need to mock the necessary parts
    from unittest.mock import MagicMock
    from sphinx.application import Sphinx
    from sphinx.util.osutil import SEP
    
    app = MagicMock(spec=Sphinx)
    app.config = MagicMock()
    app.env = MagicMock()
    
    builder = JSONHTMLBuilder(app, app.env)
    
    # Test the properties documented in the code
    uri = builder.get_target_uri(docname)
    
    # Property 1: 'index' returns empty string
    if docname == 'index':
        assert uri == ''
    # Property 2: paths ending with SEP + 'index' have that suffix removed
    elif docname.endswith(SEP + 'index'):
        assert uri == docname[:-5]
    # Property 3: other paths get SEP appended
    else:
        assert uri == docname + SEP


@given(st.dictionaries(
    st.text(),
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.text(), max_size=5)
    ),
    max_size=20
))
def test_dump_context_preserves_data(context):
    """Test that dump_context correctly serializes and can be loaded back"""
    from unittest.mock import MagicMock
    from sphinx.application import Sphinx
    
    app = MagicMock(spec=Sphinx)
    app.config = MagicMock()
    app.env = MagicMock()
    
    builder = JSONHTMLBuilder(app, app.env)
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        filename = f.name
        
    # Dump the context
    builder.dump_context(context, filename)
    
    # Load it back
    with open(filename, 'r', encoding='utf-8') as f:
        loaded = json.load(f)
    
    # The loaded data should match the original (minus any special handling)
    # Note: css_files and script_files get special treatment
    expected = context.copy()
    if 'css_files' in expected:
        # These would be transformed to just filenames
        pass
    if 'script_files' in expected:
        # These would be transformed to just filenames
        pass
    
    for key in expected:
        if key not in ['css_files', 'script_files']:
            assert loaded.get(key) == expected[key]


# Test for edge cases in JSON encoding
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False, width=64),
    st.integers(min_value=-2**53, max_value=2**53)  # JavaScript safe integer range
))
def test_json_numeric_precision(num):
    """Test that numeric values maintain precision through serialization"""
    serialized = jsonimpl.dumps(num)
    deserialized = jsonimpl.loads(serialized)
    
    if isinstance(num, float):
        # For floats, we need to be careful about precision
        import math
        if math.isfinite(num):
            # JSON might lose some precision for floats
            assert abs(deserialized - num) < 1e-10 or deserialized == num
    else:
        assert deserialized == num


@given(st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=127)))
def test_json_ascii_text_round_trip(text):
    """Test round-trip for ASCII text to avoid Unicode issues"""
    data = {"text": text, "list": [text], "nested": {"value": text}}
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


@given(st.text())
def test_json_unicode_text_round_trip(text):
    """Test round-trip for Unicode text"""
    data = {"text": text}
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


@given(st.lists(st.dictionaries(st.text(), st.text(), max_size=5), max_size=10))
def test_json_complex_structure_round_trip(data):
    """Test round-trip for more complex nested structures"""
    container = {
        "items": data,
        "count": len(data),
        "metadata": {
            "type": "test",
            "nested": {"deep": {"structure": data[:2] if len(data) >= 2 else data}}
        }
    }
    serialized = jsonimpl.dumps(container)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == container