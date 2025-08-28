import troposphere.wafregional as waf

# According to the props dictionary, these are the required fields for RateBasedRule:
# - MetricName (required)
# - Name (required)
# - RateKey (required)
# - RateLimit (required)

# Attempt 1: Create without title parameter (following props specification)
try:
    rule1 = waf.RateBasedRule(
        MetricName="TestMetric",
        Name="TestRule",
        RateKey="IP",
        RateLimit=1000
    )
    print("✓ Created RateBasedRule without title")
except TypeError as e:
    print(f"✗ Failed to create RateBasedRule without title: {e}")

# Attempt 2: Create with title parameter
try:
    rule2 = waf.RateBasedRule(
        "TestRuleTitle",  # title parameter
        MetricName="TestMetric",
        Name="TestRule",
        RateKey="IP",
        RateLimit=1000
    )
    print(f"✓ Created RateBasedRule with title: {rule2}")
except Exception as e:
    print(f"✗ Failed to create RateBasedRule with title: {e}")

# Same issue with RegexPatternSet
print("\n--- RegexPatternSet ---")

# Attempt 1: Without title (following props)
try:
    pattern_set1 = waf.RegexPatternSet(
        Name="TestPatternSet",
        RegexPatternStrings=["pattern1", "pattern2"]
    )
    print("✓ Created RegexPatternSet without title")
except TypeError as e:
    print(f"✗ Failed to create RegexPatternSet without title: {e}")

# Attempt 2: With title
try:
    pattern_set2 = waf.RegexPatternSet(
        "TestPatternSetTitle",
        Name="TestPatternSet",
        RegexPatternStrings=["pattern1", "pattern2"]
    )
    print(f"✓ Created RegexPatternSet with title: {pattern_set2}")
except Exception as e:
    print(f"✗ Failed to create RegexPatternSet with title: {e}")

# Let's check all AWSObject classes in the module
print("\n--- Checking all AWSObject classes ---")
import inspect
members = inspect.getmembers(waf)
aws_objects = [m for m in members if inspect.isclass(m[1]) and issubclass(m[1], waf.AWSObject) and m[1] != waf.AWSObject]

for name, cls in aws_objects:
    print(f"\n{name}:")
    print(f"  Props required fields: {[k for k, v in cls.props.items() if v[1] is True]}")
    print(f"  Constructor signature: {inspect.signature(cls.__init__)}")
    
    # The constructor requires 'title' but it's not in props!
    if 'title' not in [k.lower() for k in cls.props.keys()]:
        print(f"  ⚠️  'title' parameter required in __init__ but NOT in props dictionary!")