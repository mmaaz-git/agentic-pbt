#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.kendra as kendra

# Test instantiation with various inputs
print("=== Testing CapacityUnitsConfiguration ===")

# Valid integer values
try:
    config1 = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=10,
        StorageCapacityUnits=20
    )
    print(f"✓ With integers: {config1.to_dict()}")
except Exception as e:
    print(f"✗ With integers failed: {e}")

# With strings that can be converted to integers
try:
    config2 = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits="10",
        StorageCapacityUnits="20"
    )
    print(f"✓ With string numbers: {config2.to_dict()}")
except Exception as e:
    print(f"✗ With string numbers failed: {e}")

# With floats that are whole numbers
try:
    config3 = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=10.0,
        StorageCapacityUnits=20.0
    )
    print(f"✓ With float whole numbers: {config3.to_dict()}")
except Exception as e:
    print(f"✗ With float whole numbers failed: {e}")

# With negative numbers
try:
    config4 = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=-10,
        StorageCapacityUnits=-20
    )
    print(f"✓ With negative numbers: {config4.to_dict()}")
except Exception as e:
    print(f"✗ With negative numbers failed: {e}")

print("\n=== Testing DocumentAttributeTarget ===")

# With boolean values
try:
    target1 = kendra.DocumentAttributeTarget(
        TargetDocumentAttributeKey="key1",
        TargetDocumentAttributeValueDeletion=True
    )
    print(f"✓ With boolean True: {target1.to_dict()}")
except Exception as e:
    print(f"✗ With boolean True failed: {e}")

# With string "true"
try:
    target2 = kendra.DocumentAttributeTarget(
        TargetDocumentAttributeKey="key2",
        TargetDocumentAttributeValueDeletion="true"
    )
    print(f"✓ With string 'true': {target2.to_dict()}")
except Exception as e:
    print(f"✗ With string 'true' failed: {e}")

# With integer 1
try:
    target3 = kendra.DocumentAttributeTarget(
        TargetDocumentAttributeKey="key3",
        TargetDocumentAttributeValueDeletion=1
    )
    print(f"✓ With integer 1: {target3.to_dict()}")
except Exception as e:
    print(f"✗ With integer 1 failed: {e}")

# With string "0" for false
try:
    target4 = kendra.DocumentAttributeTarget(
        TargetDocumentAttributeKey="key4",
        TargetDocumentAttributeValueDeletion="0"
    )
    print(f"✓ With string '0': {target4.to_dict()}")
except Exception as e:
    print(f"✗ With string '0' failed: {e}")

print("\n=== Testing WebCrawlerConfiguration ===")

# Test double validator with MaxContentSizePerPageInMegaBytes
urls = kendra.WebCrawlerUrls(
    SeedUrlConfiguration=kendra.WebCrawlerSeedUrlConfiguration(SeedUrls=["http://example.com"])
)

try:
    web1 = kendra.WebCrawlerConfiguration(
        Urls=urls,
        MaxContentSizePerPageInMegaBytes=10.5
    )
    print(f"✓ With float: {web1.to_dict()['MaxContentSizePerPageInMegaBytes']}")
except Exception as e:
    print(f"✗ With float failed: {e}")

try:
    web2 = kendra.WebCrawlerConfiguration(
        Urls=urls,
        MaxContentSizePerPageInMegaBytes="10.5"
    )
    print(f"✓ With string float: {web2.to_dict()['MaxContentSizePerPageInMegaBytes']}")
except Exception as e:
    print(f"✗ With string float failed: {e}")