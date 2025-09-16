from sqlalchemy.ext.orderinglist import OrderingList, ordering_list

class Item:
    def __init__(self, value):
        self.value = value
        self.position = None
    
    def __repr__(self):
        return f"Item({self.value})"

factory = ordering_list("position")

# Test 1: Regular list behavior
print("Test 1: Regular Python list slice replacement")
regular_list = [Item(1), Item(2), Item(3)]
print(f"Before: {regular_list}")
regular_list[1:2] = [Item(10), Item(20)]
print(f"After:  {regular_list}")
print(f"Length: {len(regular_list)}")

# Test 2: OrderingList behavior  
print("\nTest 2: OrderingList slice replacement")
olist = factory()
olist.append(Item(1))
olist.append(Item(2))
olist.append(Item(3))
print(f"Before: {list(olist)}")
olist[1:2] = [Item(10), Item(20)]
print(f"After:  {list(olist)}")
print(f"Length: {len(olist)}")

# Test 3: Check if __setitem__ is overridden
print("\nTest 3: Check if __setitem__ is overridden")
print(f"OrderingList has custom __setitem__: {hasattr(OrderingList, '__setitem__')}")
if hasattr(OrderingList, '__setitem__'):
    import inspect
    print("Source:")
    print(inspect.getsource(OrderingList.__setitem__))