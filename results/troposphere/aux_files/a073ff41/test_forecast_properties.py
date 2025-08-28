#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/')

import troposphere.forecast as forecast
import json

def test_round_trip_properties():
    """Test round-trip property: to_dict -> from_dict -> to_dict should be identical"""
    print("Testing round-trip properties...")
    
    # Test Dataset round-trip
    dataset1 = forecast.Dataset(
        "TestDataset",
        DatasetName="test_dataset",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(
            Attributes=[
                forecast.AttributesItems(AttributeName="item_id", AttributeType="string"),
                forecast.AttributesItems(AttributeName="timestamp", AttributeType="timestamp")
            ]
        )
    )
    
    # Convert to dict
    dataset1_dict = dataset1.to_dict()
    print(f"Original dataset dict: {json.dumps(dataset1_dict, indent=2)}")
    
    # Create from dict using proper method signature
    # from_dict expects (title, dict) where dict is the Properties content
    dataset2 = forecast.Dataset.from_dict("TestDataset", dataset1_dict.get("Properties", {}))
    dataset2_dict = dataset2.to_dict()
    
    print(f"Round-trip dataset dict: {json.dumps(dataset2_dict, indent=2)}")
    print(f"Round-trip successful: {dataset1_dict == dataset2_dict}")
    print()
    
    # Test DatasetGroup round-trip
    group1 = forecast.DatasetGroup(
        "TestGroup",
        DatasetGroupName="test_group",
        Domain="RETAIL",
        DatasetArns=["arn1", "arn2"]
    )
    
    group1_dict = group1.to_dict()
    group2 = forecast.DatasetGroup.from_dict("TestGroup", group1_dict.get("Properties", {}))
    group2_dict = group2.to_dict()
    
    print(f"DatasetGroup round-trip successful: {group1_dict == group2_dict}")
    print()

def test_validation():
    """Test validation properties"""
    print("Testing validation properties...")
    
    # Test required fields
    try:
        dataset = forecast.Dataset("TestDataset")
        dataset.to_dict()  # This should fail validation
        print("ERROR: Dataset created without required fields!")
    except ValueError as e:
        print(f"Validation correctly caught missing required fields: {e}")
    
    # Test title validation
    try:
        dataset = forecast.Dataset(
            "Invalid-Title!",  # Invalid characters
            DatasetName="test",
            DatasetType="TARGET_TIME_SERIES",
            Domain="RETAIL",
            Schema=forecast.Schema()
        )
        print("ERROR: Invalid title was accepted!")
    except ValueError as e:
        print(f"Title validation correctly caught invalid characters: {e}")
    
    print()

def test_equality():
    """Test equality properties"""
    print("Testing equality properties...")
    
    # Create two identical datasets
    schema = forecast.Schema(
        Attributes=[
            forecast.AttributesItems(AttributeName="item_id", AttributeType="string")
        ]
    )
    
    dataset1 = forecast.Dataset(
        "TestDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=schema
    )
    
    dataset2 = forecast.Dataset(
        "TestDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=schema
    )
    
    print(f"Identical datasets are equal: {dataset1 == dataset2}")
    print(f"Identical datasets have same hash: {hash(dataset1) == hash(dataset2)}")
    
    # Different datasets
    dataset3 = forecast.Dataset(
        "DifferentDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=schema
    )
    
    print(f"Different datasets are not equal: {dataset1 != dataset3}")
    print(f"Different datasets have different hash: {hash(dataset1) != hash(dataset3)}")
    print()

def test_json_serialization():
    """Test JSON serialization properties"""
    print("Testing JSON serialization properties...")
    
    dataset = forecast.Dataset(
        "TestDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(
            Attributes=[
                forecast.AttributesItems(AttributeName="item_id", AttributeType="string")
            ]
        )
    )
    
    # Test to_json produces valid JSON
    json_str = dataset.to_json()
    parsed = json.loads(json_str)
    print(f"to_json produces valid JSON: {parsed is not None}")
    
    # Test JSON round-trip
    json_str1 = dataset.to_json()
    parsed = json.loads(json_str1)
    # Create new dataset from parsed properties
    dataset2 = forecast.Dataset.from_dict("TestDataset", parsed.get("Properties", {}))
    json_str2 = dataset2.to_json()
    
    print(f"JSON round-trip preserves data: {json_str1 == json_str2}")
    print()

if __name__ == "__main__":
    test_round_trip_properties()
    test_validation()
    test_equality()
    test_json_serialization()