import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import inspect
import coremltools.converters as converters

# Get source location of these classes
print("=== Source Files ===")
for cls_name in ['Shape', 'RangeDim', 'TensorType', 'ImageType']:
    cls = getattr(converters, cls_name)
    try:
        source_file = inspect.getfile(cls)
        print(f"{cls_name}: {source_file}")
    except:
        print(f"{cls_name}: Could not get source file")

# Get methods and attributes of Shape class
print("\n=== Shape Class Methods ===")
shape_cls = converters.Shape
for name, method in inspect.getmembers(shape_cls):
    if not name.startswith('_') and callable(method):
        print(f"  {name}")
        try:
            sig = inspect.signature(method)
            print(f"    Signature: {sig}")
        except:
            pass

# Same for RangeDim
print("\n=== RangeDim Class Methods ===")
rangedim_cls = converters.RangeDim
for name, method in inspect.getmembers(rangedim_cls):
    if not name.startswith('_') and callable(method):
        print(f"  {name}")
        try:
            sig = inspect.signature(method)
            print(f"    Signature: {sig}")
        except:
            pass

# Check for initialization and validation
print("\n=== Testing Basic Construction ===")
try:
    # Try creating a Shape
    shape = converters.Shape(shape=(1, 2, 3))
    print(f"Shape created: {shape}")
    print(f"Shape type: {type(shape)}")
    print(f"Shape attributes: {dir(shape)[:10]}...")
except Exception as e:
    print(f"Failed to create Shape: {e}")

try:
    # Try creating a RangeDim
    dim = converters.RangeDim()
    print(f"RangeDim created: {dim}")
except Exception as e:
    print(f"Failed to create RangeDim: {e}")