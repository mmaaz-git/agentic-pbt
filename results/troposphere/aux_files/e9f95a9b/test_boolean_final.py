"""Final test demonstrating boolean string conversion inconsistency."""

import troposphere.sns as sns


def demonstrate_bug():
    """Demonstrate the boolean string conversion inconsistency."""
    topic = sns.Topic('TestTopic')
    
    print("Boolean String Conversion Behavior:")
    print("====================================")
    
    test_cases = [
        # (value, description)
        ('true', 'lowercase true'),
        ('false', 'lowercase false'),
        ('True', 'title case True'),
        ('False', 'title case False'),
        ('TRUE', 'uppercase TRUE'),
        ('FALSE', 'uppercase FALSE'),
        ('1', 'string "1"'),
        ('0', 'string "0"'),
        (1, 'integer 1'),
        (0, 'integer 0'),
        (True, 'boolean True'),
        (False, 'boolean False'),
    ]
    
    results = []
    for value, desc in test_cases:
        try:
            topic.FifoTopic = value
            result = topic.properties.get('FifoTopic')
            status = f"✓ Accepted -> {result}"
            results.append((desc, value, status, True))
        except:
            status = "✗ Rejected"
            results.append((desc, value, status, False))
    
    # Print results
    for desc, value, status, accepted in results:
        print(f"{desc:20} ({repr(value):8}): {status}")
    
    # Analyze inconsistency
    print("\nInconsistency Analysis:")
    print("-----------------------")
    
    # Check case sensitivity
    true_variants = [r for r in results if 'true' in r[0].lower() and 'boolean' not in r[0]]
    if any(r[3] for r in true_variants) and not all(r[3] for r in true_variants):
        print("❌ INCONSISTENT: Some case variants of 'true'/'false' work, others don't")
        print("   Accepted:", [r[1] for r in true_variants if r[3]])
        print("   Rejected:", [r[1] for r in true_variants if not r[3]])
        return True
    
    return False


if __name__ == '__main__':
    has_bug = demonstrate_bug()