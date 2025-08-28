import packaging.tags

# Test case: German eszett character (ß) normalization bug
def test_eszett_normalization_bug():
    """
    The Tag class claims to normalize case, but fails for certain Unicode characters
    like the German eszett (ß) which uppercases to SS.
    """
    # Create tags with the same logical content but different case representations
    tag_with_eszett = packaging.tags.Tag('py3', 'none', 'ß')
    tag_with_upper = packaging.tags.Tag('py3', 'none', 'ß'.upper())  # 'SS'
    tag_with_ss = packaging.tags.Tag('py3', 'none', 'ss')
    
    print(f"Tag with ß: {tag_with_eszett}")
    print(f"Tag with ß.upper() (SS): {tag_with_upper}")
    print(f"Tag with ss: {tag_with_ss}")
    print()
    
    # These should all be equal if case normalization worked correctly
    print(f"tag_with_eszett == tag_with_upper: {tag_with_eszett == tag_with_upper}")
    print(f"tag_with_upper == tag_with_ss: {tag_with_upper == tag_with_ss}")
    print(f"tag_with_eszett == tag_with_ss: {tag_with_eszett == tag_with_ss}")
    print()
    
    # The problem: 'ß'.upper() = 'SS', but 'ß'.lower() = 'ß' (not 'ss')
    print(f"'ß'.upper() = '{('ß').upper()}'")
    print(f"'ß'.lower() = '{('ß').lower()}'") 
    print(f"'SS'.lower() = '{('SS').lower()}'")
    
    # This causes inconsistent normalization
    assert tag_with_upper == tag_with_ss, "SS should normalize to ss"
    assert tag_with_eszett == tag_with_upper, "ß and SS should be treated as same (case-insensitive)"
    

if __name__ == "__main__":
    try:
        test_eszett_normalization_bug()
        print("\n✓ All assertions passed")
    except AssertionError as e:
        print(f"\n✗ Bug found: {e}")
        print("\nThis violates the case-insensitive equality property that Tags claim to have")