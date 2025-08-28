from sqlalchemy.ext.orderinglist import OrderingList, count_from_0

class Item:
    def __init__(self, value):
        self.value = value
        self.position = None
    
    def __repr__(self):
        return f"Item(value={self.value}, position={self.position})"

# Test various list operations
print("Testing various list operations that may not set position:")

# Test 1: extend()
print("\n1. extend():")
olist = OrderingList('position', count_from_0)
items = [Item(i) for i in range(3)]
olist.extend(items)
print(f"  Positions after extend: {[obj.position for obj in olist]}")

# Test 2: += operator
print("\n2. += operator:")
olist2 = OrderingList('position', count_from_0)
items2 = [Item(i) for i in range(3)]
olist2 += items2
print(f"  Positions after +=: {[obj.position for obj in olist2]}")

# Test 3: slice assignment
print("\n3. Slice assignment:")
olist3 = OrderingList('position', count_from_0)
items3 = [Item(i) for i in range(3)]
olist3[:] = items3
print(f"  Positions after slice assignment: {[obj.position for obj in olist3]}")

# Test 4: __setitem__ with slice
print("\n4. __setitem__ with slice:")
olist4 = OrderingList('position', count_from_0)
olist4.append(Item(100))  # Start with one item
olist4.append(Item(101))
olist4.append(Item(102))
print(f"  Initial positions: {[obj.position for obj in olist4]}")
new_items = [Item(200), Item(201)]
olist4[1:2] = new_items  # Replace middle item with two items
print(f"  Positions after slice replacement: {[obj.position for obj in olist4]}")

# Test 5: __init__ with initial list
print("\n5. __init__ with initial list:")
initial_items = [Item(i) for i in range(3)]
olist5 = OrderingList('position', count_from_0)
olist5.extend(initial_items)  # This is essentially what happens if you pass items to __init__
print(f"  Positions after init with items: {[obj.position for obj in olist5]}")

# Test 6: clear() then extend()
print("\n6. clear() then extend():")
olist6 = OrderingList('position', count_from_0)
olist6.append(Item(0))
olist6.append(Item(1))
print(f"  Positions before clear: {[obj.position for obj in olist6]}")
olist6.clear()
new_items6 = [Item(10), Item(11)]
olist6.extend(new_items6)
print(f"  Positions after clear+extend: {[obj.position for obj in olist6]}")