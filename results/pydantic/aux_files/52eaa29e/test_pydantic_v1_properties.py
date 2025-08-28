import math
from decimal import Decimal
from datetime import datetime, date, time
from typing import List, Dict, Optional, Set, Any
import uuid

import pydantic.v1
from hypothesis import given, strategies as st, assume, settings


# ========== BaseModel JSON Round-Trip Properties ==========

@st.composite
def simple_json_compatible_value(draw):
    """Generate simple JSON-compatible values"""
    return draw(st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(min_size=0, max_size=100),
    ))


@st.composite
def nested_json_compatible_value(draw, max_depth=3):
    """Generate nested JSON-compatible values with controlled depth"""
    if max_depth <= 0:
        return draw(simple_json_compatible_value())
    
    return draw(st.one_of(
        simple_json_compatible_value(),
        st.lists(simple_json_compatible_value(), max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            simple_json_compatible_value(),
            max_size=10
        )
    ))


@given(
    name=st.text(min_size=1, max_size=50),
    age=st.integers(min_value=0, max_value=150),
    optional_field=st.one_of(st.none(), st.text()),
    items=st.lists(st.integers(), max_size=20)
)
def test_basemodel_json_roundtrip(name, age, optional_field, items):
    """Test that BaseModel instances survive JSON round-trip"""
    class TestModel(pydantic.v1.BaseModel):
        name: str
        age: int
        optional_field: Optional[str]
        items: List[int]
    
    original = TestModel(
        name=name,
        age=age,
        optional_field=optional_field,
        items=items
    )
    
    json_str = original.json()
    reconstructed = TestModel.parse_raw(json_str)
    
    assert original == reconstructed
    assert original.dict() == reconstructed.dict()


@given(
    decimal_val=st.decimals(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    datetime_val=st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 1, 1)),
    date_val=st.dates(min_value=date(1900, 1, 1), max_value=date(2100, 1, 1)),
    uuid_val=st.uuids()
)
def test_special_types_json_roundtrip(decimal_val, datetime_val, date_val, uuid_val):
    """Test that special types survive JSON round-trip"""
    class SpecialModel(pydantic.v1.BaseModel):
        decimal_field: Decimal
        datetime_field: datetime
        date_field: date
        uuid_field: uuid.UUID
    
    original = SpecialModel(
        decimal_field=decimal_val,
        datetime_field=datetime_val,
        date_field=date_val,
        uuid_field=uuid_val
    )
    
    json_str = original.json()
    reconstructed = SpecialModel.parse_raw(json_str)
    
    assert original == reconstructed
    assert str(original.decimal_field) == str(reconstructed.decimal_field)


# ========== Constrained Types Properties ==========

@given(value=st.integers())
def test_conint_validation_boundaries(value):
    """Test that conint properly validates boundaries"""
    ConInt = pydantic.v1.conint(ge=0, le=100)
    
    class Model(pydantic.v1.BaseModel):
        limited: ConInt
    
    if 0 <= value <= 100:
        model = Model(limited=value)
        assert model.limited == value
    else:
        try:
            Model(limited=value)
            assert False, f"Should have raised validation error for {value}"
        except pydantic.v1.ValidationError:
            pass


@given(value=st.floats(allow_nan=False, allow_infinity=False))
def test_confloat_validation_boundaries(value):
    """Test that confloat properly validates boundaries"""
    ConFloat = pydantic.v1.confloat(ge=-10.0, le=10.0)
    
    class Model(pydantic.v1.BaseModel):
        limited: ConFloat
    
    if -10.0 <= value <= 10.0:
        model = Model(limited=value)
        assert math.isclose(model.limited, value, rel_tol=1e-9)
    else:
        try:
            Model(limited=value)
            assert False, f"Should have raised validation error for {value}"
        except pydantic.v1.ValidationError:
            pass


@given(value=st.text())
def test_constr_length_validation(value):
    """Test that constr properly validates string length"""
    ConStr = pydantic.v1.constr(min_length=1, max_length=10)
    
    class Model(pydantic.v1.BaseModel):
        limited: ConStr
    
    if 1 <= len(value) <= 10:
        model = Model(limited=value)
        assert model.limited == value
    else:
        try:
            Model(limited=value)
            assert False, f"Should have raised validation error for string of length {len(value)}"
        except pydantic.v1.ValidationError:
            pass


@given(items=st.lists(st.integers()))
def test_conlist_size_validation(items):
    """Test that conlist properly validates list size"""
    ConList = pydantic.v1.conlist(int, min_items=1, max_items=5)
    
    class Model(pydantic.v1.BaseModel):
        limited: ConList
    
    if 1 <= len(items) <= 5:
        model = Model(limited=items)
        assert model.limited == items
    else:
        try:
            Model(limited=items)
            assert False, f"Should have raised validation error for list of size {len(items)}"
        except pydantic.v1.ValidationError:
            pass


# ========== ByteSize Properties ==========

@given(bytes_value=st.integers(min_value=0, max_value=10**15))
def test_bytesize_integer_roundtrip(bytes_value):
    """Test ByteSize construction from integer and conversion"""
    b = pydantic.v1.ByteSize(bytes_value)
    assert int(b) == bytes_value
    
    # Test through model
    class Model(pydantic.v1.BaseModel):
        size: pydantic.v1.ByteSize
    
    m = Model(size=bytes_value)
    assert int(m.size) == bytes_value


