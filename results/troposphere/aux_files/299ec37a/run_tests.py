#!/usr/bin/env python3
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

# Run individual test functions
from test_iotfleetwise_properties import *

print("Running test_campaign_round_trip...")
try:
    test_campaign_round_trip()
    print("✓ test_campaign_round_trip passed")
except Exception as e:
    print(f"✗ test_campaign_round_trip failed: {e}")

print("\nRunning test_campaign_required_properties...")
try:
    test_campaign_required_properties()
    print("✓ test_campaign_required_properties passed")
except Exception as e:
    print(f"✗ test_campaign_required_properties failed: {e}")

print("\nRunning test_fleet_type_validation...")
try:
    test_fleet_type_validation()
    print("✓ test_fleet_type_validation passed")
except Exception as e:
    print(f"✗ test_fleet_type_validation failed: {e}")

print("\nRunning test_sensor_property_consistency...")
try:
    test_sensor_property_consistency()
    print("✓ test_sensor_property_consistency passed")
except Exception as e:
    print(f"✗ test_sensor_property_consistency failed: {e}")

print("\nRunning test_state_template_round_trip...")
try:
    test_state_template_round_trip()
    print("✓ test_state_template_round_trip passed")
except Exception as e:
    print(f"✗ test_state_template_round_trip failed: {e}")

print("\nRunning test_vehicle_attributes...")
try:
    test_vehicle_attributes()
    print("✓ test_vehicle_attributes passed")
except Exception as e:
    print(f"✗ test_vehicle_attributes failed: {e}")

print("\nRunning test_decoder_manifest_network_interface...")
try:
    test_decoder_manifest_network_interface()
    print("✓ test_decoder_manifest_network_interface passed")
except Exception as e:
    print(f"✗ test_decoder_manifest_network_interface failed: {e}")