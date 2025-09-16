import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import spacy
from spacy.tokens import Doc, Token
from spacy.parts_of_speech import VERB, NOUN, ADJ, ADV, AUX
from spacy_wordnet.wordnet_annotator import WordnetAnnotator, Wordnet
from spacy_wordnet.wordnet_domains import load_wordnet_domains
from spacy_wordnet.__utils__ import fetch_wordnet_lang, spacy2wordnet_pos
import pytest


# Test 1: Wordnet.__find_synsets pos validation
@given(st.lists(st.text(min_size=1), min_size=1, max_size=5))
def test_find_synsets_pos_validation(invalid_pos_values):
    """Test that __find_synsets raises ValueError for invalid pos values"""
    # Skip if any value is actually valid
    assume(not any(v in ["verb", "noun", "adj"] for v in invalid_pos_values))
    
    # Create a mock token
    nlp = spacy.blank("en")
    doc = nlp("test")
    token = doc[0]
    
    # Should raise ValueError for invalid pos values
    with pytest.raises(ValueError, match="pos argument must be a combination"):
        Wordnet._Wordnet__find_synsets(token, "eng", pos=invalid_pos_values)


# Test 2: Wordnet.__find_synsets pos type handling
@given(st.one_of(
    st.text(min_size=1),
    st.lists(st.text(min_size=1), min_size=1, max_size=3)
))
def test_find_synsets_pos_type_conversion(pos_value):
    """Test that __find_synsets handles string and list pos arguments correctly"""
    nlp = spacy.blank("en")
    doc = nlp("test")
    token = doc[0]
    
    # Filter to only valid values
    if isinstance(pos_value, str):
        if pos_value not in ["verb", "noun", "adj"]:
            pos_value = "noun"  # Use valid default
    else:
        pos_value = [v if v in ["verb", "noun", "adj"] else "noun" for v in pos_value]
    
    # Should not raise an error for valid string or list
    result = Wordnet._Wordnet__find_synsets(token, "eng", pos=pos_value)
    assert isinstance(result, list)


# Test 3: Wordnet.synsets() always returns a list
@given(st.sampled_from([None, "verb", "noun", "adj", ["verb", "noun"], ["adj"]]))
def test_wordnet_synsets_returns_list(pos):
    """Test that Wordnet.synsets() always returns a list"""
    nlp = spacy.blank("en")
    doc = nlp("running")
    token = doc[0]
    token.pos_ = "VERB"
    token.pos = VERB
    token.lemma_ = "run"
    
    wordnet = Wordnet(token, lang="en")
    result = wordnet.synsets(pos=pos)
    assert isinstance(result, list)


# Test 4: WordnetAnnotator returns same Doc object
@given(st.lists(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), 
                        min_size=1, max_size=10), min_size=1, max_size=5))
def test_wordnet_annotator_returns_same_doc(words):
    """Test that WordnetAnnotator returns the same Doc object"""
    nlp = spacy.blank("en")
    text = " ".join(words)
    doc = nlp(text)
    
    annotator = WordnetAnnotator(nlp, "wordnet")
    result = annotator(doc)
    
    # Should return the exact same Doc object
    assert result is doc
    
    # All tokens should have wordnet extension
    for token in result:
        assert hasattr(token._, "wordnet")
        assert isinstance(token._.wordnet, Wordnet)


# Test 5: fetch_wordnet_lang error handling
@given(st.text(min_size=1, max_size=5))
def test_fetch_wordnet_lang_unsupported(lang_code):
    """Test that fetch_wordnet_lang raises exception for unsupported languages"""
    # Known supported languages
    supported = ["es", "en", "fr", "it", "pt", "de", "sq", "ar", "bg", "ca", 
                 "zh", "da", "el", "eu", "fa", "fi", "he", "hr", "id", "ja", 
                 "nl", "pl", "sl", "sv", "th", "ml"]
    
    if lang_code not in supported:
        with pytest.raises(Exception, match="Language .* not supported"):
            fetch_wordnet_lang(lang_code)
    else:
        # Should not raise for supported languages
        result = fetch_wordnet_lang(lang_code)
        assert isinstance(result, str)


# Test 6: spacy2wordnet_pos mapping
@given(st.integers())
def test_spacy2wordnet_pos_mapping(spacy_pos):
    """Test that spacy2wordnet_pos returns correct mappings or None"""
    result = spacy2wordnet_pos(spacy_pos)
    
    # Known mappings from the code
    if spacy_pos == ADJ:
        assert result == "a"
    elif spacy_pos == NOUN:
        assert result == "n"
    elif spacy_pos == ADV:
        assert result == "r"
    elif spacy_pos in [VERB, AUX]:
        assert result == "v"
    else:
        assert result is None


# Test 7: Wordnet.wordnet_synsets_for_domain returns subset
@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3))
def test_wordnet_synsets_for_domain_subset(domains):
    """Test that wordnet_synsets_for_domain returns a subset of all synsets"""
    nlp = spacy.blank("en")
    doc = nlp("computer")
    token = doc[0]
    token.pos_ = "NOUN"
    token.pos = NOUN
    token.lemma_ = "computer"
    
    load_wordnet_domains()
    wordnet = Wordnet(token, lang="en")
    
    all_synsets = wordnet.synsets()
    domain_synsets = wordnet.wordnet_synsets_for_domain(domains)
    
    # domain_synsets should be a subset of all_synsets
    assert isinstance(domain_synsets, list)
    assert set(domain_synsets).issubset(set(all_synsets))


# Test 8: Round-trip property for pos filtering
@given(st.sampled_from(["verb", "noun", "adj"]))
def test_synsets_pos_filtering_property(pos):
    """Test that filtered synsets actually have the requested POS"""
    nlp = spacy.blank("en")
    # Use words that are likely to have synsets in multiple POS categories
    doc = nlp("run")
    token = doc[0]
    token.lemma_ = "run"
    
    wordnet = Wordnet(token, lang="en")
    filtered_synsets = wordnet.synsets(pos=pos)
    
    # Map pos string to wordnet pos
    pos_map = {"verb": "v", "noun": "n", "adj": "a"}
    expected_pos = pos_map[pos]
    
    # All returned synsets should have the requested POS
    for synset in filtered_synsets:
        assert synset.pos() == expected_pos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])