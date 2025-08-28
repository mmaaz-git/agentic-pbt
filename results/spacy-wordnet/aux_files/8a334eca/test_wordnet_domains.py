import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from unittest.mock import Mock, MagicMock, patch
import pytest
from collections import defaultdict

import spacy_wordnet.wordnet_domains as wd
from spacy_wordnet.__utils__ import fetch_wordnet_lang, spacy2wordnet_pos
from spacy.parts_of_speech import ADJ, ADV, NOUN, VERB, AUX
from nltk.corpus.reader.wordnet import Synset

# Test 1: Idempotence of load_wordnet_domains
@given(st.integers(min_value=1, max_value=10))
def test_load_wordnet_domains_idempotent(n_calls):
    """Loading domains multiple times should be idempotent"""
    # Clear the global state first
    wd.__WN_DOMAINS_BY_SSID.clear()
    
    # Create a mock file
    mock_data = "12345678-n\tdomain1 domain2\n87654321-v\tdomain3\n"
    
    with patch('builtins.open', return_value=mock_data.split('\n')):
        # Load multiple times
        for _ in range(n_calls):
            wd.load_wordnet_domains()
        
        # Check that the data was loaded only once
        assert len(wd.__WN_DOMAINS_BY_SSID) == 2
        assert wd.__WN_DOMAINS_BY_SSID['12345678-n'] == ['domain1', 'domain2']
        assert wd.__WN_DOMAINS_BY_SSID['87654321-v'] == ['domain3']

# Test 2: get_domains_for_synset formatting
@given(
    st.integers(min_value=0, max_value=99999999),
    st.sampled_from(['n', 'v', 'a', 'r'])
)
def test_get_domains_for_synset_formatting(offset, pos):
    """SSID formatting should be consistent: 8-digit zero-padded offset + pos"""
    # Create a mock synset
    mock_synset = Mock(spec=Synset)
    mock_synset.offset.return_value = offset
    mock_synset.pos.return_value = pos
    
    # Clear and set up test data
    wd.__WN_DOMAINS_BY_SSID.clear()
    expected_ssid = f"{str(offset).zfill(8)}-{pos}"
    test_domains = ['test_domain1', 'test_domain2']
    wd.__WN_DOMAINS_BY_SSID[expected_ssid] = test_domains
    
    # Get domains
    result = wd.get_domains_for_synset(mock_synset)
    
    # Should get the correct domains based on formatted SSID
    assert result == test_domains

# Test 3: Wordnet.__find_synsets pos parameter handling
@given(
    st.one_of(
        st.none(),
        st.sampled_from(['verb', 'noun', 'adj']),
        st.lists(st.sampled_from(['verb', 'noun', 'adj']), min_size=0, max_size=3)
    )
)
def test_wordnet_find_synsets_pos_handling(pos_input):
    """__find_synsets should handle None, str, and list for pos parameter"""
    mock_token = Mock()
    mock_token.text = "test"
    mock_token.lemma_ = "test"
    mock_token.pos = NOUN
    
    with patch('spacy_wordnet.wordnet_domains.wn.synsets', return_value=[]):
        # This should not raise an error for valid inputs
        result = wd.Wordnet._Wordnet__find_synsets(mock_token, 'eng', pos=pos_input)
        assert isinstance(result, list)

# Test 4: Invalid pos values should raise ValueError
@given(
    st.one_of(
        st.text(min_size=1).filter(lambda x: x not in ['verb', 'noun', 'adj']),
        st.lists(st.text(min_size=1), min_size=1).filter(
            lambda lst: any(x not in ['verb', 'noun', 'adj'] for x in lst)
        )
    )
)
def test_wordnet_find_synsets_invalid_pos(invalid_pos):
    """__find_synsets should raise ValueError for invalid pos values"""
    mock_token = Mock()
    mock_token.text = "test"
    mock_token.lemma_ = "test"
    mock_token.pos = NOUN
    
    with pytest.raises(ValueError, match="pos argument must be a combination"):
        wd.Wordnet._Wordnet__find_synsets(mock_token, 'eng', pos=invalid_pos)