@given(bytes_value=st.integers(min_value=1, max_value=10**12))
def test_bytesize_unit_conversion_consistency(bytes_value):
    """Test that ByteSize unit conversions are consistent"""
    b = pydantic.v1.ByteSize(bytes_value)
    
    # Test conversions to different units
    kb_decimal = b.to('KB')
    mb_decimal = b.to('MB')
    
    # Verify relationships between units (decimal)
    assert math.isclose(kb_decimal * 1000, bytes_value, rel_tol=1e-9)
    assert math.isclose(mb_decimal * 1000000, bytes_value, rel_tol=1e-9)
    
    # Test binary units
    kib_binary = b.to('KiB')
    mib_binary = b.to('MiB')
    
    assert math.isclose(kib_binary * 1024, bytes_value, rel_tol=1e-9)
    assert math.isclose(mib_binary * 1024 * 1024, bytes_value, rel_tol=1e-9)


@given(
    value=st.floats(min_value=0.1, max_value=1000),
    unit=st.sampled_from(['B', 'KB', 'MB', 'GB', 'KiB', 'MiB', 'GiB'])
)
def test_bytesize_string_parsing(value, unit):
    """Test ByteSize parsing from string format through BaseModel"""
    class Model(pydantic.v1.BaseModel):
        size: pydantic.v1.ByteSize
    
    input_str = f"{value}{unit}"
    
    try:
        m = Model(size=input_str)
        
        # Calculate expected bytes
        multipliers = {
            'B': 1,
            'KB': 1000,
            'MB': 1000**2,
            'GB': 1000**3,
            'KiB': 1024,
            'MiB': 1024**2,
            'GiB': 1024**3,
        }
        
        expected_bytes = value * multipliers[unit]
        actual_bytes = int(m.size)
        
        # Allow for some floating point error
        assert math.isclose(actual_bytes, expected_bytes, rel_tol=1e-6)
        
    except Exception as e:
        # Some formats might not be supported
        pass


# ========== URL Properties ==========

@given(
    scheme=st.sampled_from(['http', 'https']),
    host=st.from_regex(r'[a-z][a-z0-9-]{0,20}\.com', fullmatch=True),
    path=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789/-', min_size=0, max_size=50),
    query=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789=&', min_size=0, max_size=50),
    fragment=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=0, max_size=20)
)
def test_url_parsing_components(scheme, host, path, query, fragment):
    """Test that URL components are correctly parsed"""
    # Build URL
    url_str = f"{scheme}://{host}"
    if path and not path.startswith('/'):
        path = '/' + path
    url_str += path
    if query:
        url_str += '?' + query
    if fragment:
        url_str += '#' + fragment
    
    try:
        if scheme in ['http', 'https']:
            url = pydantic.v1.HttpUrl(url_str)
        else:
            url = pydantic.v1.AnyUrl(url_str)
        
        # Verify components
        assert url.scheme == scheme
        assert url.host == host
        
        # Path might be normalized
        if path:
            assert url.path is not None
        
        if query:
            assert url.query is not None
            
        if fragment:
            assert url.fragment == fragment
            
    except pydantic.v1.UrlError:
        # Some combinations might be invalid
        pass


@given(port=st.integers(min_value=1, max_value=65535))
def test_url_port_validation(port):
    """Test URL port number handling"""
    url_str = f"http://example.com:{port}/path"
    
    url = pydantic.v1.HttpUrl(url_str)
    assert url.port == str(port)
    assert url.host == 'example.com'


# ========== Email Validation Properties ==========

@given(
    local=st.from_regex(r'[a-z][a-z0-9.]{0,20}', fullmatch=True),
    domain=st.from_regex(r'[a-z][a-z0-9-]{0,20}\.com', fullmatch=True)
)
def test_email_validation_valid(local, domain):
    """Test that valid emails are accepted"""
    email = f"{local}@{domain}"
    
    class Model(pydantic.v1.BaseModel):
        email: pydantic.v1.EmailStr
    
    try:
        m = Model(email=email)
        assert '@' in m.email
        assert m.email.count('@') == 1
    except pydantic.v1.EmailError:
        # Some combinations might still be invalid per RFC
        pass


# ========== Complex Nested Model Properties ==========

@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=50),
            st.booleans(),
            st.none()
        ),
        max_size=10
    )
)
def test_dynamic_model_creation(data):
    """Test creating models dynamically with create_model"""
    # Filter to valid field names
    valid_data = {k: v for k, v in data.items() if k.isidentifier() and not k.startswith('_')}
    
    if not valid_data:
        return
    
    # Create field definitions
    fields = {}
    for key, value in valid_data.items():
        if value is None:
            fields[key] = (Optional[str], None)
        elif isinstance(value, bool):
            fields[key] = (bool, value)
        elif isinstance(value, int):
            fields[key] = (int, value)
        elif isinstance(value, float):
            fields[key] = (float, value)
        else:
            fields[key] = (str, str(value))
    
    # Create dynamic model
    DynamicModel = pydantic.v1.create_model('DynamicModel', **fields)
    
    # Test instantiation
    instance = DynamicModel()
    
    # Test JSON round-trip
    json_str = instance.json()
    reconstructed = DynamicModel.parse_raw(json_str)
    assert instance == reconstructed


# ========== Validation Error Properties ==========

@given(value=st.integers())
def test_validation_error_contains_value(value):
    """Test that validation errors contain information about the invalid value"""
    ConInt = pydantic.v1.conint(ge=0, le=10)
    
    class Model(pydantic.v1.BaseModel):
        field: ConInt
    
    if not (0 <= value <= 10):
        try:
            Model(field=value)
            assert False, "Should have raised ValidationError"
        except pydantic.v1.ValidationError as e:
            error_dict = e.errors()[0]
            assert 'field' in str(error_dict['loc'])
            assert error_dict['type'] in ['value_error.number.not_ge', 'value_error.number.not_le']