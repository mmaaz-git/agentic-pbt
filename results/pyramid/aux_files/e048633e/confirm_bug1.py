#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.predicates import RequestParamPredicate
from unittest.mock import Mock

def test_whitespace_handling():
    """Test that RequestParamPredicate handles whitespace inconsistently"""
    config = Mock()
    
    # Test cases with whitespace
    test_cases = [
        (" key = value ", " key ", " value "),  # spaces around key and value
        ("  =  ", "  ", "  "),                    # only spaces
        (" a = b ", " a ", " b "),                # normal case with spaces
    ]
    
    for param_str, original_key, original_value in test_cases:
        pred = RequestParamPredicate(param_str, config)
        
        # Check what the predicate parsed
        parsed_key, parsed_value = pred.reqs[0]
        
        print(f"\nTest: '{param_str}'")
        print(f"  Original: key='{original_key}', value='{original_value}'")
        print(f"  Parsed:   key='{parsed_key}', value='{parsed_value}'")
        
        context = {}
        request = Mock()
        
        # Test with original (untrimmed) key/value
        request.params = {original_key: original_value}
        result1 = pred(context, request)
        print(f"  With original params: {result1}")
        
        # Test with trimmed key/value
        request.params = {parsed_key: parsed_value}
        result2 = pred(context, request)
        print(f"  With trimmed params: {result2}")
        
        # The bug: predicate strips whitespace during parsing but then
        # looks for the stripped key in request.params
        if result1 == False and result2 == True:
            print(f"  ⚠️  BUG CONFIRMED: Whitespace stripped in parsing but not in matching!")

if __name__ == "__main__":
    test_whitespace_handling()