# Bug Report: troposphere.wafregional API Contract Violation

**Target**: `troposphere.wafregional` (all AWSObject classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

All AWSObject classes in troposphere.wafregional require an undocumented `title` parameter in their constructor, violating the API contract defined by their `props` dictionaries.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.wafregional as waf

@given(
    rate_limit=st.integers(min_value=100, max_value=2000000000),
    metric_name=st.text(min_size=1, max_size=255),
    name=st.text(min_size=1, max_size=128),
    rate_key=st.sampled_from(["IP"])
)
def test_rate_based_rule_rate_limit(rate_limit, metric_name, name, rate_key):
    # Property: Should be able to create objects using only props-defined parameters
    rule = waf.RateBasedRule(
        MetricName=metric_name,
        Name=name,
        RateKey=rate_key,
        RateLimit=rate_limit
    )
    assert rule.RateLimit == rate_limit
```

**Failing input**: All inputs fail - the test always raises `TypeError: BaseAWSObject.__init__() missing 1 required positional argument: 'title'`

## Reproducing the Bug

```python
import troposphere.wafregional as waf

# According to props, these are the only required parameters
rule = waf.RateBasedRule(
    MetricName="TestMetric",
    Name="TestRule",
    RateKey="IP",
    RateLimit=1000
)
```

## Why This Is A Bug

The `props` dictionary serves as the API documentation for CloudFormation properties. Users naturally expect to instantiate classes using only the properties defined in `props`. However, all AWSObject classes require an additional positional `title` parameter that is:
1. Not documented in the `props` dictionary
2. Not a CloudFormation property
3. Required even when set to `None`

This affects all 11 AWSObject classes in the module: ByteMatchSet, GeoMatchSet, IPSet, RateBasedRule, RegexPatternSet, Rule, SizeConstraintSet, SqlInjectionMatchSet, WebACL, WebACLAssociation, and XssMatchSet.

## Fix

The issue lies in the base class design. The title parameter should either be:
1. Made truly optional with a default value of `None`
2. Documented in the props dictionary if it's required
3. Handled through a different mechanism that doesn't break the props-based API contract

```diff
class BaseAWSObject:
-   def __init__(self, title, template=None, validation=True, **kwargs):
+   def __init__(self, title=None, template=None, validation=True, **kwargs):
        # Make title truly optional with a default value
        self.title = title
        # ... rest of initialization
```