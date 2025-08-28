from sqlalchemy.ext.orderinglist import OrderingList, ordering_list, count_from_0

# Simulate what would happen in a real SQLAlchemy scenario
class Bullet:
    """Simulates a SQLAlchemy model"""
    def __init__(self, text):
        self.text = text
        self.position = None  # This would be a Column in SQLAlchemy
    
    def __repr__(self):
        return f"Bullet(text='{self.text}', position={self.position})"

# This is how ordering_list would be used in a relationship
factory = ordering_list("position")
olist = factory()

print("Realistic scenario: Managing a list of bullets in a slide")
print("=" * 50)

# Scenario 1: User adds bullets one by one (WORKS)
print("\nScenario 1: Adding bullets one by one with append()")
bullet1 = Bullet("Introduction")
bullet2 = Bullet("Main Point")
bullet3 = Bullet("Conclusion")

olist.append(bullet1)
olist.append(bullet2)
olist.append(bullet3)

print("Result:")
for b in olist:
    print(f"  {b}")

# Scenario 2: User wants to bulk-add bullets (FAILS)
print("\nScenario 2: Bulk adding bullets with extend()")
olist2 = factory()
bullets = [
    Bullet("Point A"),
    Bullet("Point B"),
    Bullet("Point C")
]
olist2.extend(bullets)

print("Result:")
for b in olist2:
    print(f"  {b}")
print("BUG: Positions are None instead of 0, 1, 2!")

# Scenario 3: User concatenates lists (FAILS)
print("\nScenario 3: Concatenating lists with +=")
olist3 = factory()
olist3.append(Bullet("First"))
print(f"Before +=: {[b.position for b in olist3]}")

more_bullets = [Bullet("Second"), Bullet("Third")]
olist3 += more_bullets
print(f"After +=: {[b.position for b in olist3]}")
print("BUG: New items have position=None!")

# Scenario 4: User replaces multiple items at once (FAILS)
print("\nScenario 4: Replacing items with slice assignment")
olist4 = factory()
olist4.append(Bullet("A"))
olist4.append(Bullet("B"))
olist4.append(Bullet("C"))
print(f"Before slice: {[(b.text, b.position) for b in olist4]}")

# Try to replace middle item
olist4[1:2] = [Bullet("X"), Bullet("Y")]
print(f"After slice: {[(b.text, b.position) for b in olist4]}")
print("Positions after replacement:", [b.position for b in olist4])
print("BUG: Positions are not consecutive after slice replacement!")