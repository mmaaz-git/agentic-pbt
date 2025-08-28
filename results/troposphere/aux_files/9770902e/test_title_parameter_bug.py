"""
Test demonstrating the API contract violation in troposphere.wafregional
"""
import troposphere.wafregional as waf
from hypothesis import given, strategies as st


# This test demonstrates the bug: AWSObject classes require a positional 'title' 
# parameter that is not documented in their props dictionary
@given(
    metric_name=st.text(min_size=1, max_size=255),
    name=st.text(min_size=1, max_size=128),
    rate_key=st.sampled_from(["IP"]),
    rate_limit=st.integers(min_value=100, max_value=2000000000)
)
def test_rate_based_rule_contract_violation(metric_name, name, rate_key, rate_limit):
    """
    Property: AWSObject classes should be instantiable using only the properties 
    defined in their `props` dictionary, as this is the documented API contract.
    
    The props dictionary for RateBasedRule specifies these required fields:
    - MetricName (required)
    - Name (required)  
    - RateKey (required)
    - RateLimit (required)
    
    However, the constructor actually requires an additional 'title' parameter.
    """
    
    # This should work according to the props specification, but it doesn't
    try:
        rule = waf.RateBasedRule(
            MetricName=metric_name,
            Name=name,
            RateKey=rate_key,
            RateLimit=rate_limit
        )
        assert False, "Should have failed without title parameter"
    except TypeError as e:
        # The actual error proves the API contract violation
        assert "missing 1 required positional argument: 'title'" in str(e)
    
    # The actual way to create it requires an undocumented parameter
    rule = waf.RateBasedRule(
        None,  # or any title string - this parameter is not in props!
        MetricName=metric_name,
        Name=name,
        RateKey=rate_key,
        RateLimit=rate_limit
    )
    assert rule.MetricName == metric_name


if __name__ == "__main__":
    # Run a simple test case directly without hypothesis decorator
    import troposphere.wafregional as waf
    
    # Try to create without title (following props)
    try:
        rule = waf.RateBasedRule(
            MetricName="TestMetric",
            Name="TestRule",
            RateKey="IP",
            RateLimit=1000
        )
        print("✗ Should have failed without title")
    except TypeError as e:
        print(f"✓ Failed as expected: {e}")
    
    # Create with title works
    rule = waf.RateBasedRule(
        None,  # title parameter not in props!
        MetricName="TestMetric",
        Name="TestRule",
        RateKey="IP",
        RateLimit=1000
    )
    print("✓ Works with undocumented title parameter")
    print("✓ Test demonstrates the API contract violation")