# Test 5: __has_domains set operation properties
@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5),
    st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5)
)
def test_has_domains_set_properties(synset_domains, query_domains):
    """__has_domains should correctly check for domain overlap using set operations"""
    mock_synset = Mock(spec=Synset)
    
    with patch('spacy_wordnet.wordnet_domains.get_domains_for_synset', return_value=synset_domains):
        result = wd.Wordnet._Wordnet__has_domains(mock_synset, query_domains)
        
        # The function returns True if there's any overlap (not disjoint)
        expected = len(set(synset_domains).intersection(set(query_domains))) > 0
        assert result == expected

# Test 6: fetch_wordnet_lang mapping consistency
@given(st.sampled_from(['es', 'en', 'fr', 'it', 'pt', 'de', 'ja', 'zh']))
def test_fetch_wordnet_lang_valid(lang):
    """fetch_wordnet_lang should return consistent mappings for valid languages"""
    result1 = fetch_wordnet_lang(lang)
    result2 = fetch_wordnet_lang(lang)
    
    # Should be consistent
    assert result1 == result2
    # Should return a string
    assert isinstance(result1, str)
    # Should return a 3-letter code
    assert len(result1) == 3

# Test 7: fetch_wordnet_lang invalid language
@given(st.text(min_size=1, max_size=5).filter(
    lambda x: x not in ['es', 'en', 'fr', 'it', 'pt', 'de', 'sq', 'ar', 'bg', 
                        'ca', 'zh', 'da', 'el', 'eu', 'fa', 'fi', 'he', 'hr', 
                        'id', 'ja', 'nl', 'pl', 'sl', 'sv', 'th', 'ml']
))
def test_fetch_wordnet_lang_invalid(invalid_lang):
    """fetch_wordnet_lang should raise Exception for unsupported languages"""
    with pytest.raises(Exception, match="Language .* not supported"):
        fetch_wordnet_lang(invalid_lang)

# Test 8: spacy2wordnet_pos mapping
@given(st.sampled_from([ADJ, NOUN, ADV, VERB, AUX]))
def test_spacy2wordnet_pos_valid(spacy_pos):
    """spacy2wordnet_pos should return consistent mappings for valid POS"""
    result = spacy2wordnet_pos(spacy_pos)
    
    # Should return a string for valid POS
    assert isinstance(result, str)
    # Should be one of the WordNet POS tags
    assert result in ['n', 'v', 'a', 'r', 's']

# Test 9: spacy2wordnet_pos invalid input
@given(st.integers().filter(lambda x: x not in [ADJ, NOUN, ADV, VERB, AUX]))
def test_spacy2wordnet_pos_invalid(invalid_pos):
    """spacy2wordnet_pos should return None for invalid POS"""
    result = spacy2wordnet_pos(invalid_pos)
    assert result is None

# Test 10: load_wordnet_domains file parsing
@given(
    st.lists(
        st.tuples(
            st.text(alphabet='0123456789', min_size=8, max_size=8),
            st.sampled_from(['n', 'v', 'a', 'r']),
            st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3)
        ),
        min_size=0,
        max_size=10
    )
)
def test_load_wordnet_domains_parsing(domain_data):
    """load_wordnet_domains should correctly parse the file format"""
    # Clear global state
    wd.__WN_DOMAINS_BY_SSID.clear()
    
    # Create mock file content
    lines = []
    expected = {}
    for offset, pos, domains in domain_data:
        ssid = f"{offset}-{pos}"
        domain_str = " ".join(domains)
        lines.append(f"{ssid}\t{domain_str}")
        expected[ssid] = domains
    
    mock_content = "\n".join(lines)
    
    with patch('builtins.open', return_value=mock_content.split('\n')):
        wd.load_wordnet_domains()
        
        # Check all data was loaded correctly
        assert dict(wd.__WN_DOMAINS_BY_SSID) == expected