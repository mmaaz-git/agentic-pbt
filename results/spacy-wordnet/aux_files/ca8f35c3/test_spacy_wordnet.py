#!/usr/bin/env python3
import sys
import os
import tempfile
from unittest.mock import Mock, MagicMock
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the spacy_wordnet module to path
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')

import spacy_wordnet
from spacy_wordnet.wordnet_domains import Wordnet, load_wordnet_domains, get_domains_for_synset
from spacy_wordnet.__utils__ import fetch_wordnet_lang, spacy2wordnet_pos
from spacy.parts_of_speech import ADJ, ADV, NOUN, VERB, AUX
from nltk.corpus.reader.wordnet import Synset

# Property 1: Test synsets() POS filtering behavior
@given(
    st.one_of(
        st.none(),
        st.text(),
        st.lists(st.text()),
        st.integers(),
        st.floats(),
        st.dictionaries(st.text(), st.text())
    )
)
def test_synsets_pos_parameter_validation(pos):
    """Test that synsets() validates POS parameter correctly according to docstring"""
    token = Mock()
    token.text = "test"
    token.lemma_ = "test"
    token.pos = NOUN
    
    wordnet_obj = Wordnet(token=token, lang="en")
    
    valid_pos = ["verb", "noun", "adj"]
    
    # According to lines 88-102, pos can be None, str, or list
    if pos is None:
        # Should work fine
        result = wordnet_obj.synsets(pos=pos)
        assert isinstance(result, list)
    elif isinstance(pos, str):
        if pos in valid_pos:
            result = wordnet_obj.synsets(pos=pos)
            assert isinstance(result, list)
        else:
            # Should raise ValueError for invalid strings
            with pytest.raises(ValueError, match="pos argument must be a combination"):
                wordnet_obj.synsets(pos=pos)
    elif isinstance(pos, list):
        if all(p in valid_pos for p in pos):
            result = wordnet_obj.synsets(pos=pos)
            assert isinstance(result, list)
        else:
            with pytest.raises(ValueError, match="pos argument must be a combination"):
                wordnet_obj.synsets(pos=pos)
    else:
        # Try to convert to list - if it fails, should raise TypeError
        try:
            list_pos = list(pos)
            if all(p in valid_pos for p in list_pos):
                result = wordnet_obj.synsets(pos=pos)
                assert isinstance(result, list)
            else:
                with pytest.raises(ValueError, match="pos argument must be a combination"):
                    wordnet_obj.synsets(pos=pos)
        except TypeError:
            with pytest.raises(TypeError, match="pos argument must be None, type str, or type list"):
                wordnet_obj.synsets(pos=pos)


# Property 2: Test language mapping behavior
@given(st.text())
def test_fetch_wordnet_lang_behavior(lang):
    """Test that fetch_wordnet_lang either returns a valid language or raises Exception"""
    # Based on lines 72-78 in __utils__.py
    valid_langs = {
        'es', 'en', 'fr', 'it', 'pt', 'de', 'sq', 'ar', 'bg', 'ca', 'zh', 
        'da', 'el', 'eu', 'fa', 'fi', 'he', 'hr', 'id', 'ja', 'nl', 'pl', 
        'sl', 'sv', 'th', 'ml'
    }
    
    if lang in valid_langs:
        result = fetch_wordnet_lang(lang)
        assert isinstance(result, str)
        assert len(result) == 3  # WordNet uses 3-letter codes
    else:
        with pytest.raises(Exception, match="Language .* not supported"):
            fetch_wordnet_lang(lang)


# Property 3: Test spacy2wordnet_pos mapping
@given(st.integers())
def test_spacy2wordnet_pos_mapping(spacy_pos):
    """Test that spacy2wordnet_pos returns either a valid mapping or None"""
    # Based on lines 59-69 in __utils__.py
    valid_mappings = {ADJ, NOUN, ADV, VERB, AUX}
    
    result = spacy2wordnet_pos(spacy_pos)
    
    if spacy_pos in valid_mappings:
        assert result is not None
        assert result in ['a', 'n', 'r', 'v']  # Valid WordNet POS tags
    else:
        assert result is None


# Property 4: Test wordnet domains file parsing
@given(
    st.lists(
        st.tuples(
            st.from_regex(r'[0-9]{8}-[nvra]', fullmatch=True),  # ssid format
            st.lists(st.from_regex(r'[a-z_]+', fullmatch=True), min_size=1)  # domain names
        ),
        min_size=0,
        max_size=100
    )
)
def test_load_wordnet_domains_parsing(domain_data):
    """Test that load_wordnet_domains correctly parses the expected file format"""
    # Based on lines 17-23 in wordnet_domains.py
    
    # Create a temporary file with test data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        for ssid, domains in domain_data:
            f.write(f"{ssid}\t{' '.join(domains)}\n")
        temp_path = f.name
    
    try:
        # Clear the global domains dictionary first
        import spacy_wordnet.wordnet_domains as wd
        wd.__WN_DOMAINS_BY_SSID.clear()
        
        # Load the domains
        load_wordnet_domains(temp_path)
        
        # Verify all domains were loaded correctly
        for ssid, expected_domains in domain_data:
            loaded_domains = wd.__WN_DOMAINS_BY_SSID.get(ssid, [])
            assert loaded_domains == expected_domains
    finally:
        os.unlink(temp_path)


# Property 5: Test list coercion in synsets method
@given(
    st.one_of(
        st.sets(st.sampled_from(["verb", "noun", "adj"])),
        st.tuples(st.sampled_from(["verb", "noun", "adj"])),
        st.frozensets(st.sampled_from(["verb", "noun", "adj"]))
    )
)
def test_synsets_iterable_to_list_conversion(pos):
    """Test that synsets() correctly converts iterables to lists"""
    # Based on lines 92-96, the code tries to convert to list
    token = Mock()
    token.text = "test"
    token.lemma_ = "test"
    token.pos = NOUN
    
    wordnet_obj = Wordnet(token=token, lang="en")
    
    # Should convert to list and work
    result = wordnet_obj.synsets(pos=pos)
    assert isinstance(result, list)


# Property 6: Test domains set operations invariant
@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=20),
    st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=20)
)
def test_has_domains_set_operation(synset_domains, query_domains):
    """Test the __has_domains method's set disjoint logic"""
    # Based on line 126 in wordnet_domains.py
    
    # Mock a synset
    synset = Mock(spec=Synset)
    synset.offset.return_value = 12345678
    synset.pos.return_value = 'n'
    
    # Mock get_domains_for_synset to return our test domains
    import spacy_wordnet.wordnet_domains as wd
    original_get_domains = wd.get_domains_for_synset
    wd.get_domains_for_synset = lambda s: synset_domains
    
    try:
        # Test the private method logic
        result = Wordnet._Wordnet__has_domains(synset, query_domains)
        
        # Verify the set logic: returns True if sets have common elements
        expected = not set(query_domains).isdisjoint(synset_domains)
        assert result == expected
    finally:
        wd.get_domains_for_synset = original_get_domains


# Property 7: Test empty list invariant for invalid tokens
@given(st.text())
def test_synsets_empty_list_for_invalid_input(text):
    """Test that synsets returns empty list for tokens with no matches"""
    token = Mock()
    token.text = text
    token.lemma_ = text
    token.pos = 999  # Invalid POS
    
    wordnet_obj = Wordnet(token=token, lang="en")
    
    # Should return empty list, not crash
    result = wordnet_obj.synsets()
    assert isinstance(result, list)
    # Most random strings won't have synsets
    if not text or not text.isalpha():
        assert result == []


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])