"""Test if the same bug affects Tag objects."""

from bs4.element import Tag

def test_tag_contains_behavior():
    """Test if Tags have the same issue with __contains__."""
    
    parent = Tag(name="div")
    
    # Create two identical but separate tags
    tag1 = Tag(name="span")
    tag1.attrs = {"class": "test"}
    
    tag2 = Tag(name="span")
    tag2.attrs = {"class": "test"}
    
    # Add only tag1
    parent.append(tag1)
    
    print("Testing Tag.__contains__ behavior:")
    print(f"  tag1 is tag2: {tag1 is tag2}")
    print(f"  tag1 == tag2: {tag1 == tag2}")
    print(f"  tag1 in parent.contents: {tag1 in parent.contents}")
    print(f"  tag2 in parent.contents: {tag2 in parent.contents}")
    
    # Test with extraction
    print("\nAfter extracting tag1:")
    tag1.extract()
    print(f"  tag1 in parent.contents: {tag1 in parent.contents}")
    print(f"  tag1.parent: {tag1.parent}")
    
    # Test with identical empty tags
    parent2 = Tag(name="div")
    empty1 = Tag(name="br")
    empty2 = Tag(name="br")
    
    parent2.append(empty1)
    
    print("\nTesting with empty tags:")
    print(f"  empty1 == empty2: {empty1 == empty2}")
    print(f"  empty2 in parent2.contents: {empty2 in parent2.contents}")
    
    # Test Tag.__eq__ implementation
    print("\nTesting Tag equality in detail:")
    t1 = Tag(name="p")
    t1.append("content")
    
    t2 = Tag(name="p")
    t2.append("content")
    
    print(f"  Tags with same structure are equal: {t1 == t2}")
    
    parent3 = Tag(name="div")
    parent3.append(t1)
    print(f"  t2 in parent3.contents (should be False): {t2 in parent3.contents}")
    
    return True


if __name__ == "__main__":
    test_tag_contains_behavior()