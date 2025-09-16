#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from sudachipy import Config

print("Further investigation of Config.update():")
print("=" * 60)

# Test if update actually modifies the config
config = Config(projection='surface')
print(f"Initial config: projection='{config.projection}', system={config.system}")

# Try update with keyword arguments
print("\nCalling config.update(projection='normalized', system='test'):")
result = config.update(projection='normalized', system='test')

print(f"Returned value: {result}")
print(f"Original config after update: projection='{config.projection}', system={config.system}")
print(f"Are they the same object? {result is config}")

# Check if update returns a new Config
print("\n" + "=" * 60)
print("Testing if update() returns a new Config:")

config1 = Config(projection='surface')
config2 = config1.update(projection='normalized')

print(f"config1: projection='{config1.projection}'")
print(f"config2: projection='{config2.projection}'")
print(f"Same object? {config1 is config2}")

# Test with all possible parameters
print("\n" + "=" * 60)
print("Testing comprehensive update:")

base = Config()
updated = base.update(
    system='test_system',
    user=['user1', 'user2'],
    projection='reading',
    characterDefinitionFile='test.def'
)

print(f"Base config: system={base.system}, projection='{base.projection}'")
print(f"Updated config: system={updated.system}, projection='{updated.projection}'")

# Test chaining
print("\n" + "=" * 60)
print("Testing method chaining:")

chained = Config().update(projection='normalized').update(system='test')
print(f"Chained result: system={chained.system}, projection='{chained.projection}'")

# Test empty update
print("\n" + "=" * 60)
print("Testing empty update:")

original = Config(projection='reading', system='original')
empty_update = original.update()
print(f"Original: system={original.system}, projection='{original.projection}'")
print(f"After empty update: system={empty_update.system}, projection='{empty_update.projection}'")
print(f"Same values? {original.system == empty_update.system and original.projection == empty_update.projection}")