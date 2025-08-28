import dataclasses
from dataclasses import dataclass, field, asdict, astuple, replace, make_dataclass, fields, is_dataclass
from hypothesis import given, strategies as st, assume, settings
import math
import pytest
from typing import Any, Dict, List, Optional


@given(
    st.text(min_size=1).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
    st.lists(
        st.tuples(
            st.text(min_size=1).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
            st.sampled_from([int, str, float, bool, list, dict, type(None)])
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]
    )
)
def test_make_dataclass_fields_roundtrip(class_name, field_specs):
    import keyword
    
    field_list = [(name, typ) for name, typ in field_specs]
    
    try:
        cls = make_dataclass(class_name, field_list)
    except (TypeError, ValueError) as e:
        return
    
    retrieved_fields = fields(cls)
    
    assert len(retrieved_fields) == len(field_list)
    
    for i, (expected_name, expected_type) in enumerate(field_list):
        assert retrieved_fields[i].name == expected_name
        assert retrieved_fields[i].type == expected_type


@given(
    st.text(min_size=1).filter(lambda x: x.isidentifier()),
    st.lists(
        st.tuples(
            st.text(min_size=1).filter(lambda x: x.isidentifier()),
            st.one_of(st.integers(), st.text(), st.floats(allow_nan=False, allow_infinity=False), st.booleans())
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]
    )
)
def test_asdict_astuple_value_consistency(class_name, field_values):
    import keyword
    assume(not keyword.iskeyword(class_name))
    for name, _ in field_values:
        assume(not keyword.iskeyword(name))
    
    field_list = [(name, type(val)) for name, val in field_values]
    
    try:
        cls = make_dataclass(class_name, field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**{name: val for name, val in field_values})
    
    dict_result = asdict(instance)
    tuple_result = astuple(instance)
    
    assert len(dict_result) == len(field_values)
    assert len(tuple_result) == len(field_values)
    
    for i, (name, val) in enumerate(field_values):
        assert dict_result[name] == val
        assert tuple_result[i] == val
    
    assert list(dict_result.values()) == list(tuple_result)


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1).filter(lambda x: x.isidentifier()),
            st.one_of(st.integers(), st.text(), st.floats(allow_nan=False, allow_infinity=False))
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]
    )
)
def test_replace_preserves_other_fields(field_values):
    import keyword
    for name, _ in field_values:
        assume(not keyword.iskeyword(name))
    
    field_list = [(name, type(val)) for name, val in field_values]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**{name: val for name, val in field_values})
    
    if len(field_values) >= 2:
        field_to_change = field_values[0][0]
        new_value = field_values[0][1]
        if isinstance(new_value, (int, float)):
            new_value = new_value + 1 if new_value != float('inf') else new_value - 1
        elif isinstance(new_value, str):
            new_value = new_value + "_modified"
        
        new_instance = replace(instance, **{field_to_change: new_value})
        
        for name, original_val in field_values:
            if name != field_to_change:
                assert getattr(new_instance, name) == original_val
            else:
                assert getattr(new_instance, name) == new_value


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1).filter(lambda x: x.isidentifier()),
            st.one_of(st.integers(), st.text(), st.floats(allow_nan=False, allow_infinity=False))
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]
    )
)
def test_asdict_modifications_dont_affect_original(field_values):
    import keyword
    for name, _ in field_values:
        assume(not keyword.iskeyword(name))
    
    field_list = [(name, type(val)) for name, val in field_values]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**{name: val for name, val in field_values})
    original_values = {name: getattr(instance, name) for name, _ in field_values}
    
    dict_result = asdict(instance)
    
    for key in dict_result:
        if isinstance(dict_result[key], (int, float, str)):
            if isinstance(dict_result[key], (int, float)):
                dict_result[key] = 999999
            else:
                dict_result[key] = "MODIFIED"
    
    for name, _ in field_values:
        assert getattr(instance, name) == original_values[name]


@dataclass
class NestedDataclass:
    value: int
    text: str


@given(
    st.integers(),
    st.text()
)
def test_asdict_nested_dataclass_deep_copy(val, txt):
    @dataclass
    class Container:
        nested: NestedDataclass
        other: int
    
    nested_obj = NestedDataclass(value=val, text=txt)
    container = Container(nested=nested_obj, other=42)
    
    dict_result = asdict(container)
    
    assert isinstance(dict_result['nested'], dict)
    assert dict_result['nested']['value'] == val
    assert dict_result['nested']['text'] == txt
    
    dict_result['nested']['value'] = val + 1000
    assert nested_obj.value == val


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1).filter(lambda x: x.isidentifier()),
            st.sampled_from([int, str, float, bool])
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]
    ),
    st.booleans()
)
def test_frozen_dataclass_immutability(field_specs, frozen):
    import keyword
    for name, _ in field_specs:
        assume(not keyword.iskeyword(name))
    
    field_list = [(name, typ) for name, typ in field_specs]
    
    try:
        cls = make_dataclass("TestClass", field_list, frozen=frozen)
    except (TypeError, ValueError):
        return
    
    values = {}
    for name, typ in field_list:
        if typ == int:
            values[name] = 1
        elif typ == str:
            values[name] = "test"
        elif typ == float:
            values[name] = 1.0
        elif typ == bool:
            values[name] = True
    
    instance = cls(**values)
    
    if frozen:
        for name in values:
            with pytest.raises(dataclasses.FrozenInstanceError):
                setattr(instance, name, values[name])
    else:
        for name in values:
            new_val = values[name]
            if isinstance(new_val, int):
                new_val = 999
            elif isinstance(new_val, str):
                new_val = "modified"
            setattr(instance, name, new_val)
            assert getattr(instance, name) == new_val


@given(
    st.lists(st.text(min_size=1).filter(lambda x: x.isidentifier()), min_size=1, max_size=10, unique=True)
)
def test_fields_returns_all_fields(field_names):
    import keyword
    for name in field_names:
        assume(not keyword.iskeyword(name))
    
    field_list = [(name, int) for name in field_names]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    retrieved_fields = fields(cls)
    retrieved_names = {f.name for f in retrieved_fields}
    
    assert retrieved_names == set(field_names)


@given(
    st.dictionaries(
        st.text(min_size=1).filter(lambda x: x.isidentifier()),
        st.one_of(st.integers(), st.text()),
        min_size=1,
        max_size=10
    )
)
def test_asdict_with_dict_factory(field_dict):
    import keyword
    for name in field_dict:
        assume(not keyword.iskeyword(name))
    
    field_list = [(name, type(val)) for name, val in field_dict.items()]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**field_dict)
    
    from collections import OrderedDict
    result = asdict(instance, dict_factory=OrderedDict)
    
    assert isinstance(result, OrderedDict)
    assert dict(result) == field_dict


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1).filter(lambda x: x.isidentifier()),
            st.lists(st.integers(), min_size=0, max_size=5)
        ),
        min_size=1,
        max_size=5,
        unique_by=lambda x: x[0]
    )
)
def test_asdict_with_nested_lists(field_values):
    import keyword
    for name, _ in field_values:
        assume(not keyword.iskeyword(name))
    
    field_list = [(name, list) for name, _ in field_values]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**{name: val[:] for name, val in field_values})
    
    dict_result = asdict(instance)
    
    for name, original_list in field_values:
        result_list = dict_result[name]
        assert result_list == original_list
        assert result_list is not getattr(instance, name)
        
        result_list.append(999999)
        assert getattr(instance, name) != result_list


if __name__ == "__main__":
    import keyword
    pytest.main([__file__, "-v", "--tb=short"])