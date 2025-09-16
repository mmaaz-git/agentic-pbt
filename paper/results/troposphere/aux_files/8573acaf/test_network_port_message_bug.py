"""Test for network_port validator error message bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

def test_network_port_error_message_inconsistency():
    """
    Bug: network_port validator accepts -1 as valid but the error message
    says port must be "between 0 and 65535", which excludes -1.
    This is misleading documentation in the error message.
    """
    
    # -1 is accepted as valid
    result = validators.network_port(-1)
    assert result == -1
    
    # 0 is also valid
    result = validators.network_port(0) 
    assert result == 0
    
    # 65535 is valid
    result = validators.network_port(65535)
    assert result == 65535
    
    # -2 is invalid
    try:
        validators.network_port(-2)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        error_msg = str(e)
        # BUG: Error says "between 0 and 65535" but -1 is actually valid
        assert "between 0 and 65535" in error_msg
        print(f"Error message: {error_msg}")
        print("BUG: Error message says 'between 0 and 65535' but -1 is accepted as valid!")
    
    # 65536 is invalid
    try:
        validators.network_port(65536)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        error_msg = str(e)
        assert "between 0 and 65535" in error_msg
    
    print("\nActual valid range: -1 to 65535")
    print("Error message claims: 0 to 65535")
    print("This is a documentation bug in the error message.")

if __name__ == "__main__":
    test_network_port_error_message_inconsistency()
    print("\nTest passed - bug confirmed!")