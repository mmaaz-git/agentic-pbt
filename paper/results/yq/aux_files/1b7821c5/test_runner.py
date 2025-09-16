#!/usr/bin/env /root/hypothesis-llm/envs/yq_env/bin/python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import io
import yaml
import traceback
from hypothesis import given, strategies as st, settings, assume
from hypothesis.errors import Flaky
from yq.dumper import get_dumper, OrderedDumper, OrderedIndentlessDumper
from yq.loader import hash_key, get_loader

# Simple test to check basic functionality
def test_basic_functionality():
    print("Testing basic dumper functionality...")
    
    # Test 1: Basic dict dumping
    data = {"key": "value", "number": 42}
    dumper = get_dumper(use_annotations=False, indentless=False, grammar_version="1.1")
    output = io.StringIO()
    yaml.dump(data, output, Dumper=dumper, default_flow_style=False)
    result = output.getvalue()
    print(f"Basic dict dump result: {repr(result)}")
    
    # Test 2: Check annotation filtering
    print("\nTesting annotation filtering...")
    annotated_data = {"key": "value", "__yq_style_abc__": "'"}
    dumper_with_annotations = get_dumper(use_annotations=True, indentless=False, grammar_version="1.1")
    output2 = io.StringIO()
    yaml.dump(annotated_data, output2, Dumper=dumper_with_annotations, default_flow_style=False)
    result2 = output2.getvalue()
    print(f"Annotation test result: {repr(result2)}")
    if "__yq_style_" in result2:
        print("BUG FOUND: Annotation keys not filtered!")
        return False
    
    # Test 3: Hash key function
    print("\nTesting hash_key function...")
    hash1 = hash_key("test")
    hash2 = hash_key("test")
    print(f"hash_key('test') = {hash1}")
    print(f"Consistent? {hash1 == hash2}")
    
    # Test 4: Round trip
    print("\nTesting round trip...")
    test_data = {"a": 1, "b": [1, 2, 3], "c": {"nested": True}}
    dumper = get_dumper(use_annotations=False, indentless=False, grammar_version="1.1")
    loader = get_loader(use_annotations=False, expand_aliases=True, expand_merge_keys=True)
    
    output3 = io.StringIO()
    yaml.dump(test_data, output3, Dumper=dumper, default_flow_style=False)
    output3.seek(0)
    loaded_data = yaml.load(output3, Loader=loader)
    print(f"Original: {test_data}")
    print(f"Loaded: {loaded_data}")
    print(f"Match: {test_data == loaded_data}")
    
    return True

# Run property-based tests with specific examples
def test_with_hypothesis():
    print("\n" + "="*50)
    print("Running property-based tests...")
    
    # Test annotation filtering with specific examples
    print("\nTest: Annotation filtering with dictionaries")
    test_cases = [
        {"key1": "value1", "__yq_style_xyz__": "'"},
        {"a": 1, "b": 2, "__yq_tag_abc__": "!custom"},
        {"nested": {"inner": "data"}, "__yq_style_def__": "flow"}
    ]
    
    for i, test_data in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test_data}")
        dumper = get_dumper(use_annotations=True, indentless=False, grammar_version="1.1")
        output = io.StringIO()
        yaml.dump(test_data, output, Dumper=dumper, default_flow_style=False)
        result = output.getvalue()
        
        if "__yq_style_" in result or "__yq_tag_" in result:
            print(f"FAILURE: Annotation keys found in output!")
            print(f"Output: {repr(result)}")
            return False
        else:
            print(f"PASS: No annotation keys in output")
    
    # Test list annotation filtering
    print("\n\nTest: Annotation filtering with lists")
    test_lists = [
        [1, 2, "__yq_style_0_'__"],
        ["a", "b", "__yq_tag_1_!custom__"],
        [{"key": "value"}, "__yq_style_0_flow__"]
    ]
    
    for i, test_data in enumerate(test_lists):
        print(f"\nTest case {i+1}: {test_data}")
        dumper = get_dumper(use_annotations=True, indentless=False, grammar_version="1.1")
        output = io.StringIO()
        yaml.dump(test_data, output, Dumper=dumper, default_flow_style=False)
        result = output.getvalue()
        
        if "__yq_style_" in result or "__yq_tag_" in result:
            print(f"FAILURE: Annotation items found in output!")
            print(f"Output: {repr(result)}")
            return False
        else:
            print(f"PASS: No annotation items in output")
    
    return True

# Run stress test
def stress_test():
    print("\n" + "="*50)
    print("Running stress tests...")
    
    # Test with deeply nested structure
    deep_data = {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}
    
    for grammar in ["1.1", "1.2"]:
        for indentless in [True, False]:
            for use_annotations in [True, False]:
                try:
                    dumper = get_dumper(
                        use_annotations=use_annotations,
                        indentless=indentless,
                        grammar_version=grammar
                    )
                    output = io.StringIO()
                    yaml.dump(deep_data, output, Dumper=dumper, default_flow_style=False)
                    result = output.getvalue()
                    if not result:
                        print(f"FAILURE: Empty output for grammar={grammar}, indentless={indentless}, annotations={use_annotations}")
                        return False
                except Exception as e:
                    print(f"FAILURE: Exception for grammar={grammar}, indentless={indentless}, annotations={use_annotations}")
                    print(f"  Error: {e}")
                    return False
    
    print("All stress tests passed!")
    return True

if __name__ == "__main__":
    success = True
    
    try:
        if not test_basic_functionality():
            success = False
    except Exception as e:
        print(f"Basic functionality test failed: {e}")
        traceback.print_exc()
        success = False
    
    try:
        if not test_with_hypothesis():
            success = False
    except Exception as e:
        print(f"Property-based tests failed: {e}")
        traceback.print_exc()
        success = False
    
    try:
        if not stress_test():
            success = False
    except Exception as e:
        print(f"Stress tests failed: {e}")
        traceback.print_exc()
        success = False
    
    if success:
        print("\n" + "="*50)
        print("All tests passed! ✅")
    else:
        print("\n" + "="*50)
        print("Some tests failed! ❌")
        sys.exit(1)