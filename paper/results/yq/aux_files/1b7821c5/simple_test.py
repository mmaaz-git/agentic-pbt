#!/usr/bin/env /root/hypothesis-llm/envs/yq_env/bin/python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

try:
    import io
    import yaml
    from yq.dumper import get_dumper
    from yq.loader import hash_key, get_loader
    
    print("Testing yq.dumper module...")
    
    # Test 1: Basic functionality
    data = {"key": "value"}
    dumper = get_dumper()
    output = io.StringIO()
    yaml.dump(data, output, Dumper=dumper)
    print(f"✓ Basic test passed: {output.getvalue().strip()}")
    
    # Test 2: Annotation filtering
    data_with_annotations = {
        "real_key": "real_value",
        "__yq_style_abc__": "should_be_filtered"
    }
    dumper = get_dumper(use_annotations=True)
    output = io.StringIO()
    yaml.dump(data_with_annotations, output, Dumper=dumper)
    result = output.getvalue()
    
    if "__yq_style_" in result:
        print("✗ BUG FOUND: Annotation keys not filtered when use_annotations=True")
        print(f"  Input: {data_with_annotations}")
        print(f"  Output: {result}")
    else:
        print("✓ Annotation filtering works correctly")
    
    # Test 3: Hash key
    h1 = hash_key("test")
    h2 = hash_key("test")
    if h1 == h2:
        print(f"✓ hash_key is consistent: {h1}")
    else:
        print(f"✗ BUG: hash_key not consistent: {h1} != {h2}")
    
    print("\nAll tests completed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()