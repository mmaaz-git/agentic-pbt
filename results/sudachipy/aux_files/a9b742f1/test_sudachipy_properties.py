#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import sudachipy
from sudachipy import config

# Test 1: Config._filter_nulls removes all None values
@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.one_of(st.none(), st.text(), st.integers(), st.booleans()),
    min_size=0, max_size=10
))
def test_config_filter_nulls_removes_all_nones(data):
    filtered = config._filter_nulls(data.copy())
    assert None not in filtered.values()
    assert all(k in data for k in filtered.keys())
    assert all(filtered[k] == data[k] for k in filtered.keys())
    assert len([v for v in data.values() if v is not None]) == len(filtered)

# Test 2: Config.as_jsons() produces valid JSON
@given(
    system=st.one_of(st.none(), st.text(min_size=1)),
    user=st.one_of(st.none(), st.lists(st.text(min_size=1), max_size=14)),
    projection=st.one_of(
        st.none(), 
        st.sampled_from(["surface", "normalized", "reading", "dictionary", 
                        "dictionary_and_surface", "normalized_and_surface", "normalized_nouns"])
    )
)
def test_config_as_jsons_produces_valid_json(system, user, projection):
    cfg = config.Config(
        system=system,
        user=user,
        projection=projection if projection else "surface"
    )
    json_str = cfg.as_jsons()
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    if system is not None:
        assert parsed.get("system") == system
    if user is not None:
        assert parsed.get("user") == user
    if projection and projection != "surface":
        assert parsed.get("projection") == projection

# Test 3: Config.update preserves unmodified fields
@given(
    initial_system=st.one_of(st.none(), st.text(min_size=1)),
    initial_user=st.one_of(st.none(), st.lists(st.text(min_size=1), max_size=14)),
    new_system=st.text(min_size=1)
)
def test_config_update_preserves_fields(initial_system, initial_user, new_system):
    cfg = config.Config(system=initial_system, user=initial_user)
    updated = cfg.update(system=new_system)
    
    assert updated.system == new_system
    assert updated.user == initial_user
    assert cfg.system == initial_system  # Original unchanged

# Test 4: _find_dict_path validates dict_type
@given(st.text(min_size=1))
def test_find_dict_path_validates_dict_type(dict_type):
    if dict_type not in ['small', 'core', 'full']:
        try:
            sudachipy._find_dict_path(dict_type)
            assert False, f"Should have raised ValueError for {dict_type}"
        except ValueError as e:
            assert '"dict_type" must be' in str(e)
        except ModuleNotFoundError:
            pass  # This is acceptable if the module doesn't exist

# Test 5: JSON round-trip property for Config
@given(
    st.dictionaries(
        st.sampled_from(["system", "user", "projection", "connectionCostPlugin", 
                        "oovProviderPlugin", "pathRewritePlugin", "inputTextPlugin", 
                        "characterDefinitionFile"]),
        st.one_of(
            st.none(),
            st.text(min_size=0, max_size=100),
            st.lists(st.text(min_size=1, max_size=20), max_size=5)
        ),
        min_size=0,
        max_size=8
    )
)
def test_config_json_roundtrip(config_dict):
    # Filter to valid field combinations
    if "user" in config_dict and config_dict["user"] is not None:
        if not isinstance(config_dict["user"], list):
            config_dict["user"] = [config_dict["user"]]
        config_dict["user"] = config_dict["user"][:14]  # Max 14 user dicts
    
    if "projection" not in config_dict or config_dict["projection"] is None:
        config_dict["projection"] = "surface"
    
    cfg = config.Config(**config_dict)
    json_str = cfg.as_jsons()
    parsed = json.loads(json_str)
    
    # Check that non-None values are preserved
    for key, value in config_dict.items():
        if value is not None:
            assert key in parsed
            assert parsed[key] == value

# Test 6: Config dataclass field access
@given(
    system=st.one_of(st.none(), st.text()),
    user=st.one_of(st.none(), st.lists(st.text(), max_size=14))
)
def test_config_field_access(system, user):
    cfg = config.Config(system=system, user=user)
    assert cfg.system == system
    assert cfg.user == user
    assert hasattr(cfg, 'projection')
    assert cfg.projection == "surface"  # Default value