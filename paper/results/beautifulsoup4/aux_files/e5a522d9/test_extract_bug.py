"""Investigate the extract behavior with identical NavigableStrings."""

from bs4.element import Tag, NavigableString

# Reproduce the issue with minimal example
tag = Tag(name="a")

# Add three identical empty strings
elements = [NavigableString(''), NavigableString(''), NavigableString('')]
for element in elements:
    tag.append(element)

print(f"Initial contents: {tag.contents}")
print(f"Number of elements: {len(tag.contents)}")

# Extract the middle element
extract_index = 1
extracted = tag.contents[extract_index]
print(f"\nExtracting element at index {extract_index}: {repr(extracted)}")
print(f"Element id before extraction: {id(extracted)}")

# Extract it
extracted.extract()

print(f"\nAfter extraction:")
print(f"Contents: {tag.contents}")
print(f"Number of elements: {len(tag.contents)}")

# Check if extracted element is still in contents by value
print(f"\nIs extracted element in contents (by value)? {extracted in tag.contents}")
print(f"Extracted element parent: {extracted.parent}")

# Check identity
print(f"\nIdentity check:")
for i, elem in enumerate(tag.contents):
    print(f"  Element {i}: id={id(elem)}, value={repr(elem)}, is_extracted={elem is extracted}")

# The bug: Even though we extracted a specific element, 
# the "in" operator returns True because it checks by value, not identity
print(f"\nBUG: The 'in' operator for NavigableString checks by value, not identity!")
print(f"This means extracted not in tag.contents returns False for identical strings.")

# Demonstrate that this works correctly with Tags (which use identity)
print("\n--- Testing with Tags instead of NavigableStrings ---")
tag2 = Tag(name="div")
child_tags = [Tag(name="span"), Tag(name="span"), Tag(name="span")]
for child in child_tags:
    tag2.append(child)

print(f"Initial tag contents: {tag2.contents}")
extracted_tag = tag2.contents[1]
extracted_tag.extract()
print(f"After extracting middle tag: {tag2.contents}")
print(f"Is extracted tag in contents? {extracted_tag in tag2.contents}")  # Should be False

# More detailed test showing the actual issue
print("\n--- Demonstrating the core issue ---")
tag3 = Tag(name="p")
str1 = NavigableString("test")
str2 = NavigableString("test")  # Same value as str1
tag3.append(str1)

print(f"str1 in tag3.contents: {str1 in tag3.contents}")  # True
print(f"str2 in tag3.contents: {str2 in tag3.contents}")  # Also True! Even though str2 was never added
print(f"str1 is str2: {str1 is str2}")  # False - they are different objects

print("\nThis violates the expected behavior where 'in' should check identity for mutable objects.")