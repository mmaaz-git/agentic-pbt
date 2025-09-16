import collections

# Reproducing the Counter addition associativity bug
d1 = {}
d2 = {'0': -1}
d3 = {'0': 1}

c1 = collections.Counter(d1)
c2 = collections.Counter(d2)
c3 = collections.Counter(d3)

# Test associativity: (c1 + c2) + c3 should equal c1 + (c2 + c3)
left_assoc = (c1 + c2) + c3
right_assoc = c1 + (c2 + c3)

print("Testing Counter addition associativity:")
print(f"d1 = {d1}, d2 = {d2}, d3 = {d3}")
print(f"c1 = {c1}")
print(f"c2 = {c2}")
print(f"c3 = {c3}")
print()
print(f"(c1 + c2) = {c1 + c2}")
print(f"(c1 + c2) + c3 = {left_assoc}")
print()
print(f"(c2 + c3) = {c2 + c3}")
print(f"c1 + (c2 + c3) = {right_assoc}")
print()
print(f"Are they equal? {left_assoc == right_assoc}")
print()

# Let's understand why this happens
print("Analysis:")
print("The issue is that Counter addition only keeps positive counts.")
print("When c2 = Counter({'0': -1}) and c3 = Counter({'0': 1}),")
print("their sum (c2 + c3) results in Counter() because -1 + 1 = 0 (not positive).")
print("But when we compute (c1 + c2) first, since c1 is empty,")
print("(c1 + c2) = Counter() (negative counts are dropped).")
print("Then Counter() + c3 = Counter({'0': 1}).")
print()
print("This violates the mathematical property of associativity!")