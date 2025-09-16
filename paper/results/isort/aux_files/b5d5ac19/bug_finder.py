#!/usr/bin/env python3
"""
Bug finder for isort.main using property-based testing insights
"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.main
from isort.settings import Config
from isort.wrap_modes import WrapModes
import traceback

bugs_found = []

def test_negative_line_length():
    """Test if parse_args accepts negative line_length (which doesn't make sense)"""
    print("\n[TEST] Negative line_length...")
    try:
        result = isort.main.parse_args(["--line-length", "-10"])
        if result.get('line_length', 0) < 0:
            bug = {
                'type': 'Logic',
                'severity': 'Medium',
                'description': 'parse_args accepts negative line_length values',
                'test_input': '--line-length -10',
                'result': result.get('line_length')
            }
            bugs_found.append(bug)
            print(f"BUG FOUND: Negative line_length accepted: {result.get('line_length')}")
            
            # Check if Config also accepts it
            try:
                config = Config(line_length=-10)
                print(f"  Config also accepted negative line_length!")
                bug['description'] += ' and Config accepts it too'
                bug['severity'] = 'High'
            except Exception as e:
                print(f"  Config rejected it: {e}")
            return True
        else:
            print("✓ No bug found")
            return False
    except Exception as e:
        print(f"✓ Rejected with error: {e}")
        return False

def test_negative_wrap_length():
    """Test if parse_args accepts negative wrap_length"""
    print("\n[TEST] Negative wrap_length...")
    try:
        result = isort.main.parse_args(["--wrap-length", "-5"])
        if result.get('wrap_length', 0) < 0:
            bug = {
                'type': 'Logic',
                'severity': 'Medium',
                'description': 'parse_args accepts negative wrap_length values',
                'test_input': '--wrap-length -5',
                'result': result.get('wrap_length')
            }
            bugs_found.append(bug)
            print(f"BUG FOUND: Negative wrap_length accepted: {result.get('wrap_length')}")
            
            # Check if Config accepts it
            try:
                config = Config(wrap_length=-5)
                print(f"  Config also accepted negative wrap_length!")
                bug['severity'] = 'High'
            except Exception as e:
                print(f"  Config rejected it: {e}")
            return True
        else:
            print("✓ No bug found")
            return False
    except Exception as e:
        print(f"✓ Rejected with error: {e}")
        return False

def test_invalid_multi_line_output():
    """Test if parse_args handles invalid multi_line_output values properly"""
    print("\n[TEST] Invalid multi_line_output integer...")
    try:
        # Try a very large integer that's definitely out of range
        result = isort.main.parse_args(["--multi-line", "999"])
        if "multi_line_output" in result:
            print(f"parse_args result: {result['multi_line_output']}")
            try:
                # Check if it's a valid WrapModes value
                mode_value = result['multi_line_output']
                print(f"  Type: {type(mode_value)}, Value: {mode_value}")
                if isinstance(mode_value, WrapModes):
                    # Check if the value is actually valid
                    print(f"  WrapModes value: {mode_value.value}, name: {mode_value.name}")
            except Exception as e:
                bug = {
                    'type': 'Crash',
                    'severity': 'Medium',
                    'description': 'Invalid multi_line_output value causes unexpected behavior',
                    'test_input': '--multi-line 999',
                    'error': str(e)
                }
                bugs_found.append(bug)
                print(f"BUG FOUND: Invalid handling of multi_line_output: {e}")
                return True
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")
        return False
    except Exception as e:
        print(f"Error during test: {e}")
        traceback.print_exc()
        return False
    
    print("✓ No bug found")
    return False

def test_zero_line_length():
    """Test if parse_args/Config accept zero line_length"""
    print("\n[TEST] Zero line_length...")
    try:
        result = isort.main.parse_args(["--line-length", "0"])
        if result.get('line_length') == 0:
            print(f"parse_args accepted line_length=0")
            
            # Check if Config accepts it
            try:
                config = Config(line_length=0)
                bug = {
                    'type': 'Logic',
                    'severity': 'Medium',
                    'description': 'parse_args and Config accept line_length=0 which makes no logical sense',
                    'test_input': '--line-length 0',
                    'result': 0
                }
                bugs_found.append(bug)
                print(f"BUG FOUND: Zero line_length accepted by both parse_args and Config!")
                return True
            except Exception as e:
                print(f"  Config rejected it: {e}")
                # Still a minor issue if parse_args accepts it
                bug = {
                    'type': 'Logic',
                    'severity': 'Low',
                    'description': 'parse_args accepts line_length=0 but Config rejects it',
                    'test_input': '--line-length 0',
                    'result': 0
                }
                bugs_found.append(bug)
                return True
        else:
            print("✓ No bug found")
            return False
    except Exception as e:
        print(f"✓ Rejected with error: {e}")
        return False

def test_jobs_zero():
    """Test if parse_args handles --jobs 0 correctly"""
    print("\n[TEST] Zero jobs value...")
    try:
        result = isort.main.parse_args(["--jobs", "0"])
        jobs_value = result.get('jobs')
        print(f"jobs value: {jobs_value}")
        
        # jobs=0 might be problematic as it could mean no parallelism at all
        if jobs_value == 0:
            print("Note: --jobs 0 is accepted, which might cause issues in multiprocessing.Pool()")
            # This could be a potential issue but needs further investigation
        
        print("✓ No obvious bug")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_contradictory_length_args():
    """Test parse_args with wrap_length > line_length"""
    print("\n[TEST] Contradictory length arguments (wrap_length > line_length)...")
    try:
        result = isort.main.parse_args(["--line-length", "50", "--wrap-length", "100"])
        print(f"parse_args accepted: line_length={result.get('line_length')}, wrap_length={result.get('wrap_length')}")
        
        # This should be caught by Config
        try:
            config = Config(**result)
            bug = {
                'type': 'Logic',
                'severity': 'High',
                'description': 'Config failed to validate wrap_length > line_length constraint',
                'test_input': '--line-length 50 --wrap-length 100',
                'result': f"line_length={result.get('line_length')}, wrap_length={result.get('wrap_length')}"
            }
            bugs_found.append(bug)
            print(f"BUG FOUND: Config accepted wrap_length > line_length!")
            return True
        except ValueError as e:
            if "wrap_length must be set lower than or equal to line_length" in str(e):
                print(f"✓ Config correctly rejected: {e}")
            else:
                print(f"Config rejected with unexpected error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_extreme_values():
    """Test parse_args with extremely large values"""
    print("\n[TEST] Extremely large line_length...")
    try:
        # Test with a very large number
        result = isort.main.parse_args(["--line-length", str(10**10)])
        if result.get('line_length') == 10**10:
            print(f"parse_args accepted extremely large line_length: {result.get('line_length')}")
            # This might not be a bug per se, but could be impractical
            print("Note: Extremely large line_length values are accepted")
        
        print("✓ No critical bug")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# Run all tests
print("=" * 60)
print("Bug Finder for isort.main")
print("=" * 60)

test_negative_line_length()
test_negative_wrap_length()
test_zero_line_length()
test_invalid_multi_line_output()
test_jobs_zero()
test_contradictory_length_args()
test_extreme_values()

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if bugs_found:
    print(f"\nFound {len(bugs_found)} potential bug(s):\n")
    for i, bug in enumerate(bugs_found, 1):
        print(f"{i}. [{bug['severity']}] {bug['type']}: {bug['description']}")
        print(f"   Test input: {bug['test_input']}")
        if 'result' in bug:
            print(f"   Result: {bug['result']}")
        if 'error' in bug:
            print(f"   Error: {bug['error']}")
        print()
else:
    print("\nNo bugs found in the tested properties.")

print("Testing complete!")