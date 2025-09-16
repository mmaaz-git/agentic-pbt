#!/usr/bin/env python3
"""Test the impact of the None value bug in real-world scenarios."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.b2bi as b2bi
import json

print("Testing real-world impact of the None value bug")
print("=" * 60)

# Scenario 1: Creating resources programmatically with conditional properties
print("\nScenario 1: Programmatic resource creation with conditionals")
print("-" * 40)

def create_profile(name, include_email=False):
    """Common pattern: conditionally include optional properties."""
    email = "admin@example.com" if include_email else None
    
    try:
        profile = b2bi.Profile(
            title="MyProfile",
            BusinessName="MyBusiness",
            Email=email,  # BUG: This fails when email is None
            Logging="ENABLED",
            Name=name,
            Phone="555-1234"
        )
        return profile
    except TypeError as e:
        print(f"✗ Cannot create profile with Email=None: {e}")
        # Workaround: Don't pass Email at all when it's None
        kwargs = {
            "title": "MyProfile",
            "BusinessName": "MyBusiness",
            "Logging": "ENABLED",
            "Name": name,
            "Phone": "555-1234"
        }
        if email is not None:
            kwargs["Email"] = email
        return b2bi.Profile(**kwargs)

profile1 = create_profile("Profile1", include_email=False)
print("✓ Workaround successful: Created profile without email")

# Scenario 2: Loading from external configuration
print("\nScenario 2: Loading from external configuration (e.g., YAML/JSON)")
print("-" * 40)

# Simulate config loaded from YAML/JSON where optional fields might be null
config = {
    "profiles": [
        {
            "title": "ConfigProfile1",
            "BusinessName": "Business1",
            "Email": None,  # Explicitly null in config
            "Logging": "ENABLED",
            "Name": "Config1",
            "Phone": "555-0001"
        },
        {
            "title": "ConfigProfile2", 
            "BusinessName": "Business2",
            "Email": "admin@business2.com",
            "Logging": "DISABLED",
            "Name": "Config2",
            "Phone": "555-0002"
        }
    ]
}

for profile_config in config["profiles"]:
    try:
        # Direct creation would fail for profiles with None values
        profile = b2bi.Profile(**profile_config)
        print(f"✓ Created {profile_config['title']}")
    except TypeError as e:
        print(f"✗ Failed to create {profile_config['title']}: {str(e)[:80]}...")
        # Need to filter out None values
        filtered_config = {k: v for k, v in profile_config.items() if v is not None}
        profile = b2bi.Profile(**filtered_config)
        print(f"  ✓ Workaround: Created after filtering None values")

# Scenario 3: CloudFormation template generation
print("\nScenario 3: CloudFormation template generation")
print("-" * 40)

# Create a profile without email (using workaround)
profile = b2bi.Profile(
    title="TemplateProfile",
    BusinessName="TemplateBusiness",
    # Email omitted (not set to None)
    Logging="ENABLED",
    Name="TemplateProfile",
    Phone="555-9999"
)

try:
    cf_json = profile.to_json()
    cf_dict = json.loads(cf_json)
    print("✓ Generated CloudFormation JSON:")
    print(f"  Properties: {list(cf_dict['Properties'].keys())}")
    print(f"  Email included: {'Email' in cf_dict['Properties']}")
except Exception as e:
    print(f"✗ Failed to generate template: {e}")

print("\n" + "=" * 60)
print("IMPACT ANALYSIS:")
print("1. The bug affects common programming patterns (conditional properties)")
print("2. It breaks when loading configurations with explicit null values")
print("3. Workaround required: Filter out None values before instantiation")
print("4. This violates Python conventions where None indicates absence")
print("5. Makes the API less intuitive and requires extra code for users")