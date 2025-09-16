"""
Focused test to demonstrate the bug in LookupDict where __getitem__ 
and get() use __dict__ instead of the parent dict's storage.
"""

from requests.structures import LookupDict


def test_lookupdict_dict_operations_broken():
    """Demonstrate that LookupDict breaks basic dict operations."""
    ld = LookupDict(name="test")
    
    # Set a value using dict's setitem
    ld["key1"] = "value1"
    
    # Basic dict operations work
    assert "key1" in ld  # Works - uses dict's __contains__
    assert len(ld) == 1  # Works - uses dict's __len__
    assert list(ld.keys()) == ["key1"]  # Works - uses dict's keys()
    
    # But __getitem__ is broken!
    assert ld["key1"] is None  # BUG: Returns None instead of "value1"!
    
    # And get() is also broken!
    assert ld.get("key1") is None  # BUG: Returns None instead of "value1"!
    
    # The value is actually there in the parent dict
    assert dict.__getitem__(ld, "key1") == "value1"  # This works
    
    # This breaks the contract of a dict subclass


def test_lookupdict_inconsistent_behavior():
    """Show the inconsistency between different dict operations."""
    ld = LookupDict(name="test") 
    
    # Add items as a normal dict
    ld["status"] = 200
    ld["message"] = "OK"
    
    # Dict says it has the items
    assert "status" in ld
    assert "message" in ld
    assert len(ld) == 2
    assert set(ld.keys()) == {"status", "message"}
    
    # But can't retrieve them!
    assert ld["status"] is None  # Should be 200
    assert ld["message"] is None  # Should be "OK"
    
    # Standard dict iteration works
    for key in ld:
        value = ld[key]
        assert value is None  # All values appear as None!
    
    # This violates the dict contract where if `key in dict`, 
    # then `dict[key]` should return the value, not None


def test_lookupdict_update_broken():
    """Show that update() is also affected."""
    ld = LookupDict(name="test")
    
    # Update with a dict
    ld.update({"key1": "value1", "key2": "value2"})
    
    # Items are in the dict
    assert len(ld) == 2
    assert "key1" in ld
    assert "key2" in ld
    
    # But can't access them
    assert ld["key1"] is None  # Should be "value1"  
    assert ld["key2"] is None  # Should be "value2"
    
    # This makes LookupDict unusable as a normal dict


def test_lookupdict_real_world_usage():
    """Test how LookupDict is actually used in requests."""
    # This is how it's used in requests.status_codes
    codes = LookupDict(name="status_codes")
    
    # Set via attributes (like _init does)
    codes.ok = 200
    codes.not_found = 404
    
    # These work
    assert codes["ok"] == 200
    assert codes["not_found"] == 404
    
    # But if someone tries to use it as a dict...
    codes["custom_status"] = 999
    
    # It's in the dict
    assert "custom_status" in codes
    assert len(codes) == 1  # Only counts dict items, not attributes!
    
    # But can't access it
    assert codes["custom_status"] is None  # BUG: Should be 999!
    
    # This shows LookupDict only works when used exactly as intended
    # (setting via attributes), but fails for normal dict operations


if __name__ == "__main__":
    print("Testing LookupDict bugs...")
    
    test_lookupdict_dict_operations_broken()
    print("✗ test_lookupdict_dict_operations_broken: Dict operations are broken")
    
    test_lookupdict_inconsistent_behavior()
    print("✗ test_lookupdict_inconsistent_behavior: Inconsistent behavior found")
    
    test_lookupdict_update_broken()
    print("✗ test_lookupdict_update_broken: Update is broken")
    
    test_lookupdict_real_world_usage()
    print("✗ test_lookupdict_real_world_usage: Mixed usage fails")
    
    print("\nAll tests demonstrate the bug in LookupDict!")