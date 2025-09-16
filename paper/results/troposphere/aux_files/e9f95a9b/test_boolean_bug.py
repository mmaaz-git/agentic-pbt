"""Focused test for boolean conversion inconsistency bug."""

import troposphere.sns as sns


def test_boolean_case_sensitivity_inconsistency():
    """Test that demonstrates case sensitivity inconsistency in boolean conversion."""
    topic = sns.Topic('TestTopic')
    
    # These work (case sensitive for text booleans)
    topic.FifoTopic = 'true'
    assert topic.properties.get('FifoTopic') is True
    
    topic.FifoTopic = 'false'
    assert topic.properties.get('FifoTopic') is False
    
    topic.FifoTopic = 'True'
    assert topic.properties.get('FifoTopic') is True
    
    topic.FifoTopic = 'False'
    assert topic.properties.get('FifoTopic') is False
    
    # These also work (string numbers)
    topic.FifoTopic = '1'
    assert topic.properties.get('FifoTopic') is True
    
    topic.FifoTopic = '0'
    assert topic.properties.get('FifoTopic') is False
    
    # But these should logically work too if we accept string booleans
    # Uppercase versions should be accepted if lowercase are
    try:
        topic.FifoTopic = 'TRUE'
        result = topic.properties.get('FifoTopic')
        print(f"'TRUE' -> {result}")
    except Exception as e:
        print(f"'TRUE' -> ERROR: boolean validator rejected uppercase TRUE")
        
    try:
        topic.FifoTopic = 'FALSE'
        result = topic.properties.get('FifoTopic')
        print(f"'FALSE' -> {result}")
    except Exception as e:
        print(f"'FALSE' -> ERROR: boolean validator rejected uppercase FALSE")


def test_whitespace_handling():
    """Test whitespace handling in boolean strings."""
    topic = sns.Topic('TestTopic')
    
    # Plain versions work
    topic.FifoTopic = 'true'
    assert topic.properties.get('FifoTopic') is True
    
    # But whitespace versions don't
    try:
        topic.FifoTopic = ' true'
        print(f"' true' accepted")
    except:
        print(f"' true' rejected - inconsistent with 'true'")
        
    try:
        topic.FifoTopic = 'true '
        print(f"'true ' accepted")
    except:
        print(f"'true ' rejected - inconsistent with 'true'")
        
    try:
        topic.FifoTopic = ' true '
        print(f"' true ' accepted")
    except:
        print(f"' true ' rejected - inconsistent with 'true'")


def test_numeric_string_consistency():
    """Test that numeric strings beyond 0/1 are handled inconsistently."""
    topic = sns.Topic('TestTopic')
    
    # Integer 2 as boolean
    topic.FifoTopic = 2
    assert topic.properties.get('FifoTopic') is True  # Non-zero is truthy
    
    # But string '2' doesn't work  
    try:
        topic.FifoTopic = '2'
        result = topic.properties.get('FifoTopic')
        print(f"'2' -> {result} (inconsistent - integer 2 works)")
    except:
        print(f"'2' rejected but integer 2 is accepted")
        
    # Same for -1
    topic.FifoTopic = -1
    assert topic.properties.get('FifoTopic') is True
    
    try:
        topic.FifoTopic = '-1'
        result = topic.properties.get('FifoTopic')
        print(f"'-1' -> {result}")
    except:
        print(f"'-1' rejected but integer -1 is accepted")


if __name__ == '__main__':
    print("=== Boolean Case Sensitivity Bug ===")
    test_boolean_case_sensitivity_inconsistency()
    
    print("\n=== Whitespace Handling Bug ===")
    test_whitespace_handling()
    
    print("\n=== Numeric String Inconsistency ===")
    test_numeric_string_consistency()