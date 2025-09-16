#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import troposphere
import troposphere.kafkaconnect as kc
from troposphere import Template

print("=== Testing template generation with bytes values ===\n")

# Create a CloudFormation template
template = Template()
template.set_description("Test template for KafkaConnect with bytes bug")

# Try to add a Connector with bytes values
try:
    connector = kc.Connector(
        "TestConnector",
        Capacity=kc.Capacity(
            ProvisionedCapacity=kc.ProvisionedCapacity(
                WorkerCount=b'5',  # bytes value
                McuCount=2
            )
        ),
        ConnectorConfiguration={"key": "value"},
        ConnectorName="test-connector",
        KafkaCluster=kc.KafkaCluster(
            ApacheKafkaCluster=kc.ApacheKafkaCluster(
                BootstrapServers="kafka.example.com:9092",
                Vpc=kc.Vpc(
                    SecurityGroups=["sg-123"],
                    Subnets=["subnet-123"]
                )
            )
        ),
        KafkaClusterClientAuthentication=kc.KafkaClusterClientAuthentication(
            AuthenticationType="NONE"
        ),
        KafkaClusterEncryptionInTransit=kc.KafkaClusterEncryptionInTransit(
            EncryptionType="TLS"
        ),
        KafkaConnectVersion="2.7.1",
        Plugins=[
            kc.Plugin(
                CustomPlugin=kc.CustomPluginProperty(
                    CustomPluginArn="arn:aws:kafkaconnect:us-east-1:123456789012:custom-plugin/test",
                    Revision=1
                )
            )
        ],
        ServiceExecutionRoleArn="arn:aws:iam::123456789012:role/service-role"
    )
    
    template.add_resource(connector)
    print("✓ Connector added to template with bytes value")
    
    # Try to generate JSON
    print("\nAttempting to generate CloudFormation JSON...")
    json_output = template.to_json()
    print("✗ Unexpectedly succeeded! This should have failed.")
    print(f"Output: {json_output[:200]}...")
    
except TypeError as e:
    print(f"✓ JSON generation failed as expected: {e}")
except Exception as e:
    print(f"Error: {e}")

# Now test the to_dict -> json.dumps path
print("\n=== Testing to_dict() -> json.dumps() ===\n")

connector2 = kc.Connector(
    "TestConnector2", 
    Capacity=kc.Capacity(
        AutoScaling=kc.AutoScaling(
            MaxWorkerCount=10,
            MinWorkerCount=1,
            McuCount=b'2',  # bytes value
            ScaleInPolicy=kc.ScaleInPolicy(CpuUtilizationPercentage=b'20'),  # bytes
            ScaleOutPolicy=kc.ScaleOutPolicy(CpuUtilizationPercentage=b'80')  # bytes
        )
    ),
    ConnectorConfiguration={"key": "value"},
    ConnectorName="test-connector-2",
    KafkaCluster=kc.KafkaCluster(
        ApacheKafkaCluster=kc.ApacheKafkaCluster(
            BootstrapServers="kafka.example.com:9092",
            Vpc=kc.Vpc(
                SecurityGroups=["sg-123"],
                Subnets=["subnet-123"]
            )
        )
    ),
    KafkaClusterClientAuthentication=kc.KafkaClusterClientAuthentication(
        AuthenticationType="NONE"
    ),
    KafkaClusterEncryptionInTransit=kc.KafkaClusterEncryptionInTransit(
        EncryptionType="TLS"
    ),
    KafkaConnectVersion="2.7.1",
    Plugins=[
        kc.Plugin(
            CustomPlugin=kc.CustomPluginProperty(
                CustomPluginArn="arn:aws:kafkaconnect:us-east-1:123456789012:custom-plugin/test",
                Revision=1
            )
        )
    ],
    ServiceExecutionRoleArn="arn:aws:iam::123456789012:role/service-role"
)

print("Connector created with bytes values in AutoScaling")
dict_repr = connector2.to_dict()
print("to_dict() succeeded")

try:
    json_str = json.dumps(dict_repr)
    print("✗ json.dumps unexpectedly succeeded")
except TypeError as e:
    print(f"✓ json.dumps failed with: {e}")
    print("\nThis confirms the bug: bytes values pass validation but break JSON serialization")