from sqlalchemy.ext.orderinglist import OrderingList, count_from_0

# Create mock objects with position attribute
class Item:
    def __init__(self, value):
        self.value = value
        self.position = None
    
    def __repr__(self):
        return f"Item(value={self.value}, position={self.position})"

# Test 1: Using extend()
print("Test 1: Using extend()")
objects1 = [Item(i) for i in range(3)]
olist1 = OrderingList('position', count_from_0)
olist1.extend(objects1)

print("After extend():")
for obj in olist1:
    print(f"  {obj}")

# Test 2: Using append() multiple times
print("\nTest 2: Using append() multiple times")
objects2 = [Item(i) for i in range(3)]
olist2 = OrderingList('position', count_from_0)
for obj in objects2:
    olist2.append(obj)

print("After multiple append():")
for obj in olist2:
    print(f"  {obj}")

# Test 3: Check what methods OrderingList overrides
print("\nTest 3: Check OrderingList methods")
print("OrderingList overrides these list methods:")
for method in dir(OrderingList):
    if not method.startswith('_') and hasattr(list, method):
        if getattr(OrderingList, method) is not getattr(list, method):
            print(f"  - {method}")