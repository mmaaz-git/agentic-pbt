#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import tokenizers.normalizers as norm
import unicodedata

# Test 1: Idempotence - applying a normalizer twice should give same result as once
@given(st.text())
def test_lowercase_idempotent(text):
    normalizer = norm.Lowercase()
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    assert once == twice

@given(st.text())
def test_nfc_idempotent(text):
    normalizer = norm.NFC()
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    assert once == twice

@given(st.text())
def test_nfd_idempotent(text):
    normalizer = norm.NFD()
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    assert once == twice

@given(st.text())
def test_nfkc_idempotent(text):
    normalizer = norm.NFKC()
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    assert once == twice

@given(st.text())
def test_nfkd_idempotent(text):
    normalizer = norm.NFKD()
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    assert once == twice

@given(st.text())
def test_strip_idempotent(text):
    normalizer = norm.Strip()
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    assert once == twice

@given(st.text())
def test_strip_accents_idempotent(text):
    normalizer = norm.StripAccents()
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    assert once == twice

# Test 2: Sequence composition - applying normalizers in sequence
@given(st.text())
def test_sequence_composition(text):
    # Create individual normalizers
    lower = norm.Lowercase()
    strip = norm.Strip()
    
    # Apply them individually
    step1 = lower.normalize_str(text)
    step2 = strip.normalize_str(step1)
    
    # Apply them as a sequence
    seq = norm.Sequence([norm.Lowercase(), norm.Strip()])
    seq_result = seq.normalize_str(text)
    
    assert step2 == seq_result

# Test 3: Prepend consistency
@given(st.text(), st.text(min_size=1, max_size=10))
def test_prepend_consistency(text, prefix):
    normalizer = norm.Prepend(prefix)
    result = normalizer.normalize_str(text)
    assert result.startswith(prefix)
    assert result == prefix + text

# Test 4: Prepend idempotence - prepending twice should add prefix only once more
@given(st.text(), st.text(min_size=1, max_size=10))
def test_prepend_not_idempotent(text, prefix):
    normalizer = norm.Prepend(prefix)
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    # Prepend is NOT idempotent - it adds the prefix each time
    assert twice == prefix + once
    assert twice == prefix + prefix + text

# Test 5: Replace functionality
@given(st.text(), st.text(min_size=1, max_size=5), st.text(min_size=0, max_size=5))
def test_replace_all_occurrences(text, pattern, replacement):
    assume(pattern != replacement)  # Avoid trivial cases
    normalizer = norm.Replace(pattern, replacement)
    result = normalizer.normalize_str(text)
    # The result should not contain the pattern anymore
    assert pattern not in result or pattern == replacement

# Test 6: Unicode normalization relationships
@given(st.text())
def test_unicode_nfc_nfd_relationship(text):
    nfc = norm.NFC()
    nfd = norm.NFD()
    
    nfc_result = nfc.normalize_str(text)
    nfd_result = nfd.normalize_str(text)
    
    # Applying NFC to an NFD string should give the same as direct NFC
    nfc_of_nfd = nfc.normalize_str(nfd_result)
    assert nfc_of_nfd == nfc_result
    
    # Applying NFD to an NFC string should give the same as direct NFD
    nfd_of_nfc = nfd.normalize_str(nfc_result)
    assert nfd_of_nfc == nfd_result

# Test 7: Strip removes whitespace from both ends
@given(st.text())
def test_strip_removes_whitespace(text):
    normalizer = norm.Strip()
    result = normalizer.normalize_str(text)
    # Result should not start or end with whitespace
    if result:
        assert not result[0].isspace()
        assert not result[-1].isspace()
    # Result should be same as Python's strip
    assert result == text.strip()

# Test 8: BertNormalizer with lowercase
@given(st.text())
def test_bert_normalizer_lowercase(text):
    normalizer = norm.BertNormalizer(lowercase=True)
    result = normalizer.normalize_str(text)
    # When lowercase is True, result should be lowercase
    assert result == result.lower()

# Test 9: BertNormalizer idempotence
@given(st.text())
def test_bert_normalizer_idempotent(text):
    normalizer = norm.BertNormalizer()
    once = normalizer.normalize_str(text)
    twice = normalizer.normalize_str(once)
    assert once == twice

# Test 10: ByteLevel normalizer preserves content semantics
@given(st.text())
def test_bytelevel_preserves_ascii(text):
    # ByteLevel uses special characters for spaces
    normalizer = norm.ByteLevel()
    result = normalizer.normalize_str(text)
    # Check that ASCII letters are preserved
    for char in text:
        if char.isalpha() and ord(char) < 128:
            assert char in result or char.lower() in result or char.upper() in result

# Test 11: Empty string handling
@given(st.just(""))
def test_empty_string_handling(text):
    normalizers = [
        norm.Lowercase(),
        norm.NFC(),
        norm.NFD(),
        norm.NFKC(),
        norm.NFKD(),
        norm.Strip(),
        norm.StripAccents(),
        norm.Prepend("prefix"),
        norm.Replace("a", "b"),
        norm.BertNormalizer(),
        norm.ByteLevel(),
        norm.Nmt(),
    ]
    
    for normalizer in normalizers:
        result = normalizer.normalize_str(text)
        if isinstance(normalizer, norm.Prepend):
            assert result == "prefix"
        else:
            assert result == ""

# Test 12: Null byte handling
@given(st.text())
def test_null_byte_handling(text):
    # Add null bytes to the text
    text_with_null = text + "\x00"
    
    normalizers = [
        norm.Lowercase(),
        norm.Strip(),
        norm.NFC(),
    ]
    
    for normalizer in normalizers:
        # This should not crash
        result = normalizer.normalize_str(text_with_null)
        assert isinstance(result, str)