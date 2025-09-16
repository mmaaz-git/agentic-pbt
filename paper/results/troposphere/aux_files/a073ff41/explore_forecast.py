#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/')

import troposphere.forecast as forecast
import json

# Test instantiation and serialization
try:
    # Test AttributesItems
    attr = forecast.AttributesItems(
        AttributeName="test_attr",
        AttributeType="string"
    )
    print("AttributesItems instantiated successfully")
    print(f"to_dict: {attr.to_dict()}")
    print(f"to_json: {attr.to_json()}")
    print()
    
    # Test Schema
    schema = forecast.Schema(
        Attributes=[
            forecast.AttributesItems(AttributeName="attr1", AttributeType="string"),
            forecast.AttributesItems(AttributeName="attr2", AttributeType="integer")
        ]
    )
    print("Schema instantiated successfully")
    print(f"to_dict: {schema.to_dict()}")
    print()
    
    # Test EncryptionConfig
    encryption = forecast.EncryptionConfig(
        KmsKeyArn="arn:aws:kms:us-east-1:123456789012:key/test",
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    print("EncryptionConfig instantiated successfully")
    print(f"to_dict: {encryption.to_dict()}")
    print()
    
    # Test TagsItems
    tag = forecast.TagsItems(Key="Environment", Value="Production")
    print("TagsItems instantiated successfully")
    print(f"to_dict: {tag.to_dict()}")
    print()
    
    # Test Dataset
    dataset = forecast.Dataset(
        "MyDataset",
        DatasetName="test_dataset",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=schema
    )
    print("Dataset instantiated successfully")
    print(f"to_dict: {dataset.to_dict()}")
    print(f"title: {dataset.title}")
    print(f"resource_type: {dataset.resource_type}")
    print()
    
    # Test DatasetGroup
    dataset_group = forecast.DatasetGroup(
        "MyDatasetGroup",
        DatasetGroupName="test_group",
        Domain="RETAIL",
        DatasetArns=["arn:aws:forecast:us-east-1:123456789012:dataset/test"]
    )
    print("DatasetGroup instantiated successfully")
    print(f"to_dict: {dataset_group.to_dict()}")
    print()
    
    # Test from_dict
    attr_dict = {"AttributeName": "test", "AttributeType": "string"}
    attr_from_dict = forecast.AttributesItems.from_dict(None, **attr_dict)
    print(f"AttributesItems from_dict: {attr_from_dict.to_dict()}")
    
    dataset_dict = {
        "DatasetName": "test_dataset",
        "DatasetType": "TARGET_TIME_SERIES",
        "Domain": "RETAIL",
        "Schema": {
            "Attributes": [
                {"AttributeName": "item_id", "AttributeType": "string"},
                {"AttributeName": "timestamp", "AttributeType": "timestamp"}
            ]
        }
    }
    dataset_from_dict = forecast.Dataset.from_dict("MyDataset", dataset_dict)
    print(f"Dataset from_dict: {dataset_from_dict.to_dict()}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()