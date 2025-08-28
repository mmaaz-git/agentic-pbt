"""Property-based test that reveals the LookupDict bug."""
from hypothesis import given, strategies as st
import requests.status_codes


def test_lookupdict_attribute_consistency():
    """
    Property: For a dict-like object, obj[key] should be consistent with 
    getattr(obj, key) when key is a string representing an attribute name.
    
    This test reveals a bug in LookupDict where inherited dict methods
    return None via __getitem__ but return the actual method via getattr.
    """
    codes = requests.status_codes.codes
    
    # Test all attributes accessible via dir()
    failing_attrs = []
    for attr in dir(codes):
        if not attr.startswith('_'):
            dict_access = codes[attr]
            attr_access = getattr(codes, attr)
            
            if dict_access != attr_access:
                failing_attrs.append((attr, dict_access, attr_access))
    
    if failing_attrs:
        print(f"Found {len(failing_attrs)} inconsistencies:")
        for attr, dict_val, attr_val in failing_attrs[:5]:  # Show first 5
            print(f"  codes['{attr}'] = {dict_val}")
            print(f"  getattr(codes, '{attr}') = {attr_val}")
        
        # This is the actual assertion that fails
        first_attr, dict_val, attr_val = failing_attrs[0]
        assert dict_val == attr_val, \
            f"Inconsistency: codes['{first_attr}'] returns {dict_val} but getattr returns {attr_val}"


if __name__ == "__main__":
    test_lookupdict_attribute_consistency()