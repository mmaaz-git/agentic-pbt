from pydantic.alias_generators import to_camel, to_pascal, to_snake

print("=== Bug 1: to_snake not idempotent ===")
input1 = 'A0'
once = to_snake(input1)
twice = to_snake(once)
print(f"to_snake('{input1}') = '{once}'")
print(f"to_snake('{once}') = '{twice}'")
print(f"Idempotent? {once == twice}")
print()

print("=== Bug 2: Round-trip snake->camel->snake fails ===")
input2 = 'a0'
camel = to_camel(input2)
back = to_snake(camel)
print(f"'{input2}' -> to_camel -> '{camel}' -> to_snake -> '{back}'")
print(f"Round-trip successful? {input2 == back}")
print()

print("=== Bug 3: Round-trip snake->pascal->snake fails ===")
input3 = 'a_0'
pascal = to_pascal(input3)
back2 = to_snake(pascal)
print(f"'{input3}' -> to_pascal -> '{pascal}' -> to_snake -> '{back2}'")
print(f"Round-trip successful? {input3 == back2}")
print()

print("=== Bug 4: Inconsistent handling of letter-digit boundaries ===")
test_cases = ['a0', 'a_0', 'A0']
for test in test_cases:
    result = to_snake(test)
    print(f"to_snake('{test}') = '{result}'")
print()

print("=== Analysis: The issue is with letter-digit boundary handling ===")
print("to_snake inserts underscore between letter and digit: 'a0' -> 'a_0'")
print("But to_pascal removes underscores: 'a_0' -> 'A0'")
print("This breaks round-trip properties and idempotence")