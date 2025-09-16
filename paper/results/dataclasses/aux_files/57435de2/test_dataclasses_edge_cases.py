import dataclasses
from dataclasses import dataclass, field, asdict, astuple, replace, make_dataclass, fields, is_dataclass, Field, InitVar, KW_ONLY
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import pytest
import keyword
from typing import Any, ClassVar
import sys


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        st.one_of(
            st.integers(),
            st.text(max_size=100),
            st.recursive(
                st.one_of(st.integers(), st.text(max_size=10)),
                lambda children: st.lists(children, max_size=3) | st.dictionaries(st.text(max_size=5), children, max_size=3),
                max_leaves=10
            )
        ),
        min_size=1,
        max_size=5
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow], max_examples=50)
def test_asdict_recursive_structures(field_dict):
    field_list = [(name, type(val)) for name, val in field_dict.items()]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**field_dict)
    
    dict_result = asdict(instance)
    
    def deep_compare(original, copied):
        if isinstance(original, (list, tuple)):
            assert len(original) == len(copied)
            for o, c in zip(original, copied):
                deep_compare(o, c)
            if isinstance(original, list):
                assert original is not copied
        elif isinstance(original, dict):
            assert len(original) == len(copied)
            for key in original:
                assert key in copied
                deep_compare(original[key], copied[key])
            assert original is not copied
        else:
            assert original == copied
    
    for name, val in field_dict.items():
        deep_compare(val, dict_result[name])


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        st.one_of(st.integers(), st.text(max_size=100)),
        min_size=1,
        max_size=10
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_replace_multiple_fields(field_dict):
    if len(field_dict) < 2:
        return
    
    field_list = [(name, type(val)) for name, val in field_dict.items()]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**field_dict)
    
    replacement_dict = {}
    for i, (name, val) in enumerate(field_dict.items()):
        if i < len(field_dict) // 2:
            if isinstance(val, int):
                replacement_dict[name] = val + 1000
            elif isinstance(val, str):
                replacement_dict[name] = val + "_replaced"
    
    if replacement_dict:
        new_instance = replace(instance, **replacement_dict)
        
        for name in field_dict:
            if name in replacement_dict:
                assert getattr(new_instance, name) == replacement_dict[name]
            else:
                assert getattr(new_instance, name) == field_dict[name]


@given(st.text(min_size=1, max_size=100))
def test_field_with_default_factory(text):
    @dataclass
    class TestClass:
        items: list = field(default_factory=list)
        text: str = ""
    
    instance1 = TestClass(text=text)
    instance2 = TestClass(text=text)
    
    instance1.items.append(1)
    
    assert instance2.items == []
    assert instance1.items == [1]
    
    dict_result = asdict(instance1)
    assert dict_result["items"] == [1]
    assert dict_result["text"] == text


@given(st.integers(), st.text())
def test_init_var_not_in_fields(val, txt):
    @dataclass
    class TestClass:
        value: int
        text: str
        init_only: InitVar[int] = None
        
        def __post_init__(self, init_only):
            if init_only is not None:
                self.value += init_only
    
    instance = TestClass(value=val, text=txt, init_only=10)
    
    field_names = [f.name for f in fields(instance)]
    assert "init_only" not in field_names
    assert "value" in field_names
    assert "text" in field_names
    
    dict_result = asdict(instance)
    assert "init_only" not in dict_result
    assert dict_result["value"] == val + 10
    assert dict_result["text"] == txt


@given(st.integers(), st.text())
def test_class_var_not_in_fields(val, txt):
    @dataclass
    class TestClass:
        value: int
        text: str
        counter: ClassVar[int] = 0
    
    instance = TestClass(value=val, text=txt)
    
    field_names = [f.name for f in fields(instance)]
    assert "counter" not in field_names
    assert "value" in field_names
    assert "text" in field_names
    
    dict_result = asdict(instance)
    assert "counter" not in dict_result
    assert dict_result["value"] == val
    assert dict_result["text"] == txt


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
            st.sampled_from([int, str])
        ),
        min_size=1,
        max_size=5,
        unique_by=lambda x: x[0]
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_fields_metadata(field_specs):
    field_list = []
    metadata_dict = {}
    
    for name, typ in field_specs:
        meta = {"description": f"Field {name}", "index": len(field_list)}
        field_list.append((name, typ, field(metadata=meta)))
        metadata_dict[name] = meta
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    retrieved_fields = fields(cls)
    
    for f in retrieved_fields:
        if f.name in metadata_dict:
            assert f.metadata == metadata_dict[f.name]


@given(st.integers(), st.text())
def test_inheritance_fields(val, txt):
    @dataclass
    class Parent:
        value: int
    
    @dataclass
    class Child(Parent):
        text: str
    
    instance = Child(value=val, text=txt)
    
    field_names = [f.name for f in fields(instance)]
    assert "value" in field_names
    assert "text" in field_names
    
    dict_result = asdict(instance)
    assert dict_result["value"] == val
    assert dict_result["text"] == txt


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x) and x != "self"),
        st.one_of(st.integers(), st.text(max_size=100)),
        min_size=1,
        max_size=5
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_asdict_custom_dict_factory(field_dict):
    field_list = [(name, type(val)) for name, val in field_dict.items()]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**field_dict)
    
    class CustomDict(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.custom_flag = True
    
    dict_result = asdict(instance, dict_factory=CustomDict)
    
    assert isinstance(dict_result, CustomDict)
    assert hasattr(dict_result, 'custom_flag')
    assert dict_result.custom_flag == True
    
    for name, val in field_dict.items():
        assert dict_result[name] == val


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        st.one_of(st.integers(), st.text(max_size=100)),
        min_size=1,
        max_size=5
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_astuple_custom_tuple_factory(field_dict):
    field_list = [(name, type(val)) for name, val in field_dict.items()]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**field_dict)
    
    def custom_tuple_factory(items):
        return list(items)
    
    result = astuple(instance, tuple_factory=custom_tuple_factory)
    
    assert isinstance(result, list)
    assert len(result) == len(field_dict)
    
    field_values = list(field_dict.values())
    for i, val in enumerate(field_values):
        assert result[i] == val


@given(st.integers(), st.text())
def test_field_repr_setting(val, txt):
    @dataclass
    class TestClass:
        value: int
        secret: str = field(repr=False)
    
    instance = TestClass(value=val, secret=txt)
    
    repr_str = repr(instance)
    assert f"value={val}" in repr_str
    assert "secret=" not in repr_str
    assert txt not in repr_str


@given(st.integers(), st.text())
def test_field_compare_setting(val, txt):
    @dataclass
    class TestClass:
        value: int
        ignored: str = field(compare=False)
    
    instance1 = TestClass(value=val, ignored=txt)
    instance2 = TestClass(value=val, ignored=txt + "_different")
    
    assert instance1 == instance2
    
    instance3 = TestClass(value=val + 1, ignored=txt)
    assert instance1 != instance3


@given(
    st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        min_size=1,
        max_size=5,
        unique=True
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_kw_only_fields(field_names):
    if sys.version_info < (3, 10):
        return
    
    field_list = []
    for i, name in enumerate(field_names):
        if i == len(field_names) // 2:
            field_list.append((KW_ONLY, ...))
        field_list.append((name, int, field(default=i)))
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    retrieved_fields = fields(cls)
    
    kw_only_start = len(field_names) // 2
    for i, f in enumerate(retrieved_fields):
        if i >= kw_only_start:
            assert f.kw_only == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])