#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')
import yq
import inspect
import io
import json
import tomlkit

# Check functions available
print("Available yq functions:")
for name, obj in inspect.getmembers(yq):
    if callable(obj) and not name.startswith("_"):
        print(f"  {name}: {type(obj)}")

# Test a simple round-trip
test_toml = """
[package]
name = "test"
version = "1.0.0"

[dependencies]
numpy = "1.2.3"
pandas = { version = "2.0.0", optional = true }

[[array_of_tables]]
key = "value1"

[[array_of_tables]]
key = "value2"
"""

print("\n\nTesting TOML round-trip:")
print("Original TOML:")
print(test_toml)

# Parse TOML to dict
parsed = tomlkit.parse(test_toml)
print("\nParsed to Python dict:", parsed)

# Convert to JSON
json_str = json.dumps(parsed, cls=yq.JSONDateTimeEncoder)
print("\nAs JSON:", json_str)

# Parse back from JSON
json_parsed = json.loads(json_str)
print("\nParsed back from JSON:", json_parsed)

# Convert back to TOML
toml_output = io.StringIO()
tomlkit.dump(json_parsed, toml_output)
print("\nBack to TOML:")
print(toml_output.getvalue())

# Check if they're equivalent
reparsed = tomlkit.parse(toml_output.getvalue())
print("\nAre they equivalent?", parsed == reparsed)