import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.location import inside


class ObjectWithoutParent:
    def __init__(self):
        pass


obj1 = ObjectWithoutParent()
obj2 = ObjectWithoutParent()

try:
    result = inside(obj1, obj2)
    print(f"Result: {result}")
except AttributeError as e:
    print(f"BUG: inside() crashes with AttributeError when object lacks __parent__")
    print(f"Error: {e}")
    
print("\nCompare with lineage() which handles this case:")
from pyramid.location import lineage

lineage_list = list(lineage(obj1))
print(f"lineage() result: {lineage_list}")
print("lineage() properly handles missing __parent__ attribute")