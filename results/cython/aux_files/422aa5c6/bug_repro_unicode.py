import Cython.Tempita

# BUG: Certain Unicode identifiers are incorrectly parsed
# º (ordinal indicator, U+00BA) is a valid Python identifier but Tempita mishandles it

# First confirm it's valid in Python
º = "test_value"
print(f"º is valid Python identifier: {º}")
print(f"º.isidentifier() = {'º'.isidentifier()}")

# But Tempita incorrectly parses it
try:
    template = Cython.Tempita.Template('{{º}}')
    result = template.substitute(**{'º': 'value'})
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    # Error says "name 'o' is not defined" - it's incorrectly parsing º as 'o'

# Test other similar Unicode characters
print("\nTesting other Unicode identifiers:")
test_chars = [
    ('ª', 'feminine ordinal indicator'),
    ('º', 'masculine ordinal indicator'),
    ('µ', 'micro sign'),
    ('μ', 'Greek small letter mu'),
]

for char, desc in test_chars:
    print(f"\n{char} ({desc}):")
    print(f"  Python identifier: {char.isidentifier()}")
    try:
        template = Cython.Tempita.Template(f'{{{{{char}}}}}')
        result = template.substitute(**{char: f'value_{char}'})
        print(f"  Tempita result: {result}")
    except Exception as e:
        print(f"  Tempita error: {e}")