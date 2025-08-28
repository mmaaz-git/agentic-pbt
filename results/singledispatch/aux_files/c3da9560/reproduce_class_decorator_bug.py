import functools
import inspect

print("=== Demonstrating the bug ===\n")

@functools.singledispatch
def process(obj):
    return "default"

print("Step 1: Define a singledispatch function 'process'")
print()

print("Step 2: Try to register a class using @process.register decorator")
print("Code:")
print("@process.register")
print("class Handler:")
print("    def __init__(self, value: int):")
print("        self.value = value")
print()

@process.register
class Handler:
    def __init__(self, value: int):
        self.value = value

print(f"After decoration, Handler is: {Handler}")
print(f"Type of Handler: {type(Handler)}")
print()

print("Step 3: Check what got registered in the registry")
for typ, func in process.registry.items():
    if typ != object:
        print(f"  Type {typ}: {func}")
print()

print("Step 4: Try to use Handler as a class")
print("Calling Handler(42)...")
result = Handler(42)
print(f"Result: {result} (type: {type(result).__name__})")
print()

print("Step 5: Try to dispatch on an int")
print(f"process(42) returns: {repr(process(42))}")
print()

print("=== Expected behavior ===")
print("The class should be registered for dispatch based on its type annotation,")
print("and Handler should still be a usable class, not replaced by a function.")
print()

print("=== Actual behavior ===")
print("1. Handler is replaced with a lambda function")
print("2. Calling Handler(42) returns 42 (an int), not a Handler instance")  
print("3. The registry appears corrupted - no proper handler registered for int")
print("4. process(42) returns 'default' instead of using the registered handler")
print()

print("=== Comparison with correct usage ===")

@functools.singledispatch
def process2(obj):
    return "default"

class Handler2:
    def __init__(self, value: int):
        self.value = value

@process2.register(int)
def _(obj):
    handler = Handler2(obj)
    return f"Handled: {handler.value}"

print("When properly registering with @process2.register(int):")
print(f"process2(42) returns: {repr(process2(42))}")