import troposphere.ssmincidents as ssmincidents

print("Bug 1: integer() function type preservation")
print("-" * 50)
result = ssmincidents.integer('123')
print(f"integer('123') returns: {repr(result)}")
print(f"Type: {type(result)}")
print(f"Expected: int, Got: {type(result).__name__}")
print()

print("Bug 2: boolean() function case sensitivity")
print("-" * 50)
test_values = ['true', 'True', 'TRUE', 'false', 'False', 'FALSE']
for val in test_values:
    try:
        result = ssmincidents.boolean(val)
        print(f"boolean('{val}') = {result} ✓")
    except ValueError:
        print(f"boolean('{val}') = ValueError ✗")
print()

print("Bug 3: IncidentTemplate Impact field type inconsistency")
print("-" * 50)
# Create template with integer
template1 = ssmincidents.IncidentTemplate(Title='Test', Impact=3)
dict1 = template1.to_dict()
print(f"With Impact=3: {dict1['Impact']} (type: {type(dict1['Impact']).__name__})")

# Create template with string
template2 = ssmincidents.IncidentTemplate(Title='Test', Impact='3')
dict2 = template2.to_dict()
print(f"With Impact='3': {dict2['Impact']} (type: {type(dict2['Impact']).__name__})")

print(f"Are they equal? {dict1['Impact'] == dict2['Impact']}")
print(f"Are they the same type? {type(dict1['Impact']) == type(dict2['Impact'])}")