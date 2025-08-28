#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages/')

from hypothesis import given, strategies as st
import copy
from azure.profiles import ProfileDefinition

@given(
    initial_dict=st.dictionaries(
        keys=st.text(min_size=1, max_size=50).filter(lambda x: '.' in x),
        values=st.dictionaries(
            keys=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
            values=st.text(min_size=1, max_size=30),
            min_size=1,
            max_size=3
        ),
        min_size=1,
        max_size=5
    ),
    label=st.text(min_size=1, max_size=50)
)
def test_profile_definition_encapsulation_violation(initial_dict, label):
    """Property: ProfileDefinition should not allow external modification of its internal state."""
    
    # Make a deep copy to track the original state
    original_state = copy.deepcopy(initial_dict)
    
    # Create ProfileDefinition
    profile = ProfileDefinition(initial_dict, label)
    
    # Get the dict
    returned_dict = profile.get_profile_dict()
    
    # Modify the returned dict
    if returned_dict:
        # Add a new key
        returned_dict["INJECTED_KEY"] = {"injected": "value"}
        
        # Get the dict again
        current_dict = profile.get_profile_dict()
        
        # Property violation: The internal state should not have changed
        # but it does because get_profile_dict() returns a reference, not a copy
        assert "INJECTED_KEY" in current_dict, "Bug confirmed: External modification affected internal state"
        
        # Also test that modifying the original input dict affects the profile
        initial_dict["ANOTHER_INJECTION"] = {"also": "injected"}
        final_dict = profile.get_profile_dict()
        
        assert "ANOTHER_INJECTION" in final_dict, "Bug confirmed: Original dict modification affected profile"
        
        # This demonstrates that ProfileDefinition violates encapsulation
        # The internal state can be modified from outside
        
        print(f"✓ Confirmed encapsulation violation with dict containing {len(initial_dict)} keys")


if __name__ == "__main__":
    # Run the property test
    test_profile_definition_encapsulation_violation()
    print("\nEncapsulation violation confirmed across multiple test cases")