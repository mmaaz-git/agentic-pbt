"""Investigate the Tags concatenation behavior more carefully."""

from troposphere import Tags


def test_tags_concatenation_detailed():
    """Detailed investigation of Tags concatenation."""
    print("Tags Concatenation Investigation")
    print("=" * 50)
    
    # Test 1: Empty tag concatenation
    t1 = Tags({"Key1": "Value1"})
    t2 = Tags({})  # Empty
    
    print(f"t1 (1 tag): {t1.to_dict()}")
    print(f"t2 (empty): {t2.to_dict()}")
    
    combined = t1 + t2
    print(f"t1 + t2: {combined.to_dict()}")
    print(f"Expected: t1's tags followed by t2's tags")
    print(f"Expected count: {len(t1.to_dict())} + {len(t2.to_dict())} = {len(t1.to_dict()) + len(t2.to_dict())}")
    print(f"Actual count: {len(combined.to_dict())}")
    
    # Check if the issue is with the concatenation logic
    print(f"\nt1.tags: {t1.tags}")
    print(f"t2.tags: {t2.tags}")
    print(f"combined.tags: {combined.tags}")
    
    # The bug is in the __add__ method
    print("\nAnalyzing __add__ implementation:")
    print("The __add__ method modifies newtags.tags = self.tags + newtags.tags")
    print("But when t2 is empty, this becomes: t2.tags = t1.tags + []")
    print("This modifies t2 in place and returns it!")
    
    # Verify this is the issue
    t3 = Tags({"Key3": "Value3"})
    t4 = Tags({})
    print(f"\nBefore concatenation:")
    print(f"t3.tags: {t3.tags}")
    print(f"t4.tags: {t4.tags}")
    print(f"id(t4): {id(t4)}")
    
    result = t3 + t4
    print(f"\nAfter t3 + t4:")
    print(f"t4.tags: {t4.tags}")  # t4 was modified!
    print(f"result.tags: {result.tags}")
    print(f"id(result): {id(result)}")
    print(f"result is t4: {result is t4}")  # This should be True, confirming the bug
    
    # The real issue: when t1 has tags and t2 is empty
    # The result should have len(t1.tags) + len(t2.tags) tags
    # But it actually returns t2 with t1's tags prepended
    
    print("\n" + "=" * 50)
    print("BUG CONFIRMED: Tags.__add__ modifies the right operand in place!")
    print("This violates the expected behavior of the + operator")
    

if __name__ == "__main__":
    test_tags_concatenation_detailed()