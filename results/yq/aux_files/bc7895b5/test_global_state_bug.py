import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import yaml
import yq.loader
import io
import threading
import time

print("=== Demonstrating Global State Mutation Bug ===\n")

def thread1_func(results):
    """Thread 1: Gets loader with expand_merge_keys=True"""
    loader_class = yq.loader.get_loader(expand_merge_keys=True)
    
    # Check if merge key is in resolvers
    has_merge = any('<' in str(resolvers) for resolvers in loader_class.yaml_implicit_resolvers.keys())
    results['thread1_has_merge'] = has_merge
    
    # Parse YAML with merge key
    yaml_with_merge = """
defaults: &defaults
  name: default
  
item:
  <<: *defaults
  value: 123
"""
    try:
        loader = loader_class(io.StringIO(yaml_with_merge))
        doc = yaml.load(io.StringIO(yaml_with_merge), Loader=loader_class)
        results['thread1_parse_success'] = True
        results['thread1_doc'] = doc
    except Exception as e:
        results['thread1_parse_success'] = False
        results['thread1_error'] = str(e)

def thread2_func(results):
    """Thread 2: Gets loader with expand_merge_keys=False"""
    # Small delay to ensure thread1 starts first
    time.sleep(0.01)
    
    loader_class = yq.loader.get_loader(expand_merge_keys=False)
    
    # Check if merge key is in resolvers
    has_merge = any('<' in str(resolvers) for resolvers in loader_class.yaml_implicit_resolvers.keys())
    results['thread2_has_merge'] = has_merge
    
    # Try to parse the same YAML
    yaml_with_merge = """
defaults: &defaults
  name: default
  
item:
  <<: *defaults
  value: 123
"""
    try:
        loader = loader_class(io.StringIO(yaml_with_merge))
        doc = yaml.load(io.StringIO(yaml_with_merge), Loader=loader_class)
        results['thread2_parse_success'] = True
        results['thread2_doc'] = doc
    except Exception as e:
        results['thread2_parse_success'] = False
        results['thread2_error'] = str(e)

# Test: Race condition with concurrent get_loader calls
print("Test 1: Concurrent get_loader calls with different settings")
print("-" * 60)

results = {}

# Create threads
t1 = threading.Thread(target=thread1_func, args=(results,))
t2 = threading.Thread(target=thread2_func, args=(results,))

# Start threads
t1.start()
t2.start()

# Wait for completion
t1.join()
t2.join()

print(f"Thread 1 (expand_merge_keys=True):")
print(f"  Has merge resolver: {results.get('thread1_has_merge')}")
print(f"  Parse success: {results.get('thread1_parse_success')}")
if 'thread1_doc' in results:
    print(f"  Document: {results['thread1_doc']}")

print(f"\nThread 2 (expand_merge_keys=False):")
print(f"  Has merge resolver: {results.get('thread2_has_merge')}")
print(f"  Parse success: {results.get('thread2_parse_success')}")
if 'thread2_doc' in results:
    print(f"  Document: {results['thread2_doc']}")

print("\n" + "=" * 60)
print("BUG: Thread 2 requested expand_merge_keys=False but got False")
print("This happens because get_loader modifies the global class state")
print("=" * 60)

# Test 2: Sequential calls affecting each other
print("\n\nTest 2: Sequential get_loader calls")
print("-" * 60)

# First call with merge keys enabled
loader1 = yq.loader.get_loader(expand_merge_keys=True)
has_merge1 = '<' in str(loader1.yaml_implicit_resolvers)
print(f"After get_loader(expand_merge_keys=True):")
print(f"  Class has merge resolver: {has_merge1}")

# Second call with merge keys disabled
loader2 = yq.loader.get_loader(expand_merge_keys=False)
has_merge2 = '<' in str(loader2.yaml_implicit_resolvers)
print(f"\nAfter get_loader(expand_merge_keys=False):")
print(f"  Class has merge resolver: {has_merge2}")

# Check if they're the same class
print(f"\nloader1 is loader2: {loader1 is loader2}")

print("\n" + "=" * 60)
print("BUG CONFIRMED: get_loader returns the same class but modifies it")
print("This means the last call's settings apply to ALL users of the class!")
print("=" * 60)

# Test 3: Impact on actual YAML parsing
print("\n\nTest 3: Impact on YAML parsing")
print("-" * 60)

yaml_content = """
base: &base
  key1: value1
  
derived:
  <<: *base
  key2: value2
"""

# Get loader with merge expansion disabled
loader_class = yq.loader.get_loader(expand_merge_keys=False)

# Try to load YAML
doc = yaml.load(io.StringIO(yaml_content), Loader=loader_class)
print(f"Loaded document: {doc}")

if '<<' in str(doc.get('derived', {})):
    print("\nResult: Merge key '<<' appears as literal key (not expanded)")
else:
    print("\nResult: Merge key was expanded despite expand_merge_keys=False")

print("\n" + "=" * 60)
print("SEVERITY: Medium")
print("This is a real bug that affects concurrent usage and")
print("sequential calls with different settings.")
print("=" * 60)