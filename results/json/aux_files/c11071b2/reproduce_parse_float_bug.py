#!/usr/bin/env python3
"""
Minimal reproduction of parse_float not being called for Infinity/NaN
"""

import json


def test_parse_float_not_called_for_special_values():
    """
    According to the documentation, parse_float "will be called with the string
    of every JSON float to be decoded." However, it's not called for the special
    values Infinity, -Infinity, and NaN.
    """
    
    calls = []
    
    def track_calls(s):
        calls.append(s)
        return float(s)
    
    # Test regular float - parse_float IS called
    calls.clear()
    json.loads('3.14', parse_float=track_calls)
    assert calls == ['3.14'], f"Regular float: parse_float called with {calls}"
    
    # Test Infinity - parse_float is NOT called  
    calls.clear()
    result = json.loads('Infinity', parse_float=track_calls)
    assert calls == [], f"Infinity: parse_float unexpectedly called with {calls}"
    assert result == float('inf')
    
    # Test -Infinity - parse_float is NOT called
    calls.clear() 
    result = json.loads('-Infinity', parse_float=track_calls)
    assert calls == [], f"-Infinity: parse_float unexpectedly called with {calls}"
    assert result == float('-inf')
    
    # Test NaN - parse_float is NOT called
    calls.clear()
    result = json.loads('NaN', parse_float=track_calls)
    assert calls == [], f"NaN: parse_float unexpectedly called with {calls}"
    assert str(result) == 'nan'
    
    print("BUG CONFIRMED: parse_float is not called for Infinity, -Infinity, or NaN")
    print("These values are instead handled by parse_constant")
    
    # Verify parse_constant handles them
    def custom_constant(s):
        return f"CONST_{s}"
    
    assert json.loads('Infinity', parse_constant=custom_constant) == 'CONST_Infinity'
    assert json.loads('-Infinity', parse_constant=custom_constant) == 'CONST_-Infinity'
    assert json.loads('NaN', parse_constant=custom_constant) == 'CONST_NaN'


if __name__ == "__main__":
    test_parse_float_not_called_for_special_values()
    print("\nThis violates the documented behavior that parse_float")
    print("'will be called with the string of every JSON float'")
    print("since Infinity, -Infinity, and NaN are float values in JSON.")