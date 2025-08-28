from sqlalchemy.ext.orderinglist import OrderingList, ordering_list

class Bullet:
    def __init__(self, text):
        self.text = text
        self.position = None
    
    def __repr__(self):
        return f"Bullet('{self.text}', pos={self.position})"

factory = ordering_list("position")
olist = factory()

# Add initial items
olist.append(Bullet("A"))
olist.append(Bullet("B"))
olist.append(Bullet("C"))

print("Initial list:")
for i, b in enumerate(olist):
    print(f"  [{i}] {b}")

print(f"\nLength before: {len(olist)}")

# Replace [1:2] (just "B") with two items
replacement = [Bullet("X"), Bullet("Y")]
print(f"\nReplacing olist[1:2] with {replacement}")
olist[1:2] = replacement

print(f"\nLength after: {len(olist)}")
print("\nFinal list:")
for i, b in enumerate(olist):
    print(f"  [{i}] {b}")

print("\nExpected: A, X, Y, C with positions 0, 1, 2, 3")
print(f"Actual: {', '.join([b.text for b in olist])} with positions {[b.position for b in olist]}")

# Check if X is missing
if len(olist) != 4:
    print("\nBUG: Slice replacement didn't work correctly! One item is missing.")