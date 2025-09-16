import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.appintegrations import ExternalUrlConfig

print("Realistic scenario: Building config from user input or API response")
print("=" * 60)

# Simulating data from an API or user configuration
api_response = {
    "access_url": "https://example.com",
    "approved_origins": None  # API might return None for unset fields
}

print(f"API Response: {api_response}")
print("\nAttempting to create ExternalUrlConfig from API data...")

# Common pattern: mapping API response to troposphere objects
try:
    config = ExternalUrlConfig(
        AccessUrl=api_response["access_url"],
        ApprovedOrigins=api_response["approved_origins"]
    )
    print("Success!")
except TypeError as e:
    print(f"ERROR: {e}")
    print("\nDevelopers would need to add defensive code:")
    
    # Workaround code developers would need to write
    kwargs = {"AccessUrl": api_response["access_url"]}
    if api_response["approved_origins"] is not None:
        kwargs["ApprovedOrigins"] = api_response["approved_origins"]
    
    config = ExternalUrlConfig(**kwargs)
    print("Workaround successful, but adds unnecessary complexity")

print("\n" + "=" * 60)
print("Another scenario: Using dict.get() with default None")
print("=" * 60)

config_dict = {"access_url": "https://example.com"}
print(f"Config dict: {config_dict}")

try:
    config = ExternalUrlConfig(
        AccessUrl=config_dict.get("access_url"),
        ApprovedOrigins=config_dict.get("approved_origins")  # Returns None if key missing
    )
    print("Success!")
except TypeError as e:
    print(f"ERROR: {e}")
    print("This common Python pattern fails with troposphere!")