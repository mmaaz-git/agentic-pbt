#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

# Run the tests manually
from test_praw_properties import *

if __name__ == "__main__":
    print("Running property-based tests for praw...")
    
    # Test 1: Idempotence
    print("\n1. Testing camel_to_snake idempotence...")
    try:
        test_camel_to_snake_idempotence()
        print("✓ Idempotence test passed")
    except Exception as e:
        print(f"✗ Idempotence test failed: {e}")
    
    # Test 2: Output format
    print("\n2. Testing camel_to_snake output format...")
    try:
        test_camel_to_snake_output_format()
        print("✓ Output format test passed")
    except Exception as e:
        print(f"✗ Output format test failed: {e}")
    
    # Test 3: Dictionary size preservation
    print("\n3. Testing snake_case_keys preserves size...")
    try:
        test_snake_case_keys_preserves_size()
        print("✓ Dictionary size preservation test passed")
    except Exception as e:
        print(f"✗ Dictionary size test failed: {e}")
    
    # Test 4: Dictionary values preservation
    print("\n4. Testing snake_case_keys preserves values...")
    try:
        test_snake_case_keys_preserves_values()
        print("✓ Dictionary values preservation test passed")
    except Exception as e:
        print(f"✗ Dictionary values test failed: {e}")
    
    # Test 5: Dictionary idempotence
    print("\n5. Testing snake_case_keys idempotence...")
    try:
        test_snake_case_keys_idempotence()
        print("✓ Dictionary idempotence test passed")
    except Exception as e:
        print(f"✗ Dictionary idempotence test failed: {e}")
    
    # Test 6: Acronym handling
    print("\n6. Testing acronym handling...")
    try:
        test_camel_to_snake_handles_acronyms()
        print("✓ Acronym handling test passed")
    except Exception as e:
        print(f"✗ Acronym handling test failed: {e}")
    
    # Test 7: Edge cases
    print("\n7. Testing edge cases...")
    try:
        test_camel_to_snake_edge_cases()
        print("✓ Edge cases test passed")
    except Exception as e:
        print(f"✗ Edge cases test failed: {e}")
    
    # Test 8: Collision handling
    print("\n8. Testing key collision handling...")
    try:
        test_snake_case_keys_collision()
        print("✓ Key collision test passed")
    except Exception as e:
        print(f"✗ Key collision test failed: {e}")
    
    print("\n" + "="*50)
    print("Test run complete!")