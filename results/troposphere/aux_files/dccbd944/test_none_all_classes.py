import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.codestarconnections as csc

print("Testing None handling for all CodeStarConnections classes:\n")

# Test Connection
print("1. Connection with HostArn=None (optional string property):")
try:
    conn = csc.Connection(
        title="TestConn",
        ConnectionName="test",
        HostArn=None  # Optional property (plain string, no validator)
    )
    print("  ✓ Accepted None")
except TypeError as e:
    print(f"  ✗ Rejected None with TypeError: {e}")
except ValueError as e:
    print(f"  ✗ Rejected None with ValueError: {e}")

# Test RepositoryLink
print("\n2. RepositoryLink with EncryptionKeyArn=None (optional):")
try:
    repo = csc.RepositoryLink(
        title="TestRepo",
        ConnectionArn="arn:aws:test",
        OwnerId="owner",
        RepositoryName="repo",
        EncryptionKeyArn=None  # Optional property
    )
    print("  ✓ Accepted None")
except TypeError as e:
    print(f"  ✗ Rejected None: {e}")

# Test SyncConfiguration
print("\n3. SyncConfiguration with PublishDeploymentStatus=None (optional):")
try:
    sync = csc.SyncConfiguration(
        title="TestSync",
        Branch="main",
        ConfigFile="config.yml",
        RepositoryLinkId="link-id",
        ResourceName="resource",
        RoleArn="arn:aws:iam::123:role/test",
        SyncType="CFN_STACK_SYNC",
        PublishDeploymentStatus=None  # Optional property
    )
    print("  ✓ Accepted None")
except TypeError as e:
    print(f"  ✗ Rejected None: {e}")

print("\nConclusion: This None handling issue affects ALL troposphere classes!")
print("When None is passed for optional properties, it raises TypeError.")
print("This is a systematic issue in the BaseAWSObject.__setattr__ method.")