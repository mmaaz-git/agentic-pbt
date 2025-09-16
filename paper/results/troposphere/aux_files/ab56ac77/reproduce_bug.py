import troposphere.eventschemas as es

print("Testing case sensitivity of boolean function:")
print()

test_cases = [
    ('true', 'lowercase'),
    ('True', 'title case'),
    ('TRUE', 'uppercase'),
    ('false', 'lowercase'),
    ('False', 'title case'),
    ('FALSE', 'uppercase'),
]

for value, description in test_cases:
    try:
        result = es.boolean(value)
        print(f"boolean('{value}') [{description}] = {result}")
    except ValueError:
        print(f"boolean('{value}') [{description}] = ValueError")

print()
print("BUG: The function accepts 'true' and 'True' but not 'TRUE'")
print("     The function accepts 'false' and 'False' but not 'FALSE'")
print("     This is inconsistent case handling for boolean strings.")