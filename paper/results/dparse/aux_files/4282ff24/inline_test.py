import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

# Direct inline testing
exec("""
from dparse.dependencies import Dependency
from dparse.parser import Parser
from packaging.specifiers import SpecifierSet
import json
from dparse.dependencies import DparseJSONEncoder

# Test 1: Key property
dep = Dependency(name="Test_Package", specs=SpecifierSet(), line="Test_Package")
assert dep.key == "test-package", f"Key property failed: {dep.key}"
print("✓ Key property test passed")

# Test 2: Full name with extras
dep = Dependency(name="pkg", specs=SpecifierSet(), line="pkg", extras=["dev", "test"])
assert dep.full_name == "pkg[dev,test]", f"Full name failed: {dep.full_name}"
print("✓ Full name test passed")

# Test 3: Serialize/deserialize
original = Dependency(name="TestPkg", specs=SpecifierSet(">=1.0"), line="TestPkg>=1.0")
serialized = original.serialize()
serialized_json = json.dumps(serialized, cls=DparseJSONEncoder)
deserialized_dict = json.loads(serialized_json)
deserialized_dict['specs'] = SpecifierSet(deserialized_dict['specs'])
restored = Dependency.deserialize(deserialized_dict)
assert restored.name == original.name, f"Deserialization failed"
print("✓ Serialize/deserialize test passed")

# Test 4: Index server normalization
result = Parser.parse_index_server("-i http://example.com")
assert result == "http://example.com/", f"Index server failed: {result}"
print("✓ Index server normalization test passed")

# Test 5: Hash parsing
cleaned, hashes = Parser.parse_hashes("pkg --hash=sha256:abc123")
assert "--hash=sha256:abc123" in hashes, f"Hash parsing failed: {hashes}"
print("✓ Hash parsing test passed")

print("\\nAll basic tests passed!")
""")