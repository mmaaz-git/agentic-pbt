"""Property-based tests for isort.profiles module"""
import sys
import os
import copy
from hypothesis import given, strategies as st, settings, assume

# Add the isort environment to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.profiles


def test_profile_immutability_after_copy():
    """Test that profiles remain immutable when accessed via .copy()
    
    This property is claimed by the code in settings.py:367 where it calls
    profiles[profile_name].copy() to prevent mutation of the original profile.
    """
    for profile_name, profile in isort.profiles.profiles.items():
        original_profile = copy.deepcopy(profile)
        profile_copy = profile.copy()
        
        # Mutate the copy
        profile_copy['test_key'] = 'test_value'
        if 'line_length' in profile_copy:
            profile_copy['line_length'] = 999999
        
        # Original should remain unchanged
        assert profile == original_profile, f"Profile {profile_name} was mutated"
        assert 'test_key' not in profile, f"Profile {profile_name} gained unexpected key"


def test_plone_profile_inherits_from_black():
    """Test that plone profile correctly inherits from black profile
    
    The code explicitly shows: plone = black.copy() followed by plone.update()
    This means plone should have all black's keys plus its own.
    """
    black = isort.profiles.black
    plone = isort.profiles.plone
    
    # Plone should have all keys from black
    for key in black:
        if key not in ['force_alphabetical_sort', 'force_single_line', 'lines_after_imports']:
            # These are the keys that plone explicitly overrides
            assert key in plone, f"Plone profile missing black key: {key}"
    
    # Plone should have its specific overrides
    assert plone.get('force_alphabetical_sort') == True
    assert plone.get('force_single_line') == True
    assert plone.get('lines_after_imports') == 2


def test_appnexus_profile_expands_black():
    """Test that appnexus profile correctly expands from black using **black
    
    The code shows: appnexus = {**black, ...} which should merge dictionaries
    """
    black = isort.profiles.black
    appnexus = isort.profiles.appnexus
    
    # Appnexus should have all keys from black (unless explicitly overridden)
    for key in black:
        assert key in appnexus, f"Appnexus profile missing black key: {key}"
    
    # Verify appnexus-specific settings exist
    assert 'force_sort_within_sections' in appnexus
    assert 'order_by_type' in appnexus
    assert 'case_sensitive' in appnexus
    assert 'reverse_relative' in appnexus
    assert 'sort_relative_in_force_sorted_sections' in appnexus
    assert 'sections' in appnexus
    assert 'no_lines_before' in appnexus


def test_profiles_dict_completeness():
    """Test that all defined profiles are in the profiles dictionary
    
    The module defines individual profile variables and then collects them
    in a profiles dict. They should all be present.
    """
    # All individual profile variables should be in the profiles dict
    expected_profiles = {
        'black', 'django', 'pycharm', 'google', 'open_stack', 
        'plone', 'attrs', 'hug', 'wemake', 'appnexus'
    }
    
    actual_profiles = set(isort.profiles.profiles.keys())
    
    assert expected_profiles == actual_profiles, \
        f"Profile mismatch. Expected: {expected_profiles}, Got: {actual_profiles}"
    
    # Each profile in the dict should reference the same object as the module variable
    assert isort.profiles.profiles['black'] is isort.profiles.black
    assert isort.profiles.profiles['django'] is isort.profiles.django
    assert isort.profiles.profiles['pycharm'] is isort.profiles.pycharm
    assert isort.profiles.profiles['google'] is isort.profiles.google
    assert isort.profiles.profiles['open_stack'] is isort.profiles.open_stack
    assert isort.profiles.profiles['plone'] is isort.profiles.plone
    assert isort.profiles.profiles['attrs'] is isort.profiles.attrs
    assert isort.profiles.profiles['hug'] is isort.profiles.hug
    assert isort.profiles.profiles['wemake'] is isort.profiles.wemake
    assert isort.profiles.profiles['appnexus'] is isort.profiles.appnexus


@given(st.text(min_size=1, max_size=20).filter(lambda x: x not in isort.profiles.profiles))
def test_setdefault_preserves_existing_profiles(new_profile_name):
    """Test that setdefault doesn't override existing profiles
    
    In settings.py:362, the code uses profiles.setdefault() to add plugin profiles.
    This should not override existing profiles.
    """
    profiles_dict = isort.profiles.profiles.copy()
    
    # Get an existing profile
    existing_name = 'black'
    original_black = profiles_dict[existing_name]
    
    # Try to setdefault with a different value
    new_value = {'completely': 'different'}
    result = profiles_dict.setdefault(existing_name, new_value)
    
    # Should return the existing value, not the new one
    assert result is original_black
    assert profiles_dict[existing_name] is original_black
    assert profiles_dict[existing_name] != new_value
    
    # But setdefault should work for non-existing keys
    result2 = profiles_dict.setdefault(new_profile_name, new_value)
    assert result2 is new_value
    assert profiles_dict[new_profile_name] is new_value


def test_black_copy_independence():
    """Test that black.copy() creates independent dictionaries
    
    The plone profile is created using black.copy(). This tests that
    mutations to plone don't affect black.
    """
    # Store original black profile
    original_black = copy.deepcopy(isort.profiles.black)
    
    # plone was created as black.copy() then updated
    # Let's verify that black wasn't affected by plone's creation
    assert isort.profiles.black == original_black
    
    # Verify plone has its unique settings that black doesn't have
    assert 'force_alphabetical_sort' not in isort.profiles.black
    assert 'force_alphabetical_sort' in isort.profiles.plone
    
    # Verify shared keys have the right values
    if 'line_length' in isort.profiles.black:
        # Black and plone should have the same line_length since plone didn't override it
        assert isort.profiles.black['line_length'] == isort.profiles.plone['line_length']


@given(st.sampled_from(list(isort.profiles.profiles.keys())))
def test_profile_types_consistency(profile_name):
    """Test that profile configuration values have consistent types
    
    Based on how profiles are used in settings.py, certain keys should have
    consistent types across all profiles.
    """
    profile = isort.profiles.profiles[profile_name]
    
    # Check common configuration keys and their expected types
    if 'line_length' in profile:
        assert isinstance(profile['line_length'], int), \
            f"line_length should be int in {profile_name}"
        assert profile['line_length'] > 0, \
            f"line_length should be positive in {profile_name}"
    
    if 'multi_line_output' in profile:
        assert isinstance(profile['multi_line_output'], int), \
            f"multi_line_output should be int in {profile_name}"
    
    if 'force_single_line' in profile:
        assert isinstance(profile['force_single_line'], bool), \
            f"force_single_line should be bool in {profile_name}"
    
    if 'include_trailing_comma' in profile:
        assert isinstance(profile['include_trailing_comma'], bool), \
            f"include_trailing_comma should be bool in {profile_name}"
    
    if 'use_parentheses' in profile:
        assert isinstance(profile['use_parentheses'], bool), \
            f"use_parentheses should be bool in {profile_name}"
    
    if 'sections' in profile:
        assert isinstance(profile['sections'], (list, tuple)), \
            f"sections should be list or tuple in {profile_name}"