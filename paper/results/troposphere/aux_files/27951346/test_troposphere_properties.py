import json
from hypothesis import given, strategies as st, assume, settings
import troposphere
from troposphere import (
    Template, Parameter, Output, Tag, Tags,
    Join, Split, Select, Base64, Ref,
    validate_delimiter, validate_pausetime
)


@given(st.text(min_size=0, max_size=100))
def test_template_description_idempotence(description):
    """Template.to_dict() should be idempotent"""
    t = Template(Description=description)
    dict1 = t.to_dict()
    dict2 = t.to_dict()
    assert dict1 == dict2


@given(st.lists(
    st.tuples(
        st.from_regex(r'^[a-zA-Z0-9]+$').filter(lambda s: 1 <= len(s) <= 50),
        st.sampled_from(['String', 'Number', 'CommaDelimitedList', 'AWS::EC2::KeyPair::KeyName'])
    ),
    min_size=1,
    max_size=10
))
def test_template_parameters_preserve_in_dict(params):
    """Parameters added to template should appear in to_dict()"""
    t = Template()
    added_params = {}
    
    for name, param_type in params:
        if name not in added_params:
            p = Parameter(name, Type=param_type)
            t.add_parameter(p)
            added_params[name] = param_type
    
    result = t.to_dict()
    assert 'Parameters' in result
    assert len(result['Parameters']) == len(added_params)
    
    for name, param_type in added_params.items():
        assert name in result['Parameters']
        assert result['Parameters'][name]['Type'] == param_type


@given(st.from_regex(r'^[a-zA-Z0-9]+$').filter(lambda s: 1 <= len(s) <= 50))
def test_duplicate_parameter_names_raise_error(name):
    """Adding parameters with duplicate names should raise an error"""
    t = Template()
    p1 = Parameter(name, Type='String')
    p2 = Parameter(name, Type='Number')
    
    t.add_parameter(p1)
    try:
        t.add_parameter(p2)
        assert False, "Should have raised an error for duplicate parameter"
    except Exception as e:
        assert 'duplicate' in str(e).lower()


@given(st.one_of(
    st.text(min_size=0, max_size=10),
    st.just(''),
    st.just('\n'),
    st.just('\t'),
    st.just('|'),
    st.just(',')
))
def test_validate_delimiter_accepts_strings(delimiter):
    """validate_delimiter should accept any string"""
    result = validate_delimiter(delimiter)
    assert result is None


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.none(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
def test_validate_delimiter_rejects_non_strings(value):
    """validate_delimiter should reject non-strings"""
    try:
        validate_delimiter(value)
        assert False, f"Should have rejected non-string value: {value}"
    except ValueError as e:
        assert "must be a String" in str(e)


@given(
    hours=st.integers(min_value=0, max_value=999),
    minutes=st.integers(min_value=0, max_value=999),
    seconds=st.integers(min_value=0, max_value=999)
)
def test_validate_pausetime_valid_format(hours, minutes, seconds):
    """validate_pausetime should accept valid PT#H#M#S format"""
    # Build pausetime string
    parts = []
    if hours > 0:
        parts.append(f"{hours}H")
    if minutes > 0:
        parts.append(f"{minutes}M")
    if seconds > 0:
        parts.append(f"{seconds}S")
    
    if not parts:
        parts = ["0S"]
    
    pausetime = "PT" + "".join(parts)
    result = validate_pausetime(pausetime)
    assert result == pausetime


@given(st.text().filter(lambda s: not s.startswith('PT') or not any(c in s for c in 'HMS')))
def test_validate_pausetime_invalid_format(text):
    """validate_pausetime should reject invalid formats"""
    assume(text != '')
    try:
        validate_pausetime(text)
        if not text.startswith('PT'):
            assert False, f"Should have rejected pausetime without PT prefix: {text}"
    except ValueError as e:
        assert "should look like PT#H#M#S" in str(e)


@given(
    delimiter=st.text(min_size=0, max_size=5),
    items=st.lists(st.text(min_size=0, max_size=20), min_size=0, max_size=10)
)
def test_join_to_dict_deterministic(delimiter, items):
    """Join.to_dict() should be deterministic"""
    j = Join(delimiter, items)
    dict1 = j.to_dict()
    dict2 = j.to_dict()
    assert dict1 == dict2
    assert dict1 == {'Fn::Join': [delimiter, items]}


@given(
    index=st.integers(min_value=-100, max_value=100),
    items=st.lists(st.text(min_size=0, max_size=20), min_size=1, max_size=10)
)
def test_select_allows_any_index(index, items):
    """Select should allow any index without validation at creation"""
    sel = Select(index, items)
    result = sel.to_dict()
    assert result == {'Fn::Select': [index, items]}


@given(st.lists(
    st.tuples(
        st.text(min_size=1, max_size=50),
        st.text(min_size=0, max_size=100)
    ),
    min_size=0,
    max_size=20
))
def test_tags_preserve_all_tags(tag_pairs):
    """Tags should preserve all added tags"""
    tag_objects = [Tag(key, value) for key, value in tag_pairs]
    tags = Tags(*tag_objects)
    
    result = tags.to_dict()
    assert isinstance(result, list)
    assert len(result) == len(tag_pairs)
    
    for i, (key, value) in enumerate(tag_pairs):
        assert result[i]['Key'] == key
        assert result[i]['Value'] == value


@given(st.text(min_size=0, max_size=1000))
def test_base64_to_dict_preserves_input(text):
    """Base64.to_dict() should preserve the input text exactly"""
    b64 = Base64(text)
    result = b64.to_dict()
    assert result == {'Fn::Base64': text}


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=30).filter(lambda s: s.isidentifier()),
        st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=10
    )
)
def test_tags_from_kwargs_preserves_all(kwargs):
    """Tags created from kwargs should preserve all key-value pairs"""
    tags = Tags(**kwargs)
    result = tags.to_dict()
    
    assert isinstance(result, list)
    assert len(result) == len(kwargs)
    
    result_dict = {tag['Key']: tag['Value'] for tag in result}
    for key, value in kwargs.items():
        assert key in result_dict
        assert result_dict[key] == value


@given(st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=10))
def test_template_to_json_valid_json(items):
    """Template.to_json() should produce valid JSON"""
    t = Template()
    for i, item in enumerate(items):
        p = Parameter(f'Param{i}', Type='String', Default=item)
        t.add_parameter(p)
    
    json_str = t.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    # Should preserve parameter count
    assert len(parsed.get('Parameters', {})) == len(items)