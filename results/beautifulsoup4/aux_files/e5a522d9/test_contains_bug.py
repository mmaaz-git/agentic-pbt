"""Demonstrate the bug in Tag.__contains__ for NavigableString objects."""

from bs4.element import Tag, NavigableString

def test_navigable_string_contains_bug():
    """
    Bug: Tag.__contains__ uses value equality instead of identity for NavigableStrings.
    
    This causes problems when checking if a specific NavigableString instance
    is in a Tag's contents, as it will return True for any NavigableString
    with the same value, not just the specific instance.
    """
    
    # Create a tag and add a NavigableString
    tag = Tag(name="p")
    string1 = NavigableString("Hello")
    tag.append(string1)
    
    # Create another NavigableString with the same value but different identity
    string2 = NavigableString("Hello")
    
    # These should be different objects
    assert string1 is not string2
    
    # But they are equal by value
    assert string1 == string2
    
    # BUG: string2 appears to be in tag.contents even though it was never added!
    assert string2 in tag.contents  # This should be False but returns True
    
    # This violates the principle that only elements explicitly added to a tag
    # should be considered "in" that tag's contents
    
    # The parent relationship correctly shows string2 is not a child
    assert string1.parent is tag
    assert string2.parent is None
    
    # But the 'in' operator gives misleading results
    print("BUG CONFIRMED: NavigableString with same value but never added")
    print(f"  string2 in tag.contents: {string2 in tag.contents} (should be False)")
    print(f"  string2.parent: {string2.parent} (correctly None)")
    
    return True


def test_extraction_false_positive():
    """
    This bug causes false positives when checking if an extracted element
    is still in the parent tag's contents.
    """
    
    tag = Tag(name="div")
    
    # Add multiple identical strings
    strings = [NavigableString("same"), NavigableString("same"), NavigableString("same")]
    for s in strings:
        tag.append(s)
    
    # Extract the middle one
    middle = strings[1]
    middle.extract()
    
    # The element has been extracted
    assert middle.parent is None
    assert len(tag.contents) == 2
    
    # BUG: But 'in' still returns True because other strings have the same value
    assert middle in tag.contents  # Should be False but returns True!
    
    print("BUG CONFIRMED: Extracted element still appears to be in contents")
    print(f"  Extracted string in tag.contents: {middle in tag.contents} (should be False)")
    print(f"  Extracted string parent: {middle.parent} (correctly None)")
    
    return True


def test_correct_identity_check():
    """
    Show how the check should work using identity instead of equality.
    """
    
    tag = Tag(name="div")
    strings = [NavigableString("same"), NavigableString("same"), NavigableString("same")]
    for s in strings:
        tag.append(s)
    
    middle = strings[1]
    middle.extract()
    
    # Correct way to check - using identity
    is_really_in_contents = any(elem is middle for elem in tag.contents)
    
    print("\nCorrect identity-based check:")
    print(f"  Using 'in' operator: {middle in tag.contents} (incorrect - uses equality)")
    print(f"  Using identity check: {is_really_in_contents} (correct - uses 'is')")
    
    assert is_really_in_contents == False  # Correctly returns False
    
    return True


def test_implications_for_algorithms():
    """
    This bug can cause incorrect behavior in algorithms that rely on
    checking membership after extraction.
    """
    
    tag = Tag(name="ul")
    items = [NavigableString("item"), NavigableString("item"), NavigableString("item")]
    for item in items:
        tag.append(item)
    
    # Algorithm that tries to move items around
    to_move = []
    for item in tag.contents[:]:  # Make a copy to iterate safely
        if str(item) == "item":
            item.extract()
            to_move.append(item)
    
    # Check that items were removed
    for item in to_move:
        # BUG: This check is unreliable!
        if item in tag.contents:
            print(f"ERROR: Item {id(item)} still in contents after extraction!")
            # This will incorrectly report items as still being in contents
    
    print("\nImplication: Algorithms using 'in' after extract() may behave incorrectly")
    
    return True


if __name__ == "__main__":
    print("Testing Tag.__contains__ bug with NavigableString objects\n")
    print("=" * 60)
    
    test_navigable_string_contains_bug()
    print("\n" + "=" * 60)
    
    test_extraction_false_positive()
    print("\n" + "=" * 60)
    
    test_correct_identity_check()
    print("\n" + "=" * 60)
    
    test_implications_for_algorithms()
    
    print("\n" + "=" * 60)
    print("\nSUMMARY: Tag.__contains__ uses value equality instead of identity,")
    print("causing false positives when checking if NavigableString objects")
    print("are in a Tag's contents. This affects extraction operations and")
    print("any code that relies on membership testing after modifications.")