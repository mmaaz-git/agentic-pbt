"""Test serialization and round-trip properties in troposphere.s3"""

from hypothesis import given, strategies as st, assume, settings
import troposphere.s3 as s3
import troposphere
import json
import re


# Strategy for valid property values
def valid_bucket_property_strategy():
    """Generate valid property combinations for S3 Bucket"""
    return st.dictionaries(
        st.sampled_from(['BucketName', 'AccessControl']),
        st.one_of(
            # Valid bucket names
            st.from_regex(r'^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$', fullmatch=True),
            # Valid access control values
            st.sampled_from(['Private', 'PublicRead', 'PublicReadWrite', 'AuthenticatedRead'])
        ),
        max_size=2
    ).filter(lambda d: 
        all(
            (k != 'BucketName' or re.match(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$', v)) and
            (k != 'AccessControl' or v in ['Private', 'PublicRead', 'PublicReadWrite', 'AuthenticatedRead'])
            for k, v in d.items()
        )
    )


@given(valid_bucket_property_strategy())
def test_bucket_to_dict_json_round_trip(properties):
    """Test that Bucket serialization to JSON and back preserves data"""
    bucket = s3.Bucket('TestBucket')
    
    # Set valid properties
    for key, value in properties.items():
        if key == 'BucketName':
            # Extra validation for bucket names
            if not ('.' * 2 in value or re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value)):
                bucket.BucketName = value
        else:
            setattr(bucket, key, value)
    
    # Serialize to dict
    dict_repr = bucket.to_dict()
    
    # Convert to JSON and back
    json_str = json.dumps(dict_repr)
    parsed = json.loads(json_str)
    
    # Should preserve structure
    assert parsed == dict_repr
    assert parsed['Type'] == 'AWS::S3::Bucket'
    
    # Properties should be preserved
    if hasattr(bucket, 'BucketName') and bucket.BucketName:
        assert parsed['Properties']['BucketName'] == bucket.BucketName


@given(st.dictionaries(
    st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_', min_size=1, max_size=50),
    st.text(min_size=0, max_size=100),
    min_size=0,
    max_size=20
))
def test_tags_order_independence(tag_dict):
    """Test that Tags are order-independent in their representation"""
    # Create tags from dict
    tags1 = troposphere.Tags(**tag_dict)
    
    # Create same tags in potentially different order
    tags2 = troposphere.Tags(**dict(reversed(list(tag_dict.items()))))
    
    # to_dict should produce same set of key-value pairs (order might differ)
    result1 = tags1.to_dict()
    result2 = tags2.to_dict()
    
    # Convert to sets for comparison
    set1 = {(item['Key'], item['Value']) for item in result1}
    set2 = {(item['Key'], item['Value']) for item in result2}
    
    assert set1 == set2


@given(st.lists(
    st.tuples(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=20),
        st.text(min_size=0, max_size=50)
    ),
    min_size=0,
    max_size=10
))
def test_tags_duplicate_keys(pairs):
    """Test how Tags handles duplicate keys"""
    # Create dict from pairs - later values should override earlier ones
    tag_dict = dict(pairs)
    
    tags = troposphere.Tags(**tag_dict)
    result = tags.to_dict()
    
    # Result should have no duplicates
    keys_in_result = [item['Key'] for item in result]
    assert len(keys_in_result) == len(set(keys_in_result)), "Duplicate keys in Tags.to_dict()"
    
    # Should match the deduplicated dict
    result_dict = {item['Key']: item['Value'] for item in result}
    assert result_dict == tag_dict


# Test CorsRule serialization
@given(st.dictionaries(
    st.sampled_from(['AllowedHeaders', 'AllowedMethods', 'AllowedOrigins', 'ExposeHeaders', 'MaxAge']),
    st.one_of(
        st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3),
        st.integers(min_value=0, max_value=86400)
    ),
    min_size=1,
    max_size=3
))
def test_cors_rule_serialization(properties):
    """Test CorsRule serialization"""
    cors_rule = s3.CorsRule()
    
    # Set properties appropriately
    for key, value in properties.items():
        if key == 'MaxAge':
            if isinstance(value, int):
                cors_rule.MaxAge = value
        elif key in ['AllowedHeaders', 'AllowedMethods', 'AllowedOrigins', 'ExposeHeaders']:
            if isinstance(value, list):
                setattr(cors_rule, key, value)
    
    # Should be able to convert to dict
    if hasattr(cors_rule, 'to_dict'):
        result = cors_rule.to_dict()
        assert isinstance(result, dict)


# Test LifecycleRule with various properties
@given(
    st.one_of(st.just('Enabled'), st.just('Disabled')),
    st.one_of(st.none(), st.integers(min_value=1, max_value=3650)),
    st.one_of(st.none(), st.text(alphabet='abcdefghijklmnopqrstuvwxyz/', min_size=0, max_size=20))
)
def test_lifecycle_rule_properties(status, days, prefix):
    """Test LifecycleRule with various property combinations"""
    rule = s3.LifecycleRule()
    rule.Status = status
    
    if days is not None:
        rule.ExpirationInDays = days
    if prefix is not None:
        rule.Prefix = prefix
    
    # Should be able to serialize
    if hasattr(rule, 'to_dict'):
        result = rule.to_dict()
        assert result['Status'] == status
        if days is not None:
            assert result.get('ExpirationInDays') == days
        if prefix is not None:
            assert result.get('Prefix') == prefix


# Test potential integer/string confusion
@given(st.integers(min_value=0, max_value=1000000))
def test_numeric_properties_type_preservation(number):
    """Test that numeric properties preserve their type"""
    # Create a LifecycleRule with numeric property
    rule = s3.LifecycleRule()
    rule.ExpirationInDays = number
    
    if hasattr(rule, 'to_dict'):
        result = rule.to_dict()
        # Should preserve as integer, not string
        assert isinstance(result.get('ExpirationInDays'), int)
        assert result['ExpirationInDays'] == number


# Test WebsiteConfiguration  
@given(
    st.one_of(
        st.none(),
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz.', min_size=5, max_size=30)
    ),
    st.one_of(
        st.none(),
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz.', min_size=5, max_size=30)
    )
)
def test_website_configuration(index_doc, error_doc):
    """Test WebsiteConfiguration properties"""
    config = s3.WebsiteConfiguration()
    
    if index_doc:
        config.IndexDocument = index_doc
    if error_doc:
        config.ErrorDocument = error_doc
    
    if hasattr(config, 'to_dict'):
        result = config.to_dict()
        if index_doc:
            assert result.get('IndexDocument') == index_doc
        if error_doc:
            assert result.get('ErrorDocument') == error_doc